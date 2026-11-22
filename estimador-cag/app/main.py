from fastapi import FastAPI

from app.config import get_settings
from app.routers import estimations

app = FastAPI(
    title="Estimador CAG",
    description=(
        "Genera estimaciones de proyectos de software a partir de transcripciones de "
        "reuniones. Arquitectura CAG: los ejemplos de estimaciones previas se inyectan "
        "directamente en el prompt del LLM."
    ),
    version="0.1.0",
)

app.include_router(estimations.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "model": settings.model,
        "api_key_configured": settings.api_key() is not None,
    }
