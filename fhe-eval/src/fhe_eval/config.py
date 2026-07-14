"""CKKS parameter profile shared by backend and client."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CkksProfile:
    """Fixed CKKS profile used by the prototype (≈128-bit class parameters)."""

    context_id: str = "ckks-n8192-s40-d8-16"
    scheme: str = "CKKS"
    poly_modulus_degree: int = 8192
    coeff_mod_bit_sizes: tuple[int, ...] = (60, 40, 40, 60)
    global_scale: float = 2**40
    allowed_dims: tuple[int, ...] = (8, 16)
    allowed_ops: tuple[str, ...] = ("add", "mul_plain", "linear_score")
    engine_name: str = "tenseal-ckks"
    security_note: str = (
        "Prototype profile for academic evaluation; not a formal security certification."
    )


PROFILE = CkksProfile()
