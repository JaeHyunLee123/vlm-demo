from __future__ import annotations

import io
import json
import unittest
from collections.abc import Callable

from fastapi.testclient import TestClient
from PIL import Image

from backend.api import create_api


def make_png_bytes() -> bytes:
    image = Image.new("RGB", (40, 20), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class AnalyzeApiContractTests(unittest.TestCase):
    api_key = "A1b2C3"

    def make_client(self, candidate: str | Callable[[Image.Image], str]) -> TestClient:
        if callable(candidate):
            reader = candidate
        else:
            reader = lambda _image: candidate
        return TestClient(create_api(api_key=self.api_key, candidate_reader=reader))

    def post_image(self, client: TestClient, *, key: str | None = None, body: bytes | None = None, content_type: str = "image/png"):
        headers = {} if key is None else {"X-API-Key": key}
        return client.post(
            "/analyze",
            headers=headers,
            files={"image": ("nameplate.png", body if body is not None else make_png_bytes(), content_type)},
        )

    def test_returns_normalized_refrigerant_type_and_analysis_time_for_confirmed_candidate(self) -> None:
        client = self.make_client(json.dumps({"refrigerant_type": "r410a"}))

        response = self.post_image(client, key=self.api_key)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["refrigerant_type"], "R-410A")
        self.assertIsInstance(response.json()["analysis_time_seconds"], float)

    def test_rejects_missing_or_invalid_shared_api_key(self) -> None:
        client = self.make_client(json.dumps({"refrigerant_type": "R-32"}))

        self.assertEqual(self.post_image(client).status_code, 401)
        self.assertEqual(self.post_image(client, key="wrong").status_code, 401)

    def test_rejects_an_invalid_shared_api_key_configuration(self) -> None:
        with self.assertRaises(ValueError):
            create_api(api_key="not-six", candidate_reader=lambda _image: "")

    def test_rejects_a_missing_nameplate_image_with_400(self) -> None:
        client = self.make_client(json.dumps({"refrigerant_type": "R-32"}))

        response = client.post("/analyze", headers={"X-API-Key": self.api_key})

        self.assertEqual(response.status_code, 400)

    def test_rejects_unsupported_or_oversized_upload_before_analysis(self) -> None:
        calls = 0

        def reader(_image: Image.Image) -> str:
            nonlocal calls
            calls += 1
            return json.dumps({"refrigerant_type": "R-32"})

        client = self.make_client(reader)
        unsupported = self.post_image(client, key=self.api_key, content_type="image/gif")
        oversized = self.post_image(client, key=self.api_key, body=b"x" * (10 * 1024 * 1024 + 1))

        self.assertEqual(unsupported.status_code, 400)
        self.assertEqual(oversized.status_code, 400)
        self.assertEqual(calls, 0)

    def test_normalizes_a_large_supported_image_before_reading_candidate(self) -> None:
        observed_sizes: list[tuple[int, int]] = []

        def reader(image: Image.Image) -> str:
            observed_sizes.append(image.size)
            return json.dumps({"refrigerant_type": "R-32"})

        original = Image.new("RGB", (3_000, 1_500), color="white")
        buffer = io.BytesIO()
        original.save(buffer, format="PNG")
        response = self.post_image(self.make_client(reader), key=self.api_key, body=buffer.getvalue())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(observed_sizes, [(1_920, 960)])

    def test_returns_analysis_failure_without_refrigerant_for_malformed_or_ambiguous_candidate(self) -> None:
        for candidate in (
            "R-32",
            json.dumps({"refrigerant_type": "R-32 / R-410A"}),
            json.dumps({"refrigerant_type": "R-9999ABC"}),
            json.dumps({"refrigerant_type": None}),
        ):
            with self.subTest(candidate=candidate):
                response = self.post_image(self.make_client(candidate), key=self.api_key)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {
                        "status": "failure",
                        "message": "분석 실패",
                        "analysis_time_seconds": response.json()["analysis_time_seconds"],
                    },
                )
                self.assertIsInstance(response.json()["analysis_time_seconds"], float)
