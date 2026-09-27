"""Modal deployment entry point for the Refrigerant Nameplate Analysis API."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

import modal
from fastapi import FastAPI

from backend.api import create_api
from backend.model import QwenCandidateReader

app = modal.App("refrigerant-nameplate-analysis")
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "fastapi",
    "modal",
    "Pillow",
    "python-multipart",
    "qwen-vl-utils",
    "torch",
    "transformers>=4.49.0",
)


@app.function(
    image=image,
    gpu="T4",
    max_containers=1,
    scaledown_window=120,
    secrets=[modal.Secret.from_name("refrigerant-demo-secret")],
)
@modal.concurrent(max_inputs=1)
@modal.asgi_app()
def api() -> FastAPI:
    reader: QwenCandidateReader | None = None

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        nonlocal reader
        reader = QwenCandidateReader()
        yield

    def candidate_reader(image):
        if reader is None:
            raise RuntimeError("Inference Model has not loaded")
        return reader(image)

    return create_api(
        api_key=os.environ.get("ANALYSIS_API_KEY"),
        candidate_reader=candidate_reader,
        lifespan=lifespan,
    )
