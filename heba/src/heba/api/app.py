"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from heba import __version__
from heba.api.routes import router
from heba.engine import EvalEngine
from heba.metrics import METRICS


def create_app() -> FastAPI:
    app = FastAPI(
        title="HEBA Backend",
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
