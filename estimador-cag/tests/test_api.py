from app.context.examples import ESTIMATION_EXAMPLES
from app.services import llm_service

TRANSCRIPTION = (
    "El cliente necesita una landing page con formulario de contacto, integración con "
    "HubSpot y un blog con editor WYSIWYG. El diseño ya existe en Figma."
)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model"] == "gpt-4o-mini"
    assert body["api_key_configured"] is True


def test_docs_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").json()["info"]["title"] == "Estimador CAG"


def test_openapi_documents_error_responses(client):
    responses = client.get("/openapi.json").json()["paths"]["/api/v1/estimate"]["post"]["responses"]
    assert {"200", "422", "502", "503"} <= set(responses)


def test_system_prompt_injects_all_examples():
    prompt = llm_service.build_system_prompt()
    for example in ESTIMATION_EXAMPLES:
        assert example["meeting_summary"] in prompt
        assert example["estimation"].strip() in prompt


def test_estimate_sends_cag_messages_and_returns_json(client, monkeypatch):
    captured = {}

    def fake_openai(settings, api_key, transcription):
        captured["transcription"] = transcription
        captured["model"] = settings.model
        return "## Estimación: Landing page\n**Total estimado: 80 horas**", 1200, 300, "gpt-4o-mini"

    monkeypatch.setattr(llm_service, "_call_openai", fake_openai)

    response = client.post("/api/v1/estimate", json={"transcription": TRANSCRIPTION})

    assert response.status_code == 200
    body = response.json()
    assert body["estimation"].startswith("## Estimación")
    assert body["provider"] == "openai"
    assert body["model"] == "gpt-4o-mini"
    assert body["usage"] == {"input_tokens": 1200, "output_tokens": 300}
    assert captured == {"transcription": TRANSCRIPTION, "model": "gpt-4o-mini"}


def test_anthropic_provider_uses_haiku_by_default(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-dummy")
    llm_service.get_settings.cache_clear()
    monkeypatch.setattr(
        llm_service,
        "_call_anthropic",
        lambda settings, key, text: ("## Estimación", 10, 5, settings.model),
    )

    body = client.post("/api/v1/estimate", json={"transcription": TRANSCRIPTION}).json()

    assert body["provider"] == "anthropic"
    assert body["model"] == "claude-haiku-4-5"


def test_missing_api_key_returns_503(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    llm_service.get_settings.cache_clear()

    assert client.get("/health").json()["api_key_configured"] is False
    response = client.post("/api/v1/estimate", json={"transcription": TRANSCRIPTION})

    assert response.status_code == 503
    assert "API key" in response.json()["detail"]


def test_provider_error_returns_502(client, monkeypatch):
    def boom(*args):
        raise RuntimeError("rate limit")

    monkeypatch.setattr(llm_service, "_call_openai", boom)

    response = client.post("/api/v1/estimate", json={"transcription": TRANSCRIPTION})

    assert response.status_code == 502


def test_rejects_empty_transcription(client):
    assert client.post("/api/v1/estimate", json={"transcription": ""}).status_code == 422
    assert client.post("/api/v1/estimate", json={}).status_code == 422
