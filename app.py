import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify
import providers

app = Flask(__name__)

CONFIG_DIR = os.getenv("JT_CONFIG_DIR", "config")

def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def read_text(rel_path: str) -> str:
    path = os.path.join(CONFIG_DIR, rel_path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def read_json(rel_path: str) -> Dict[str, Any]:
    path = os.path.join(CONFIG_DIR, rel_path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def resolve_model_name(model_env: str) -> str:
    return os.getenv(model_env, "") or model_env

def split_persona_id(persona_id: str) -> Tuple[str, str]:
    if "_" not in persona_id:
        return persona_id, ""
    role_id, variant = persona_id.rsplit("_", 1)
    return role_id, variant

def load_contact(persona_id: str) -> Dict[str, Any]:
    vm = read_json("variant_map.json")
    for c in vm.get("contacts", []):
        if c.get("persona_id") == persona_id:
            return c
    return {}

def choose_route(role_id: str) -> Dict[str, str]:
    routing = read_json("routing.json")
    if role_id in routing.get("role_overrides", {}):
        return routing["role_overrides"][role_id]
    return routing["default"]

@app.get("/health")
def health():
    return jsonify({"ok": True, "ts": utc_now()})

@app.post("/v1/turn")
def turn():
    payload = request.get_json(force=True, silent=True) or {}
    persona_id = (payload.get("persona_id") or "").strip()
    user_text = (payload.get("text") or "").strip()
    first_name = (payload.get("first_name") or "").strip()

    if not persona_id:
        return jsonify({"error": "persona_id required"}), 400
    if not user_text:
        return jsonify({"error": "text required"}), 400

    role_id, variant = split_persona_id(persona_id)

    ethos = read_text("ethos.txt")
    mem_global = read_text("memory_global.txt")
    role_contract = read_text(f"roles/{role_id}.txt")

    contact = load_contact(persona_id)
    voice = (contact.get("voice") or {}) if contact else {}
    voice_id = voice.get("voice_id", "")
    voice_style = voice.get("style", {}) if isinstance(voice.get("style", {}), dict) else {}
    preview_voice_url = voice.get("preview_voice_url", "")

    system_parts = [p for p in [ethos, mem_global, role_contract] if p]
    system_text = "\n\n".join(system_parts)

    if first_name:
        system_text += f"\n\nUser first name: {first_name}. Use it occasionally, not constantly."

    if voice_id or voice_style:
        system_text += "\n\nVoice delivery settings:"
        if voice_id:
            system_text += f"\n- voice_id: {voice_id}"
        for k, v in (voice_style or {}).items():
            system_text += f"\n- {k}: {v}"

    route = choose_route(role_id)
    provider_name = route.get("provider", "anthropic_messages")
    model_used = resolve_model_name(route.get("model_env", "DEFAULT_MODEL"))

    try:
        if provider_name == "anthropic_messages":
            reply_text = providers.call_anthropic_messages(
                model=model_used, system_text=system_text, user_text=user_text
            )
        elif provider_name == "xai_chat_completions":
            reply_text = providers.call_xai_chat_completions(
                model=model_used, system_text=system_text, user_text=user_text
            )
        else:
            return jsonify({"error": f"Unknown provider: {provider_name}"}), 500
    except Exception as e:
        print(json.dumps({
            "ts": utc_now(),
            "event": "error",
            "persona_id": persona_id,
            "role_id": role_id,
            "provider": provider_name,
            "model_used": model_used,
            "message": str(e),
        }))
        return jsonify({
            "error": "Gateway could not complete the request.",
            "persona_id": persona_id,
            "provider": provider_name,
            "model_used": model_used,
            "ts": utc_now(),
        }), 502

    print(json.dumps({
        "ts": utc_now(),
        "event": "turn",
        "persona_id": persona_id,
        "role_id": role_id,
        "provider": provider_name,
        "model_used": model_used,
    }))

    return jsonify({
        "reply_text": reply_text,
        "persona_id": persona_id,
        "role_id": role_id,
        "variant": variant,
        "provider": provider_name,
        "model_used": model_used,
        "voice_id": voice_id,
        "voice_style": voice_style,
        "preview_voice_url": preview_voice_url,
        "ts": utc_now(),
    })
