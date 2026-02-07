import os
import time
from pathlib import Path
from flask import Flask, request, jsonify

from providers import run_model

app = Flask(__name__)

def now():
    return int(time.time())

@app.get("/health")
def health():
    return jsonify(ok=True, ts=now())

@app.post("/message")
def message():
    # auth
    expected = os.getenv("GATEWAY_SHARED_SECRET", "")
    provided = request.headers.get("X-JustTalking-Secret", "")

    if not expected or provided != expected:
        return jsonify(ok=False, error="unauthorized", ts=now()), 401

    # input
    data = request.get_json(silent=True) or {}
    persona = (data.get("persona") or "unknown").strip()
    text = (data.get("text") or "").strip()

    # load role contract (persona file)
    role_path = Path(f"config/roles/{persona}.txt")
    if role_path.exists():
        system_prompt = role_path.read_text(encoding="utf-8").strip()
    else:
        system_prompt = f"You are {persona}. Keep replies short."

    # generate reply (high creativity, short)
    reply_text = run_model(
        system_prompt=system_prompt,
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
