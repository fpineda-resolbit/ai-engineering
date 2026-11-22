from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.schemas.estimation import (
    ErrorResponse,
    EstimationRequest,
    EstimationResponse,
    TokenUsage,
)
from app.services.llm_service import LLMConfigError, LLMServiceError, generate_estimation

router = APIRouter(tags=["estimations"])


@router.post(
    "/estimate",
    response_model=EstimationResponse,
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": "El proveedor del LLM falló (red, autenticación, rate limit, "
            "respuesta truncada o rechazada).",
            "content": {
                "application/json": {
                    "example": {"detail": "Error llamando a anthropic: rate limit"}
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Servicio sin configurar: falta la API key del proveedor.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Falta la API key para el proveedor 'anthropic'. Revisa el .env."
                    }
                }
            },
        },
    },
)
async def estimate(request: EstimationRequest) -> EstimationResponse:
    """Recibe una transcripción de reunión y devuelve una estimación generada por el LLM."""
    try:
        # Los SDK son síncronos: se ejecutan en un hilo para no bloquear el event loop.
        result = await run_in_threadpool(generate_estimation, request.transcription)
    except LLMConfigError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return EstimationResponse(
        estimation=result.estimation,
        model=result.model,
        provider=result.provider,
        usage=TokenUsage(input_tokens=result.input_tokens, output_tokens=result.output_tokens),
        latency_ms=result.latency_ms,
    )
