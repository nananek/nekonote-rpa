"""AI/LLM API integration for nekonote scripts.

Usage::

    from nekonote import ai

    ai.configure(provider="openai", api_key="sk-...", default_model="gpt-4o")
    result = ai.generate("Summarize this text: ...")
    data = ai.generate_json("Extract invoice data: ...", schema={...})
"""

from __future__ import annotations

import json as _json
from typing import Any

from nekonote.http import post as _http_post

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_config: dict[str, Any] = {}


def configure(
    *,
    provider: str = "openai",
    api_key: str = "",
    default_model: str = "",
    base_url: str = "",
) -> None:
    """Configure the AI provider.

    Supported providers: ``"openai"``, ``"azure_openai"``, ``"gemini"``.
    """
    _config["provider"] = provider
    _config["api_key"] = api_key
    _config["default_model"] = default_model
    if base_url:
        _config["base_url"] = base_url


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate(
    prompt: str,
    *,
    provider: str = "",
    model: str = "",
    api_key: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Generate text from a prompt. Returns the response text."""
    p = provider or _config.get("provider", "openai")
    k = api_key or _config.get("api_key", "")
    m = model or _config.get("default_model", "")

    if p == "openai":
        return _openai_generate(prompt, model=m or "gpt-4o", api_key=k,
                                system=system, temperature=temperature, max_tokens=max_tokens)
    elif p == "gemini":
        return _gemini_generate(prompt, model=m or "gemini-pro", api_key=k,
                                temperature=temperature, max_tokens=max_tokens)
    else:
        raise ValueError(f"Unsupported provider: {p!r}")


def generate_json(
    prompt: str,
    *,
    schema: dict[str, Any] | None = None,
    provider: str = "",
    model: str = "",
    api_key: str = "",
    system: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> Any:
    """Generate structured JSON output.

    If *schema* is provided, it's included in the system prompt to guide
    the model's output format.
    """
    sys_prompt = system or "You are a helpful assistant that responds only in valid JSON."
    if schema:
        sys_prompt += f"\n\nRespond with JSON matching this schema:\n{_json.dumps(schema, indent=2)}"

    text = generate(
        prompt,
        provider=provider,
        model=model,
        api_key=api_key,
        system=sys_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Strip markdown code fence if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    return _json.loads(text)


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


def _openai_generate(
    prompt: str,
    *,
    model: str,
    api_key: str,
    system: str,
    temperature: float,
    max_tokens: int,
) -> str:
    base = _config.get("base_url", "https://api.openai.com/v1")
    url = f"{base}/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = _http_post(
        url,
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )

    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API error ({resp.status_code}): {resp.text()}")

    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _gemini_generate(
    prompt: str,
    *,
    model: str,
    api_key: str,
    temperature: float,
    max_tokens: int,
) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    resp = _http_post(
        url,
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        },
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text()}")

    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
