"""In-memory metrics for the last evaluation request."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from threading import Lock
from time import perf_counter
from typing import Any


@dataclass
class EvalMetrics:
    operation: str = ""
    context_id: str = ""
    dimension: int = 0
    accepted: bool = False
    reject_reason: str = ""
    eval_ms: float = 0.0
    request_ciphertext_bytes: int = 0
    response_ciphertext_bytes: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._last: EvalMetrics = EvalMetrics()

    def set_last(self, metrics: EvalMetrics) -> None:
        with self._lock:
            self._last = metrics

    def get_last(self) -> dict[str, Any]:
        with self._lock:
            return self._last.to_dict()


class Timer:
    def __init__(self) -> None:
        self._start = perf_counter()

    def ms(self) -> float:
        return (perf_counter() - self._start) * 1000.0


METRICS = MetricsStore()
