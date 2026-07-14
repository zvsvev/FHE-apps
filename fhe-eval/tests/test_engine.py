"""Unit tests for the TenSEAL CKKS engine (no HTTP)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fhe_eval.config import PROFILE
from fhe_eval.engine import (
    EvalEngine,
    b64encode,
    create_client_context,
    decrypt_scalar,
    decrypt_vector,
    encrypt_vector,
    make_public_context_bytes,
)


@pytest.fixture()
def client_ctx():
    return create_client_context()


@pytest.fixture()
def engine(client_ctx):
    eng = EvalEngine()
    eng.bind_public_context(
        PROFILE.context_id,
        b64encode(make_public_context_bytes(client_ctx)),
    )
    return eng


def test_add_matches_plaintext(client_ctx, engine):
    left = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    right = [0.5] * 8
    out = engine.add(
        PROFILE.context_id,
        b64encode(encrypt_vector(client_ctx, left)),
        b64encode(encrypt_vector(client_ctx, right)),
        8,
    )
    dec = decrypt_vector(client_ctx, out)
    expected = np.asarray(left) + np.asarray(right)
    assert np.allclose(dec, expected, atol=1e-3)


def test_mul_plain_matches_plaintext(client_ctx, engine):
    x = [1.0, -1.0, 2.0, -2.0, 0.5, 0.25, 3.0, 1.5]
    w = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    out = engine.mul_plain(
        PROFILE.context_id,
        b64encode(encrypt_vector(client_ctx, x)),
        w,
        8,
    )
    dec = decrypt_vector(client_ctx, out)
    expected = np.asarray(x) * np.asarray(w)
    assert np.allclose(dec, expected, atol=1e-3)


def test_linear_score_matches_plaintext(client_ctx, engine):
    x = np.linspace(-1.0, 1.0, 8).tolist()
    w = np.linspace(0.2, 1.0, 8).tolist()
    bias = 0.35
    out = engine.linear_score(
        PROFILE.context_id,
        b64encode(encrypt_vector(client_ctx, x)),
        w,
        bias,
        8,
    )
    dec = decrypt_scalar(client_ctx, out)
    expected = float(np.dot(x, w) + bias)
    rel = abs(dec - expected) / max(abs(expected), 1e-12)
    assert rel < 1e-3


def test_reject_secret_in_public_context(client_ctx):
    eng = EvalEngine()
    # Explicitly include the secret key — backend must refuse binding.
    full = b64encode(
        client_ctx.serialize(
            save_public_key=True,
            save_secret_key=True,
            save_galois_keys=True,
            save_relin_keys=True,
        )
    )
    with pytest.raises(Exception):
        eng.bind_public_context(PROFILE.context_id, full)
