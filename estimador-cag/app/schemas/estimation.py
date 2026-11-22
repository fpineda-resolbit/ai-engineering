from pydantic import BaseModel, Field


class EstimationRequest(BaseModel):
    transcription: str = Field(
        ...,
        min_length=20,
        description="Texto de la transcripción de la reunión con el cliente.",
        examples=[
            "En la reunión con el equipo de marketing, el cliente explicó que necesita una "
            "landing page con formulario de contacto e integración con HubSpot."
        ],
    )


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Descripción del error.")


class EstimationResponse(BaseModel):
    estimation: str = Field(..., description="Estimación generada por el LLM (Markdown).")
    model: str
    provider: str
    usage: TokenUsage | None = None
    latency_ms: int | None = None
