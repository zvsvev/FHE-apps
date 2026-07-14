"""Application–backend interaction standards (enforced on every eval request)."""

from __future__ import annotations

from typing import Any, Sequence

from fhe_eval.config import PROFILE


class StandardsViolation(ValueError):
    def __init__(self, reason: str, message: str) -> None:
        self.reason = reason
        super().__init__(message)


def reject_secret_key(payload: Any) -> None:
    """Secret keys must never be sent to the evaluation backend."""
    if getattr(payload, "secret_key", None) is not None:
        raise StandardsViolation(
            "secret_key_forbidden",
            "secret_key must not be sent to the evaluation backend",
        )
    if isinstance(payload, dict) and payload.get("secret_key") is not None:
        raise StandardsViolation(
            "secret_key_forbidden",
            "secret_key must not be sent to the evaluation backend",
        )


def validate_context_id(context_id: str) -> None:
    if context_id != PROFILE.context_id:
        raise StandardsViolation(
            "context_id_mismatch",
            f"context_id must be {PROFILE.context_id}",
        )


def validate_dimension(dimension: int) -> None:
    if dimension not in PROFILE.allowed_dims:
        raise StandardsViolation(
            "dimension_not_allowed",
            f"dimension must be one of {list(PROFILE.allowed_dims)}",
        )


def validate_operation(operation: str) -> None:
    if operation not in PROFILE.allowed_ops:
        raise StandardsViolation(
            "operation_not_allowed",
            f"operation must be one of {list(PROFILE.allowed_ops)}",
        )


def validate_weights(weights: Sequence[float], dimension: int) -> None:
    if len(weights) != dimension:
        raise StandardsViolation(
            "weights_dimension_mismatch",
            f"weights length {len(weights)} does not match dimension {dimension}",
        )


def validate_eval_request(
    *,
    operation: str,
    context_id: str,
    dimension: int,
    payload: Any,
    weights: Sequence[float] | None = None,
) -> None:
    reject_secret_key(payload)
    validate_operation(operation)
    validate_context_id(context_id)
    validate_dimension(dimension)
    if weights is not None:
        validate_weights(weights, dimension)
