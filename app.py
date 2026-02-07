import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from flask import Flask, request, jsonify

from providers import XAIProvider

APP_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = APP_ROOT / "config"
ROLES_DIR = CONFIG_DIR / "roles"

app = Flask(__name__)

_provider: Optional[XAIProvider] = None


def get_provider() -> XAIProvider:
    global _provider
    if _provider is None:
        _provider = XAIProvider()
    return _provider


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


def safe_persona_name(persona: str) -> str:
    p = (persona or "").strip().lower()
    p = p.replace(" ", "_")
    p = re.sub(r"[^a-z0-9_\-]", "", p)
    return p


def load_persona_role(persona: str) -> Dict[str, str]:
    persona_key = safe_persona_name(persona)
    role_path = ROLES_DIR / f"{persona_key}.txt"

    role_text = read_text_file(role_path)
    if not role_text:
        raise FileNotFoundError(f"Missing persona role file: config/roles/{persona_key}.txt")

    ethos = read_text_file(CONFIG_DIR / "ethos.txt")
    memory_global = read_text_file(CONFIG_DIR / "memory_global.txt")

    return {
        "persona_key": persona_key,
        "role_text": role_text,
        "ethos": ethos,
        "memory_global": memory_global,
    }


def build_system_prompt(persona_payload: Dict[str, str], persona_display: str) -> str:
    parts: List[str] = []

    ethos = persona_payload.get("ethos", "").strip()
    if ethos:
        parts.append(ethos)

    memory_global = persona_payload.get("memory_global", "").strip()
    if memory_global:
        parts.append("GLOBAL MEMORY (read-only):\n" + memory_global)

    role_text = persona_payload.get("role_text", "").strip()
    parts.append(f"PERSONA: {persona_display}\n{role_text}")

    parts.append(
        "OUTPUT RULES:\n"
        "- Reply in 1–2 lines unless the user spoke for a long time or asks for more.\n"
        "- High energy, natural, not corporate.\n"
        "- No disclaimers, no policy talk, no 'as an AI' language.\n"
        "- Do not repeat the user verbatim; respond to them.\n"
    )

    return "\n\n".join([p for p in parts if p])


def auth_ok(req) -> bool:
    # existing shared secret env var
    expected = os.getenv("GATEWAY_SHARED_SECRET", "").strip()
    if not expected:
        return False
    got = (req.headers.get("X-JustTalking-Secret") or "").strip()
    return bool(got) and got == expected


@app.get("/health")
def health() -> Any:
    return jsonify({"ok": True})


@app.post("/message")
def message() -> Any:
    if not auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    persona = (data.get("persona") or "").strip()
    text = (data.get("text") or "").strip()

    if not persona or not text:
        return jsonify({"error": "missing persona or text"}), 400

    history = data.get("history")
    if history is not None and not isinstance(history, list):
        return jsonify({"error": "history must be a list"}), 400

    try:
        persona_payload = load_persona_role(persona)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    system_prompt = build_system_prompt(persona_payload, persona_display=persona)

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if isinstance(history, list):
        for m in history:
            if not isinstance(m, dict):
                continue
            role = (m.get("role") or "").strip()
            content = (m.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": text})

    try:
        provider = get_provider()
        out = provider.chat(messages)
        reply = (out.get("text") or "").strip()
        if not reply:
            return jsonify({"error": "empty model reply"}), 502

        return jsonify(
            {
                "persona": persona,
                "reply": reply,
                "model": out.get("model"),
            }
        )
    except Exception as e:
        return jsonify({"error": f"provider_error: {type(e).__name__}: {e}"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)
