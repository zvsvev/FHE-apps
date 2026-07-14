#!/usr/bin/env python3
"""End-to-end demo: encrypted linear scoring via the FHE backend."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "client"))

from fhe_client import FheEvalClient, plaintext_linear_score  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo linear_score against FHE backend")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--dim", type=int, choices=[8, 16], default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    features = rng.normal(0.0, 1.0, size=args.dim).tolist()
    weights = rng.normal(0.0, 0.5, size=args.dim).tolist()
    bias = float(rng.normal(0.0, 0.1))

    client = FheEvalClient(base_url=args.base_url)
    info = client.get_context_info()
    print("context:", json.dumps(info, indent=2))

    bind = client.bind()
    print("bind:", bind)

    baseline = plaintext_linear_score(features, weights, bias)
    result, meta = client.linear_score(features, weights, bias)
    abs_err = abs(result - baseline)
    rel_err = abs_err / max(abs(baseline), 1e-12)

    print(f"dimension     : {args.dim}")
    print(f"baseline y    : {baseline:.10f}")
    print(f"fhe decrypt y : {result:.10f}")
    print(f"abs error     : {abs_err:.3e}")
    print(f"rel error     : {rel_err:.3e}")
    print(f"backend eval  : {meta['eval_ms']:.2f} ms")
    print("metrics:", json.dumps(client.last_metrics(), indent=2))

    if rel_err > 1e-3:
        print("FAIL: relative error exceeds 1e-3", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
