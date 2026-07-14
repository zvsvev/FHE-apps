"""API tests using FastAPI TestClient — real CKKS evaluation path."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fhe_eval.api.app import create_app
from fhe_eval.config import PROFILE
from fhe_eval.engine import (
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
def api(client_ctx):
    app = create_app()
    with TestClient(app) as test_client:
        # Bind public context once per test app.
        resp = test_client.post(
            "/v1/context/bind",
            json={
                "context_id": PROFILE.context_id,
                "public_context_b64": b64encode(make_public_context_bytes(client_ctx)),
            },
        )
        assert resp.status_code == 200, resp.text
        yield test_client, client_ctx


def test_get_context(api):
    test_client, _ = api
    resp = test_client.get("/v1/context")
    assert resp.status_code == 200
    body = resp.json()
    assert body["context_id"] == PROFILE.context_id
    assert body["allowed_ops"] == list(PROFILE.allowed_ops)
    assert body["bound"] is True


def test_linear_score_endpoint(api):
    test_client, ctx = api
    dim = 8
    x = np.linspace(-0.5, 0.5, dim).tolist()
    w = np.linspace(0.1, 0.8, dim).tolist()
    bias = 0.2
    resp = test_client.post(
        "/v1/eval/linear_score",
        json={
            "context_id": PROFILE.context_id,
            "dimension": dim,
            "features_ciphertext_b64": b64encode(encrypt_vector(ctx, x)),
            "weights": w,
            "bias": bias,
        },
    )
    assert resp.status_code == 200, resp.text
    result = decrypt_scalar(ctx, __import__("base64").b64decode(resp.json()["result_ciphertext_b64"]))
    expected = float(np.dot(x, w) + bias)
    rel = abs(result - expected) / max(abs(expected), 1e-12)
    assert rel < 1e-3


def test_add_endpoint(api):
    test_client, ctx = api
    left = [1.0] * 8
    right = [2.0] * 8
    resp = test_client.post(
        "/v1/eval/add",
        json={
            "context_id": PROFILE.context_id,
            "dimension": 8,
            "left_ciphertext_b64": b64encode(encrypt_vector(ctx, left)),
            "right_ciphertext_b64": b64encode(encrypt_vector(ctx, right)),
        },
    )
    assert resp.status_code == 200, resp.text
    from fhe_eval.engine import b64decode

    dec = decrypt_vector(ctx, b64decode(resp.json()["result_ciphertext_b64"]))
    assert np.allclose(dec, np.array(left) + np.array(right), atol=1e-3)


def test_reject_secret_key(api):
    test_client, ctx = api
    resp = test_client.post(
        "/v1/eval/add",
        json={
            "context_id": PROFILE.context_id,
            "dimension": 8,
            "left_ciphertext_b64": b64encode(encrypt_vector(ctx, [1.0] * 8)),
            "right_ciphertext_b64": b64encode(encrypt_vector(ctx, [1.0] * 8)),
            "secret_key": "should-be-rejected",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["reject_reason"] == "secret_key_forbidden"


def test_reject_bad_dimension(api):
    test_client, ctx = api
    resp = test_client.post(
        "/v1/eval/mul_plain",
        json={
            "context_id": PROFILE.context_id,
            "dimension": 7,
            "ciphertext_b64": b64encode(encrypt_vector(ctx, [1.0] * 8)),
            "weights": [1.0] * 7,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["reject_reason"] == "dimension_not_allowed"


def test_reject_wrong_context_id(api):
    test_client, ctx = api
    resp = test_client.post(
        "/v1/eval/linear_score",
        json={
            "context_id": "wrong-id",
            "dimension": 8,
            "features_ciphertext_b64": b64encode(encrypt_vector(ctx, [0.1] * 8)),
            "weights": [0.1] * 8,
            "bias": 0.0,
        },
    )
    assert resp.status_code == 400
