"""Thin application client that follows the backend interaction standard.

The client owns the secret key. The backend only receives public context
material and ciphertexts.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

import httpx
import numpy as np

# Allow running without installing the package.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fhe_eval.config import PROFILE  # noqa: E402
from fhe_eval.engine import (  # noqa: E402
    b64encode,
    create_client_context,
    decrypt_scalar,
    decrypt_vector,
    encrypt_vector,
    make_public_context_bytes,
)


class FheEvalClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.context = create_client_context(PROFILE)
        self.context_id = PROFILE.context_id

    def get_context_info(self) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/v1/context")
            response.raise_for_status()
            return response.json()

    def bind(self) -> dict:
        public_b64 = b64encode(make_public_context_bytes(self.context))
        payload = {
            "context_id": self.context_id,
            "public_context_b64": public_b64,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/v1/context/bind", json=payload)
            response.raise_for_status()
            return response.json()

    def encrypt(self, values: Sequence[float]) -> str:
        return b64encode(encrypt_vector(self.context, values))

    def decrypt_vector(self, ciphertext_b64: str) -> list[float]:
        from fhe_eval.engine import b64decode

        return decrypt_vector(self.context, b64decode(ciphertext_b64))

    def decrypt_scalar(self, ciphertext_b64: str) -> float:
        from fhe_eval.engine import b64decode

        return decrypt_scalar(self.context, b64decode(ciphertext_b64))

    def add(self, left: Sequence[float], right: Sequence[float]) -> tuple[list[float], dict]:
        dimension = len(left)
        payload = {
            "context_id": self.context_id,
            "dimension": dimension,
            "left_ciphertext_b64": self.encrypt(left),
            "right_ciphertext_b64": self.encrypt(right),
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/v1/eval/add", json=payload)
            response.raise_for_status()
            body = response.json()
        return self.decrypt_vector(body["result_ciphertext_b64"]), body

    def mul_plain(
        self, values: Sequence[float], weights: Sequence[float]
    ) -> tuple[list[float], dict]:
        dimension = len(values)
        payload = {
            "context_id": self.context_id,
            "dimension": dimension,
            "ciphertext_b64": self.encrypt(values),
            "weights": list(map(float, weights)),
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/v1/eval/mul_plain", json=payload)
            response.raise_for_status()
            body = response.json()
        return self.decrypt_vector(body["result_ciphertext_b64"]), body

    def linear_score(
        self, features: Sequence[float], weights: Sequence[float], bias: float
    ) -> tuple[float, dict]:
        dimension = len(features)
        payload = {
            "context_id": self.context_id,
            "dimension": dimension,
            "features_ciphertext_b64": self.encrypt(features),
            "weights": list(map(float, weights)),
            "bias": float(bias),
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/v1/eval/linear_score", json=payload)
            response.raise_for_status()
            body = response.json()
        return self.decrypt_scalar(body["result_ciphertext_b64"]), body

    def last_metrics(self) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/v1/metrics/last")
            response.raise_for_status()
            return response.json()["metrics"]


def plaintext_linear_score(features: Sequence[float], weights: Sequence[float], bias: float) -> float:
    return float(np.dot(np.asarray(features, dtype=float), np.asarray(weights, dtype=float)) + bias)
