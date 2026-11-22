# Estimador CAG

Servicio FastAPI que recibe la transcripción de una reunión con un cliente y devuelve una estimación de proyecto de software generada por un LLM.

Ejercicio de la **Sesión 2 — Scaffolding del proyecto FastAPI** del Máster en AI Engineering (LIDR).

## Arquitectura: CAG (Cache Augmented Generation)

Todo el contexto que necesita el modelo viaja en cada llamada: no hay base de datos, ni retrieval, ni persistencia.

```
POST /api/v1/estimate { transcription }
        │
        ▼
routers/estimations.py ── valida el request (Pydantic)
        │
        ▼
services/llm_service.py ── construye los mensajes:
        │     [system] instrucciones + ejemplos de context/examples.py
        │     [user]   transcripción de la reunión
        ▼
OpenAI (gpt-4o-mini) o Anthropic (claude-haiku-4-5), según LLM_PROVIDER
        │
        ▼
{ estimation, model, provider, usage, latency_ms }
```

| Carpeta | Responsabilidad |
|---|---|
| `app/routers/` | Endpoints HTTP |
| `app/services/` | Lógica de negocio: prompt y llamada al LLM |
| `app/context/` | Contexto estático: estimaciones previas (few-shot) |
| `app/schemas/` | Modelos Pydantic de request/response |
| `app/config.py` | Configuración desde `.env` con `BaseSettings` |
| `transcripts/` | Transcripciones de ejemplo para probar el servicio |
| `tests/` | Tests de estructura y de la API (LLM simulado, sin coste) |

## Puesta en marcha

Requisitos: Python 3.12+ y [uv](https://docs.astral.sh/uv/).

```bash
cd estimador-cag
uv sync
cp .env.example .env   # y añade tu OPENAI_API_KEY o ANTHROPIC_API_KEY
uv run uvicorn app.main:app --reload
```

Variables de entorno (`.env`):

| Variable | Por defecto | Descripción |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` o `anthropic` |
| `LLM_MODEL` | vacío | Vacío = `gpt-4o-mini` / `claude-haiku-4-5` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | — | Clave del proveedor elegido |
| `LLM_TEMPERATURE` | `0.2` | Temperatura de generación |
| `LLM_MAX_TOKENS` | `2000` | Máximo de tokens de salida |

## Uso

- Swagger UI: <http://localhost:8000/docs>
- Health: `curl localhost:8000/health`

Estimar la transcripción de ejemplo ([`transcripts/landing-hubspot.txt`](transcripts/landing-hubspot.txt)):

```bash
scripts/estimate.sh transcripts/landing-hubspot.txt
```

O con curl directamente:

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"transcription": "En la reunión con el equipo de marketing, el cliente explicó que necesita una landing page con formulario de contacto, integración con su CRM actual (HubSpot), y una sección de blog con editor WYSIWYG. El plazo ideal sería tenerlo listo en 4 semanas. El diseño ya existe en Figma."}'
```

Respuesta:

```json
{
  "estimation": "## Estimación: Landing page con integración HubSpot ...",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "usage": { "input_tokens": 1250, "output_tokens": 420 },
  "latency_ms": 5300
}
```

Errores: `422` si la transcripción está vacía o es demasiado corta, `503` si falta la API key del proveedor, `502` si el proveedor falla.

## Validación automática

```bash
uv run pytest        # estructura de carpetas, .env ignorado, endpoints, prompt CAG
uv run ruff check .
```

El workflow [`.github/workflows/estimador-cag.yml`](../.github/workflows/estimador-cag.yml) se ejecuta en cada push que toque `estimador-cag/` y hace lo siguiente:

1. Lint con ruff.
2. Tests: estructura de carpetas y API con el LLM simulado.
3. Smoke test: arranca el servidor y comprueba `/health`, `/docs` y que `/estimate` responde `503` sin API key.
4. Estimación real con la transcripción de ejemplo, solo si el repo tiene el secret `OPENAI_API_KEY`.

## Checklist del ejercicio

- [x] Arranca con `uv run uvicorn app.main:app --reload`
- [x] API keys cargadas desde `.env`, nunca en el código (`SecretStr`)
- [x] `GET /health` responde 200
- [x] `POST /api/v1/estimate` recibe una transcripción y devuelve una estimación
- [x] El prompt inyecta los ejemplos de contexto (test `test_system_prompt_injects_all_examples`)
- [x] Swagger en `/docs`
- [x] `.env` en `.gitignore`
