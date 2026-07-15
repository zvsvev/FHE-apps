"""REST endpoints for context binding, evaluation, and metrics."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from heba.config import PROFILE
from heba.engine import EngineError, b64encode
from heba.metrics import EvalMetrics, Timer
from heba.schemas import (
    AddRequest,
    BindContextRequest,
    BindContextResponse,
    ContextInfo,
    EvalResponse,
    LinearScoreRequest,
    MetricsResponse,
    MulPlainRequest,
)
from heba.standards import StandardsViolation, validate_eval_request

router = APIRouter()


def _http_400(reason: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"detail": message, "reject_reason": reason},
    )


@router.get("/v1/context", response_model=ContextInfo)
def get_context(request: Request) -> ContextInfo:
    engine = request.app.state.engine
    return ContextInfo(
        context_id=PROFILE.context_id,
        scheme=PROFILE.scheme,
        engine=PROFILE.engine_name,
        poly_modulus_degree=PROFILE.poly_modulus_degree,
        coeff_mod_bit_sizes=list(PROFILE.coeff_mod_bit_sizes),
        global_scale=PROFILE.global_scale,
        allowed_dims=list(PROFILE.allowed_dims),
        allowed_ops=list(PROFILE.allowed_ops),
        bound=engine.is_bound,
        security_note=PROFILE.security_note,
    )


@router.post("/v1/context/bind", response_model=BindContextResponse)
def bind_context(body: BindContextRequest, request: Request) -> BindContextResponse:
    engine = request.app.state.engine
    try:
        engine.bind_public_context(body.context_id, body.public_context_b64)
    except EngineError as exc:
        raise _http_400("bind_failed", str(exc)) from exc
    return BindContextResponse(
        context_id=body.context_id,
        bound=True,
        message="public context bound; evaluation endpoints are ready",
    )


@router.post("/v1/eval/add", response_model=EvalResponse)
def eval_add(body: AddRequest, request: Request) -> EvalResponse:
    metrics_store = request.app.state.metrics
    engine = request.app.state.engine
    timer = Timer()
    try:
        validate_eval_request(
            operation="add",
            context_id=body.context_id,
            dimension=body.dimension,
            payload=body,
        )
        result = engine.add(
            body.context_id,
            body.left_ciphertext_b64,
            body.right_ciphertext_b64,
            body.dimension,
        )
    except StandardsViolation as exc:
        metrics_store.set_last(
            EvalMetrics(
                operation="add",
                context_id=body.context_id,
                dimension=body.dimension,
                accepted=False,
                reject_reason=exc.reason,
                eval_ms=timer.ms(),
            )
        )
        raise _http_400(exc.reason, str(exc)) from exc
    except EngineError as exc:
        metrics_store.set_last(
            EvalMetrics(
                operation="add",
                context_id=body.context_id,
                dimension=body.dimension,
                accepted=False,
                reject_reason="engine_error",
                eval_ms=timer.ms(),
            )
        )
        raise _http_400("engine_error", str(exc)) from exc

    eval_ms = timer.ms()
    result_b64 = b64encode(result)
    metrics_store.set_last(
        EvalMetrics(
            operation="add",
            context_id=body.context_id,
            dimension=body.dimension,
            accepted=True,
            eval_ms=eval_ms,
            request_ciphertext_bytes=len(body.left_ciphertext_b64) + len(body.right_ciphertext_b64),
            response_ciphertext_bytes=len(result_b64),
        )
    )
    return EvalResponse(
        context_id=body.context_id,
        operation="add",
        dimension=body.dimension,
        result_ciphertext_b64=result_b64,
        eval_ms=eval_ms,
    )


@router.post("/v1/eval/mul_plain", response_model=EvalResponse)
def eval_mul_plain(body: MulPlainRequest, request: Request) -> EvalResponse:
    metrics_store = request.app.state.metrics
    engine = request.app.state.engine
    timer = Timer()
    try:
        validate_eval_request(
            operation="mul_plain",
            context_id=body.context_id,
            dimension=body.dimension,
            payload=body,
            weights=body.weights,
        )
        result = engine.mul_plain(
            body.context_id,
            body.ciphertext_b64,
            body.weights,
            body.dimension,
        )
    except StandardsViolation as exc:
        metrics_store.set_last(
            EvalMetrics(
                operation="mul_plain",
                context_id=body.context_id,
                dimension=body.dimension,
                accepted=False,
                reject_reason=exc.reason,
                eval_ms=timer.ms(),
            )
        )
        raise _http_400(exc.reason, str(exc)) from exc
    except EngineError as exc:
        metrics_store.set_last(
            EvalMetrics(
                operation="mul_plain",
                context_id=body.context_id,
                dimension=body.dimension,
                accepted=False,
                reject_reason="engine_error",
                eval_ms=timer.ms(),
            )
        )
        raise _http_400("engine_error", str(exc)) from exc

    eval_ms = timer.ms()
    result_b64 = b64encode(result)
    metrics_store.set_last(
        EvalMetrics(
            operation="mul_plain",
            context_id=body.context_id,
            dimension=body.dimension,
            accepted=True,
            eval_ms=eval_ms,
            request_ciphertext_bytes=len(body.ciphertext_b64),
            response_ciphertext_bytes=len(result_b64),
        )
    )
    return EvalResponse(
        context_id=body.context_id,
        operation="mul_plain",
        dimension=body.dimension,
        result_ciphertext_b64=result_b64,
        eval_ms=eval_ms,
    )


@router.post("/v1/eval/linear_score", response_model=EvalResponse)
def eval_linear_score(body: LinearScoreRequest, request: Request) -> EvalResponse:
    metrics_store = request.app.state.metrics
    engine = request.app.state.engine
    timer = Timer()
    try:
        validate_eval_request(
            operation="linear_score",
            context_id=body.context_id,
            dimension=body.dimension,
            payload=body,
            weights=body.weights,
        )
        result = engine.linear_score(
            body.context_id,
            body.features_ciphertext_b64,
            body.weights,
            body.bias,
            body.dimension,
        )
    except StandardsViolation as exc:
        metrics_store.set_last(
            EvalMetrics(
                operation="linear_score",
                context_id=body.context_id,
                dimension=body.dimension,
                accepted=False,
                reject_reason=exc.reason,
                eval_ms=timer.ms(),
            )
        )
        raise _http_400(exc.reason, str(exc)) from exc
    except EngineError as exc:
        metrics_store.set_last(
            EvalMetrics(
                operation="linear_score",
                context_id=body.context_id,
                dimension=body.dimension,
                accepted=False,
                reject_reason="engine_error",
                eval_ms=timer.ms(),
            )
        )
        raise _http_400("engine_error", str(exc)) from exc

    eval_ms = timer.ms()
    result_b64 = b64encode(result)
    metrics_store.set_last(
        EvalMetrics(
            operation="linear_score",
            context_id=body.context_id,
            dimension=body.dimension,
            accepted=True,
            eval_ms=eval_ms,
            request_ciphertext_bytes=len(body.features_ciphertext_b64),
            response_ciphertext_bytes=len(result_b64),
            extra={"bias": body.bias},
        )
    )
    return EvalResponse(
        context_id=body.context_id,
        operation="linear_score",
        dimension=body.dimension,
        result_ciphertext_b64=result_b64,
        eval_ms=eval_ms,
    )


@router.get("/v1/metrics/last", response_model=MetricsResponse)
def metrics_last(request: Request) -> MetricsResponse:
    return MetricsResponse(metrics=request.app.state.metrics.get_last())
