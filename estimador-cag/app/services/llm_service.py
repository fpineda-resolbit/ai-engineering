"""Lógica de negocio: construir el prompt CAG y llamar al LLM configurado.

Estructura de mensajes:
    [system]    instrucciones + ejemplos de estimaciones previas (contexto estático)
    [user]      transcripción de la reunión a estimar
    [assistant] estimación generada por el modelo
"""

import time
from dataclasses import dataclass
from functools import lru_cache

from app.config import Settings, get_settings
from app.context.examples import format_examples

SYSTEM_INSTRUCTIONS = """\
Eres un consultor senior de software experto en estimación de proyectos.
Recibirás la transcripción de una reunión con un cliente y debes generar una estimación.

Reglas:
- Usa como referencia las estimaciones previas de abajo: imita su formato, nivel de \
detalle y tarifas (60 €/h de media).
- Responde en español y en Markdown, con esta estructura: título "## Estimación: <proyecto>", \
tabla de desglose de tareas con horas, total de horas y coste, equipo recomendado, \
duración estimada, y una sección de supuestos y riesgos.
- Si la transcripción no aporta un dato necesario, decláralo como supuesto en lugar de \
inventarlo.
- No estimes funcionalidades que el cliente no haya pedido.

## Estimaciones previas de referencia
"""


class LLMServiceError(Exception):
    """Error al llamar al proveedor del LLM."""


class LLMConfigError(LLMServiceError):
    """Configuración incompleta (p. ej. falta la API key)."""


@dataclass
class EstimationResult:
    estimation: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


@lru_cache
def build_system_prompt() -> str:
    """System prompt = instrucciones + ejemplos. Es estático, así que se cachea."""
    return SYSTEM_INSTRUCTIONS + "\n" + format_examples()


def generate_estimation(transcription: str, settings: Settings | None = None) -> EstimationResult:
    settings = settings or get_settings()
    api_key = settings.api_key()
    if not api_key:
        raise LLMConfigError(
            f"Falta la API key para el proveedor '{settings.LLM_PROVIDER}'. Revisa el .env."
        )

    call = _call_openai if settings.LLM_PROVIDER == "openai" else _call_anthropic
    start = time.perf_counter()
    try:
        text, input_tokens, output_tokens, model = call(settings, api_key, transcription)
    except Exception as exc:  # errores de red, auth, rate limit del SDK
        raise LLMServiceError(f"Error llamando a {settings.LLM_PROVIDER}: {exc}") from exc

    return EstimationResult(
        estimation=text,
        model=model,
        provider=settings.LLM_PROVIDER,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )


def _call_openai(settings: Settings, api_key: str, transcription: str):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=settings.model,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": transcription},
        ],
    )
    usage = response.usage
    return (
        response.choices[0].message.content or "",
        usage.prompt_tokens if usage else 0,
        usage.completion_tokens if usage else 0,
        response.model,
    )


def _call_anthropic(settings: Settings, api_key: str, transcription: str):
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    # La API de Anthropic ya no acepta temperature/top_p/top_k; los modelos actuales
    # razonan (adaptive thinking) y esos tokens cuentan dentro de max_tokens.
    response = client.messages.create(
        model=settings.model,
        max_tokens=settings.LLM_MAX_TOKENS,
        system=build_system_prompt(),
        messages=[{"role": "user", "content": transcription}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("el modelo rechazó la petición")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("respuesta truncada: sube LLM_MAX_TOKENS")
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, response.usage.input_tokens, response.usage.output_tokens, response.model
