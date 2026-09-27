"""Public HTTP contract for Refrigerant Nameplate Analysis."""

from __future__ import annotations

import io
import json
import logging
import re
import secrets
import time
from collections.abc import Callable
from typing import AsyncContextManager, Optional

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_EDGE = 1_920
SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}
REFRIGERANT_PATTERN = re.compile(r"^R[\s-]?([0-9]{1,4}[A-Za-z]{0,3})$", re.IGNORECASE)
VERIFIED_REFRIGERANT_TYPES = frozenset(
    {
        "R-12",
        "R-22",
        "R-32",
        "R-134A",
        "R-290",
        "R-404A",
        "R-407C",
        "R-410A",
        "R-417A",
        "R-422D",
        "R-448A",
        "R-449A",
        "R-452B",
        "R-454B",
        "R-507A",
        "R-513A",
        "R-600A",
        "R-717",
        "R-744",
        "R-1233ZD",
        "R-1234YF",
        "R-1234ZE",
    }
)
logger = logging.getLogger(__name__)

CandidateReader = Callable[[Image.Image], str]
ApplicationLifespan = Callable[[FastAPI], AsyncContextManager[None]]


def normalize_refrigerant_type(raw_candidate: str) -> str | None:
    """Return one canonical, single Refrigerant Type, or reject the candidate."""
    match = REFRIGERANT_PATTERN.fullmatch(raw_candidate.strip())
    if match is None:
        return None
    return f"R-{match.group(1).upper()}"


def read_candidate_refrigerant_type(raw_model_output: str) -> tuple[str, bool] | None:
    """Read one Candidate Refrigerant Type and report whether it is verified."""
    payload = None
    decoder = json.JSONDecoder()
    for start_index, character in enumerate(raw_model_output):
        if character != "{":
            continue
        try:
            decoded, _ = decoder.raw_decode(raw_model_output, start_index)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, dict) and set(decoded) == {"refrigerant_type"}:
            payload = decoded
            break

    if payload is None:
        logger.warning("Analysis Failure: malformed model output")
        return None

    candidate = payload["refrigerant_type"]
    if not isinstance(candidate, str):
        logger.info("Analysis Failure: no Candidate Refrigerant Type")
        return None

    normalized = normalize_refrigerant_type(candidate)
    if normalized is None:
        logger.warning("Analysis Failure: ambiguous or invalid Candidate Refrigerant Type")
        return None

    is_verified = normalized in VERIFIED_REFRIGERANT_TYPES
    if not is_verified:
        logger.info("Unverified Candidate Refrigerant Type: %s", normalized)
    return normalized, is_verified


def read_supported_image(upload: UploadFile, body: bytes) -> Image.Image:
    if upload.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
    if not body or len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="이미지 크기는 10 MB 이하여야 합니다.")

    try:
        image = Image.open(io.BytesIO(body))
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail="손상된 이미지입니다.") from error

    if image.format not in SUPPORTED_PIL_FORMATS:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    normalized = image.convert("RGB")
    if max(normalized.size) > MAX_IMAGE_EDGE:
        normalized.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
    return normalized


def analysis_failure(started_at: float) -> dict[str, str | float]:
    return {
        "status": "failure",
        "message": "분석 실패",
        "analysis_time_seconds": round(time.perf_counter() - started_at, 3),
    }


def create_api(
    *,
    api_key: str | None,
    candidate_reader: CandidateReader,
    lifespan: ApplicationLifespan | None = None,
) -> FastAPI:
    """Build the single-endpoint API around a direct-model candidate reader."""
    if api_key is None or len(api_key) != 6:
        raise ValueError("ANALYSIS_API_KEY must be a six-character Shared API Key")

    api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "https://jaehyunlee123.github.io"],
        allow_credentials=False,
        allow_methods=["POST"],
        allow_headers=["X-API-Key", "Content-Type"],
    )

    @api.middleware("http")
    async def log_total_request_time(request, call_next):
        started_at = time.perf_counter()
        try:
            return await call_next(request)
        finally:
            logger.info(
                "Total request time for %s: %.3f seconds",
                request.url.path,
                time.perf_counter() - started_at,
            )

    @api.post("/analyze")
    async def analyze(
        image: Optional[UploadFile] = File(default=None),
        x_api_key: Optional[str] = Header(default=None),
    ):
        if api_key is None or x_api_key is None or not secrets.compare_digest(x_api_key, api_key):
            raise HTTPException(status_code=401, detail="유효하지 않은 API 키입니다.")
        if image is None:
            raise HTTPException(status_code=400, detail="명판 이미지가 필요합니다.")

        body = await image.read()
        nameplate_image = read_supported_image(image, body)
        started_at = time.perf_counter()

        try:
            raw_model_output = candidate_reader(nameplate_image)
            logger.info("Inference Model raw output: %s", raw_model_output)
            candidate = read_candidate_refrigerant_type(raw_model_output)
        except Exception:
            logger.exception("Analysis Failure: Inference Model execution failed")
            return analysis_failure(started_at)

        if candidate is None:
            return analysis_failure(started_at)

        refrigerant_type, is_verified = candidate

        return {
            "status": "success",
            "refrigerant_type": refrigerant_type,
            "is_verified": is_verified,
            "analysis_time_seconds": round(time.perf_counter() - started_at, 3),
        }

    return api
