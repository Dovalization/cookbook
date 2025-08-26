from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

from shared.errors import LLMError, LLMRateLimit, LLMAuthError


class HttpClient:
    """Small thin wrapper around requests.Session implementing retry/backoff.

    Keep the interface tiny so adapters can call `client.post(url, headers, json)`.
    """

    def __init__(self, session: Optional[requests.Session] = None, timeout_s: int = 60, max_retries: int = 3):
        self.session = session or requests.Session()
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    def post(self, url: str, headers: Optional[Dict[str, str]] = None, json: Optional[Dict[str, Any]] = None):
        last_err: Optional[Exception] = None
        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(url, headers=headers, json=json, timeout=self.timeout_s)
                if resp.status_code in (429, 408):
                    raise LLMRateLimit(f"Rate limited or timeout: {resp.status_code} {resp.text[:200]}")
                if 500 <= resp.status_code < 600:
                    raise LLMError(f"Server error {resp.status_code}: {resp.text[:200]}")
                if resp.status_code in (401, 403):
                    raise LLMAuthError(f"Auth failed: {resp.text[:200]}")
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, LLMError) as e:
                last_err = e
                if attempt == self.max_retries:
                    break
                time.sleep(delay)
                delay = min(delay * 2.0, 8.0)
        assert last_err is not None
        raise LLMError(f"POST {url} failed after {self.max_retries} attempts: {last_err}")
