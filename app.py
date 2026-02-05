import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

def now():
    return int(time.time())

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
    persona = data.get("persona", "unknown")
    text = data.get("text", "")

    return jsonify(
        ok=True,
        ts=now(),
        persona=persona,
        received=text,
        reply=f"[{persona}] heard you."
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
