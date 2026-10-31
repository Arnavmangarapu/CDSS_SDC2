"""Shared JSON generation with provider and model fallbacks."""

import json
from contextvars import ContextVar
from typing import Callable, Dict, Optional

import requests

from backend.config import settings
from backend.services.telemetry import stage

_response_schema = ContextVar("response_schema", default=None)


class LLMFallback:
    MODEL_IDS = {
        "Gemini Flash Lite": "gemini-3.5-flash-lite",
        "Gemini Flash": "gemini-3.8-flash",
        "Cohere": "command-r-plus-08-2024",
        "Mistral": "mistral-small-latest",
        "OpenRouter": "openrouter/free (underlying model varies)",
    }

    def __init__(self):
        self.last_provider: str | None = None
        self.last_model: str | None = None
        self.last_response_metadata: dict = {}
        self.providers = (
            ("Gemini Flash Lite", settings.GEMINI_API_KEY, self._gemini_lite),
            ("Gemini Flash", settings.GEMINI_API_KEY, self._gemini_flash),
            ("Cohere", settings.COHERE_API_KEY, self._cohere),
            ("Mistral", settings.MISTRAL_API_KEY, self._mistral),
            ("OpenRouter", settings.OPENROUTER_API_KEY, self._openrouter),
        )

    def generate_json(
        self,
        prompt: str,
        system_instruction: str,
        validate: Optional[Callable[[Dict], None]] = None,
        response_schema: dict | None = None,
    ) -> Optional[Dict]:
        token = _response_schema.set(response_schema)
        try:
            return self._generate_json(prompt, system_instruction, validate)
        finally:
            _response_schema.reset(token)

    def _generate_json(
        self,
        prompt: str,
        system_instruction: str,
        validate: Optional[Callable[[Dict], None]] = None,
    ) -> Optional[Dict]:
        """Try configured providers until one returns valid, usable JSON."""
        self.last_provider = None
        self.last_model = None
        self.last_response_metadata = {}
        for name, key, call in self.providers:
            if not key or not key.strip():
                continue
            try:
                self.last_response_metadata = {}
                with stage("model_call_wall"):
                    content = call(key.strip(), prompt, system_instruction)
                content = content.strip()
                if content.startswith("```"):
                    content = content[3:]
                    if content.lower().startswith("json"):
                        content = content[4:]
                    content = content.strip()
                    if content.endswith("```"):
                        content = content[:-3].strip()
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("Response was not a JSON object")
                if validate:
                    validate(parsed)
                self.last_provider = name
                self.last_model = self.MODEL_IDS.get(name, "unknown")
                print(f"LLM fallback: {name} succeeded")
                return parsed
            except (requests.RequestException, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
                # Do not log response bodies, prompts, URLs with secrets, or API keys.
                status = getattr(getattr(exc, "response", None), "status_code", None)
                detail = f"HTTP {status}" if status else type(exc).__name__
                print(f"LLM fallback: {name} failed ({detail}); trying next provider")
        return None

    def response_trace(self) -> dict:
        """Requested alias and provider-returned identity are deliberately separate."""
        return {"provider": self.last_provider, "model": self.last_model,
                "requested_model": self.last_model, **self.last_response_metadata}

    @staticmethod
    def _post(url: str, headers: Dict, payload: Dict) -> Dict:
        response = requests.post(url, headers=headers, json=payload, timeout=(5, 35))
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or data.get("error"):
            raise ValueError("Provider returned an error or invalid response")
        return data

    def _gemini(self, model: str, key: str, prompt: str, system: str) -> str:
        data = self._post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"x-goog-api-key": key, "Content-Type": "application/json"},
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                     **({"responseJsonSchema": _response_schema.get()}
                                        if _response_schema.get() is not None else {})},
            },
        )
        self.last_response_metadata = {
            "returned_model_version": data.get("modelVersion"),
            "response_id": data.get("responseId"),
            "usage_metadata": {key: value for key, value in data.get("usageMetadata", {}).items()
                               if key.endswith("TokenCount") and isinstance(value, int)},
            "finish_reasons": [item.get("finishReason") for item in data.get("candidates", [])],
        }
        return "".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"]
                       if not part.get("thought", False))

    def _gemini_lite(self, key: str, prompt: str, system: str) -> str:
        return self._gemini("gemini-3.5-flash-lite", key, prompt, system)

    def _gemini_flash(self, key: str, prompt: str, system: str) -> str:
        return self._gemini("gemini-3.8-flash", key, prompt, system)

    def _cohere(self, key: str, prompt: str, system: str) -> str:
        data = self._post(
            "https://api.cohere.ai/v2/chat",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {
                "model": "command-r-plus-08-2024",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0,
            },
        )
        return "".join(part.get("text", "") for part in data["message"]["content"])

    def _mistral(self, key: str, prompt: str, system: str) -> str:
        data = self._post(
            "https://api.mistral.ai/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {
                "model": "mistral-small-latest",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
        )
        return data["choices"][0]["message"]["content"]

    def _openrouter(self, key: str, prompt: str, system: str) -> str:
        data = self._post(
            "https://openrouter.ai/api/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {
                "model": "openrouter/free",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0,
            },
        )
        return data["choices"][0]["message"]["content"]
