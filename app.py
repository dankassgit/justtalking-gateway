import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROLES_DIR = os.path.join(BASE_DIR, "config", "roles")

def now():
    return int(time.time())

def load_role(persona):
    try:
        path = os.path.join(ROLES_DIR, f"{persona}.txt")
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None

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
    persona = data.get("persona", "flirt")
    text = data.get("text", "")

    role_text = load_role(persona)

    if not role_text:
        reply = f"[{persona}] heard you."
    else:
        # TEMP placeholder — proves file is being read
        reply = role_text.splitlines()[0]

    return jsonify(
        ok=True,
        ts=now(),
        persona=persona,
        received=text,
        reply=reply
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
