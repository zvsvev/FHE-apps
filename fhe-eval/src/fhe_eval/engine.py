"""CKKS evaluation engine backed by TenSEAL (Microsoft SEAL).

The server only holds a public context (no secret key). Ciphertexts are
deserialized and evaluated; decryption always happens on the client.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Sequence

import tenseal as ts

from fhe_eval.config import PROFILE, CkksProfile


class EngineError(ValueError):
    """Raised when evaluation cannot proceed."""


@dataclass
class BoundContext:
    context_id: str
    public_context: ts.Context


def create_client_context(profile: CkksProfile = PROFILE) -> ts.Context:
    """Create a full client context (includes secret key)."""
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=profile.poly_modulus_degree,
        coeff_mod_bit_sizes=list(profile.coeff_mod_bit_sizes),
    )
    context.generate_galois_keys()
    context.global_scale = profile.global_scale
    return context


def make_public_context_bytes(context: ts.Context) -> bytes:
    """Serialize context without secret key for server binding."""
    return context.serialize(
        save_public_key=True,
        save_secret_key=False,
        save_galois_keys=True,
        save_relin_keys=True,
    )


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def encrypt_vector(context: ts.Context, values: Sequence[float]) -> bytes:
    vec = ts.ckks_vector(context, list(map(float, values)))
    return vec.serialize()


def decrypt_vector(context: ts.Context, ciphertext: bytes) -> list[float]:
    vec = ts.ckks_vector_from(context, ciphertext)
    return list(vec.decrypt())


def decrypt_scalar(context: ts.Context, ciphertext: bytes) -> float:
    values = decrypt_vector(context, ciphertext)
    if not values:
        raise EngineError("Empty decryption result")
    return float(values[0])


class EvalEngine:
    """Server-side evaluator. Never stores or accepts secret keys."""

    def __init__(self, profile: CkksProfile = PROFILE) -> None:
        self.profile = profile
        self._bound: BoundContext | None = None

    @property
    def is_bound(self) -> bool:
        return self._bound is not None

    def bind_public_context(self, context_id: str, public_context_b64: str) -> None:
        if context_id != self.profile.context_id:
            raise EngineError(
                f"context_id mismatch: expected {self.profile.context_id}, got {context_id}"
            )
        raw = b64decode(public_context_b64)
        public_context = ts.context_from(raw)
        if public_context.has_secret_key():
            raise EngineError("public context must not contain a secret key")
        self._bound = BoundContext(context_id=context_id, public_context=public_context)

    def _require_bound(self, context_id: str) -> BoundContext:
        if self._bound is None:
            raise EngineError("no public context bound; call /v1/context/bind first")
        if context_id != self._bound.context_id:
            raise EngineError(
                f"context_id mismatch: expected {self._bound.context_id}, got {context_id}"
            )
        return self._bound

    def _load_vector(self, bound: BoundContext, ciphertext_b64: str) -> ts.CKKSVector:
        return ts.ckks_vector_from(bound.public_context, b64decode(ciphertext_b64))

    def add(
        self,
        context_id: str,
        left_b64: str,
        right_b64: str,
        dimension: int,
    ) -> bytes:
        bound = self._require_bound(context_id)
        left = self._load_vector(bound, left_b64)
        right = self._load_vector(bound, right_b64)
        if left.size() != dimension or right.size() != dimension:
            raise EngineError("ciphertext dimension does not match declared dimension")
        return (left + right).serialize()

    def mul_plain(
        self,
        context_id: str,
        ciphertext_b64: str,
        weights: Sequence[float],
        dimension: int,
    ) -> bytes:
        bound = self._require_bound(context_id)
        vec = self._load_vector(bound, ciphertext_b64)
        if vec.size() != dimension or len(weights) != dimension:
            raise EngineError("dimension mismatch between ciphertext and weights")
        return (vec * list(map(float, weights))).serialize()

    def linear_score(
        self,
        context_id: str,
        features_b64: str,
        weights: Sequence[float],
        bias: float,
        dimension: int,
    ) -> bytes:
        """Compute y = w·x + b on encrypted x; returns ciphertext of the scalar result."""
        bound = self._require_bound(context_id)
        x = self._load_vector(bound, features_b64)
        if x.size() != dimension or len(weights) != dimension:
            raise EngineError("dimension mismatch between ciphertext and weights")
        # Element-wise product then sum of slots, then add public bias.
        weighted = x * list(map(float, weights))
        score = weighted.sum() + float(bias)
        return score.serialize()
