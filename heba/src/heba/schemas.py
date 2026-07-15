"""Pydantic request/response models for the REST contract."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from heba.config import PROFILE


class ContextInfo(BaseModel):
    context_id: str
    scheme: str
    engine: str
    poly_modulus_degree: int
    coeff_mod_bit_sizes: list[int]
    global_scale: float
    allowed_dims: list[int]
    allowed_ops: list[str]
    bound: bool
    security_note: str


class BindContextRequest(BaseModel):
    context_id: str
    public_context_b64: str = Field(..., min_length=16)

    @field_validator("context_id")
    @classmethod
    def check_context_id(cls, value: str) -> str:
        if value != PROFILE.context_id:
            raise ValueError(f"unsupported context_id: {value}")
        return value


class BindContextResponse(BaseModel):
    context_id: str
    bound: bool
    message: str


class AddRequest(BaseModel):
    context_id: str
    dimension: int
    left_ciphertext_b64: str
    right_ciphertext_b64: str
    # Forbidden field name — presence must be rejected by standards layer.
    secret_key: str | None = None


class MulPlainRequest(BaseModel):
    context_id: str
    dimension: int
    ciphertext_b64: str
    weights: list[float]
    secret_key: str | None = None


class LinearScoreRequest(BaseModel):
    context_id: str
    dimension: int
    features_ciphertext_b64: str
    weights: list[float]
    bias: float = 0.0
    secret_key: str | None = None


class EvalResponse(BaseModel):
    context_id: str
    operation: str
    dimension: int
    result_ciphertext_b64: str
    eval_ms: float


class ErrorBody(BaseModel):
    detail: str
    reject_reason: str | None = None


class MetricsResponse(BaseModel):
    metrics: dict[str, Any]
