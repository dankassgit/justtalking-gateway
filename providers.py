import os
import requests

DEFAULT_TIMEOUT_SECONDS = float(os.getenv("JT_HTTP_TIMEOUT", "20"))

def call_anthropic_messages(*, model: str, system_text: str, user_text: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY")

    url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": int(os.getenv("JT_MAX_TOKENS", "700")),
        "system": system_text,
        "messages": [{"role": "user", "content": user_text}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
    r.raise_for_status()
    data = r.json()
    parts = []
    for blk in data.get("content", []):
        if blk.get("type") == "text" and "text" in blk:
            parts.append(blk["text"])
    return "".join(parts).strip() or "(no text)"

def call_xai_chat_completions(*, model: str, system_text: str, user_text: str) -> str:
    api_key = os.getenv("XAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing XAI_API_KEY")

    base = os.getenv("XAI_BASE_URL", "https://api.x.ai")
    url = base.rstrip("/") + "/v1/chat/completions"
    headers = {"authorization": f"Bearer {api_key}", "content-type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        "temperature": float(os.getenv("JT_TEMPERATURE", "0.8")),
    }
    r = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
    r.raise_for_status()
    data = r.json()
    return (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip() or "(no text)"
