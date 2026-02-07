import os
import json
import urllib.request
import urllib.error


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-sonnet-4.5")
ANTHROPIC_VERSION = os.getenv("ANTHROPIC_VERSION", "2023-06-01")


def generate_reply(role_text: str, user_text: str, temperature: float = 1.0, max_tokens: int = 120) -> str:
    """
    Calls Anthropic via raw HTTPS so we don't need the 'anthropic' Python package.
    """
    if not ANTHROPIC_API_KEY:
        return "[gateway] missing ANTHROPIC_API_KEY"

    payload = {
        "model": DEFAULT_MODEL,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "system": role_text or "You are a playful assistant. Keep replies short.",
        "messages": [{"role": "user", "content": user_text or ""}],
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)

        content = data.get("content") or []
        if isinstance(content, list) and content and isinstance(content[0], dict):
            text = (content[0].get("text") or "").strip()
            return text or "[gateway] empty reply"

        return "[gateway] unexpected response"

    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode("utf-8")
        except Exception:
            err = ""
        return f"[gateway] http {e.code} {err[:200]}".strip()

    except Exception as e:
        return f"[gateway] error {type(e).__name__}"
