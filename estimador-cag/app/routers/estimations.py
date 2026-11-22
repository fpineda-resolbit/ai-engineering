from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.schemas.estimation import EstimationRequest, EstimationResponse, TokenUsage
from app.services.llm_service import LLMConfigError, LLMServiceError, generate_estimation

router = APIRouter(tags=["estimations"])


@router.post("/estimate", response_model=EstimationResponse)
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
