"""
Adapters for multiple LLM providers with clear contracts and readable structure.

Design goals:
- Explicit contracts via Protocols / TypedDicts (TS-like clarity).
- Small helpers for payload building and parsing per provider.
- Narrow exception handling with uniform error messages.
- Local imports of LLMResult to avoid circular imports at import time.

Dependencies expected:
- shared.http_client.HttpClient: exposes .post(url, headers=?, json=?)-> dict-like
- shared.errors: LLMAuthError, LLMError
- shared.llm: LLMResult.from_provider(provider, raw, text, model, usage)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Protocol, TypedDict, Literal, runtime_checkable

from shared.http_client import HttpClient
from shared.errors import LLMAuthError, LLMError


# ---------- Public contracts (TS-like) ----------

class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


@runtime_checkable
class LLMConfig(Protocol):
    # Core model knobs
    model: str
    temperature: float
    max_tokens: int | None

    # Provider-specific config
    anthropic_version: str

    # Provider keys/URLs
    openai_api_key: str | None
    anthropic_api_key: str | None

    def openai_url(self) -> str: ...
    def anthropic_url(self) -> str: ...
    def ollama_url(self) -> str: ...


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class ProviderAdapter(Protocol):
    def chat(self, cfg: LLMConfig, messages: List[ChatMessage], client: HttpClient):
        """Return shared.llm.LLMResult"""


# ---------- Base utilities ----------

@dataclass(frozen=True)
class _JsonResponse:
    raw: Dict[str, Any]


class BaseAdapter:
    JSON_CT = "application/json"

    @staticmethod
    def require(value: str | None, name: str) -> str:
        if not value:
            raise LLMAuthError(f"Missing {name}")
        return value

    @staticmethod
    def ensure_dict(obj: Any, provider: Provider) -> Dict[str, Any]:
        if not isinstance(obj, dict):
            raise LLMError(f"{provider.value}: expected JSON object, got {type(obj)}")
        return obj

    @staticmethod
    def split_system_message(messages: List[ChatMessage]) -> tuple[str | None, List[ChatMessage]]:
        """Extract first system message and return (system, rest)."""
        system: str | None = None
        core: List[ChatMessage] = []
        for m in messages:
            if m["role"] == "system" and system is None:
                system = m["content"]
            else:
                core.append(m)
        return system, core


# ---------- OpenAI helpers ----------

def _build_openai_payload(cfg: LLMConfig, messages: List[ChatMessage]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
    }
    if cfg.max_tokens is not None:
        payload["max_tokens"] = cfg.max_tokens
    return payload


def _parse_openai_text(raw: Dict[str, Any]) -> str:
    try:
        return raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"openai: unexpected response shape: {e}. Raw: {raw!r}") from e


# ---------- Anthropic helpers ----------

def _map_anthropic_role(role: str) -> Literal["user", "assistant"]:
    return role if role in ("user", "assistant") else "user"


def _to_anthropic_messages(msgs: List[ChatMessage]) -> List[Dict[str, Any]]:
    return [
        {
            "role": _map_anthropic_role(m["role"]),
            "content": [{"type": "text", "text": m["content"]}],
        }
        for m in msgs
    ]


def _build_anthropic_payload(
    cfg: LLMConfig,
    messages: List[ChatMessage],
    system_prompt: str | None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": cfg.model,
        "max_tokens": cfg.max_tokens or 1024,
        "temperature": cfg.temperature,
        "messages": _to_anthropic_messages(messages),
    }
    if system_prompt:
        payload["system"] = system_prompt
    return payload


def _parse_anthropic_text(raw: Dict[str, Any]) -> str:
    try:
        blocks = raw["content"]
        if not isinstance(blocks, list):
            raise TypeError("content is not a list")
        text = "".join(
            b.get("text", "")
            for b in blocks
            if isinstance(b, dict) and b.get("type") == "text"
        ).strip()
        return text
    except (KeyError, TypeError) as e:
        raise LLMError(f"anthropic: unexpected response shape: {e}. Raw: {raw!r}") from e


# ---------- Ollama helpers ----------

def _build_ollama_payload(cfg: LLMConfig, messages: List[ChatMessage]) -> Dict[str, Any]:
    options: Dict[str, Any] = {"temperature": cfg.temperature}
    if cfg.max_tokens is not None:
        options["num_predict"] = cfg.max_tokens
    return {
        "model": cfg.model,
        "messages": messages,
        "stream": False,
        "options": options,
    }


def _parse_ollama_text(raw: Dict[str, Any]) -> str:
    try:
        msg = raw.get("message") or {}
        if not isinstance(msg, dict):
            raise TypeError("message is not an object")
        return msg.get("content", "") or ""
    except Exception as e:
        raise LLMError(f"ollama: unexpected response shape: {e}. Raw: {raw!r}") from e


# ---------- Adapters ----------

class OpenAIAdapter(BaseAdapter):
    def chat(self, cfg: LLMConfig, messages: List[ChatMessage], client: HttpClient):
        api_key = self.require(cfg.openai_api_key, "OPENAI_API_KEY")
        url = cfg.openai_url()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": self.JSON_CT,
        }
        payload = _build_openai_payload(cfg, messages)

        raw = self.ensure_dict(client.post(url, headers=headers, json=payload), Provider.OPENAI)
        text = _parse_openai_text(raw)

        # local import to avoid circular dependency at import time
        from shared.llm import LLMResult  # type: ignore
        return LLMResult.from_provider(Provider.OPENAI.value, raw, text, cfg.model, raw.get("usage"))


class AnthropicAdapter(BaseAdapter):
    def chat(self, cfg: LLMConfig, messages: List[ChatMessage], client: HttpClient):
        api_key = self.require(cfg.anthropic_api_key, "ANTHROPIC_API_KEY")
        url = cfg.anthropic_url()

        system_prompt, core = self.split_system_message(messages)
        headers = {
            "x-api-key": api_key,
            "anthropic-version": cfg.anthropic_version,
            "content-type": self.JSON_CT,
        }
        payload = _build_anthropic_payload(cfg, core, system_prompt)

        raw = self.ensure_dict(client.post(url, headers=headers, json=payload), Provider.ANTHROPIC)
        text = _parse_anthropic_text(raw)

        from shared.llm import LLMResult  # type: ignore
        return LLMResult.from_provider(Provider.ANTHROPIC.value, raw, text, cfg.model, raw.get("usage"))


class OllamaAdapter(BaseAdapter):
    def chat(self, cfg: LLMConfig, messages: List[ChatMessage], client: HttpClient):
        url = cfg.ollama_url()
        payload = _build_ollama_payload(cfg, messages)

        raw = self.ensure_dict(client.post(url, json=payload), Provider.OLLAMA)
        text = _parse_ollama_text(raw)

        from shared.llm import LLMResult  # type: ignore
        return LLMResult.from_provider(Provider.OLLAMA.value, raw, text, cfg.model, raw.get("eval_count"))
