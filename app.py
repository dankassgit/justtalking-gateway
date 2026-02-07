import os
import time
from flask import Flask, request, jsonify

from providers import generate_reply

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROLES_DIR = os.path.join(BASE_DIR, "config", "roles")

app = Flask(__name__)

def now():
    return int(time.time())

def load_role(persona: str) -> str:
    persona = (persona or "flirt").strip().lower()
    path = os.path.join(ROLES_DIR, f"{persona}.txt")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

@app.get("/health")
def health():
    return jsonify(ok=True, ts=now())

@app.post("/message")
def message():
    expected = os.getenv("GATEWAY_SHARED_SECRET", "")
    provided = request.headers.get("X-JustTalking-Secret", "")

    if not expected or provided != expected:
        return jsonify(ok=False, error="unauthorized", ts=now()), 401

    data = request.get_json(silent=True) or {}
    persona = (data.get("persona") or "flirt").strip().lower()
    text = (data.get("text") or "").strip()

    role_text = load_role(persona)
    if not role_text:
        role_text = f"You are {persona}. Keep replies very short."

    reply_text = generate_reply(
        role_text=role_text,
        user_text=text,
        temperature=1.0,
        max_tokens=120
    )

    return jsonify(
        ok=True,
        ts=now(),
        persona=persona,
        received=text,
        reply=reply_text
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
