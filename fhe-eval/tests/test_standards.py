"""Standards validation unit tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fhe_eval.config import PROFILE
from fhe_eval.standards import StandardsViolation, validate_eval_request


def test_accepts_valid_request():
    payload = SimpleNamespace(secret_key=None)
    validate_eval_request(
        operation="linear_score",
        context_id=PROFILE.context_id,
        dimension=8,
        payload=payload,
        weights=[0.1] * 8,
    )


def test_rejects_unknown_operation():
    with pytest.raises(StandardsViolation) as exc:
        validate_eval_request(
            operation="decrypt",
            context_id=PROFILE.context_id,
            dimension=8,
            payload=SimpleNamespace(secret_key=None),
        )
    assert exc.value.reason == "operation_not_allowed"


def test_rejects_secret_key():
    with pytest.raises(StandardsViolation) as exc:
        validate_eval_request(
            operation="add",
            context_id=PROFILE.context_id,
            dimension=8,
            payload=SimpleNamespace(secret_key="abc"),
        )
    assert exc.value.reason == "secret_key_forbidden"
