"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from fhe_eval import __version__
from fhe_eval.api.routes import router
from fhe_eval.engine import EvalEngine
from fhe_eval.metrics import METRICS


def create_app() -> FastAPI:
    app = FastAPI(
        title="FHE Evaluation Backend",
        description=(
            "Backend layanan evaluasi Fully Homomorphic Encryption (CKKS/TenSEAL) "
            "dengan standar interaksi untuk pengembang aplikasi."
        ),
        version=__version__,
    )
    app.state.engine = EvalEngine()
    app.state.metrics = METRICS
    app.include_router(router)
    return app


app = create_app()
