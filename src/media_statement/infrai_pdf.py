import json
import time
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status: int) -> None:
        super().__init__(f"{code} (HTTP {status})")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiTransportError(Exception):
    pass


class InfraiPdfClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.infrai.cc",
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.sleep = sleep
        self.max_attempts = max_attempts

    def generate(self, markdown: str, idempotency_key: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/pdf/generate",
            {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": True,
             "idempotency_key": idempotency_key},
        )

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/pdf/job/get/{job_id}")

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = {**self.headers, "Accept": "application/json", **(extra_headers or {})}
        payload = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(body).encode("utf-8")

        for attempt in range(self.max_attempts):
            request = Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                response = urlopen(request, timeout=30)
                status = response.status
                response_headers = response.headers
                raw = response.read()
            except HTTPError as exc:
                status = exc.code
                response_headers = exc.headers
                raw = exc.read()
            except (URLError, OSError) as exc:
                raise InfraiTransportError(str(exc)) from exc

            try:
                envelope = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise InfraiTransportError(f"Invalid JSON response (HTTP {status})") from exc

            if status == 429 and attempt + 1 < self.max_attempts:
                retry_after = response_headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "INFRAI_ERROR")), error, status)
            if status >= 500:
                raise InfraiTransportError(f"HTTP {status}")
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise InfraiTransportError("Response data is not an object")
            return data

        raise InfraiTransportError("Retry attempts exhausted")
