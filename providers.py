import os
from typing import List, Dict, Any

from openai import OpenAI


class XAIProvider:
    """
    xAI (Grok) via OpenAI-compatible API.
    Uses env vars:
      - XAI_API_KEY
      - XAI_BASE_URL (default https://api.x.ai/v1)
      - JT_MODEL (default grok-4-1-fast-non-reasoning)
      - JT_TEMPERATURE, JT_MAX_TOKENS, JT_TOP_P,
        JT_PRESENCE_PENALTY, JT_FREQUENCY_PENALTY (optional)
    """

    def __init__(self) -> None:
        api_key = os.getenv("XAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Missing XAI_API_KEY")

        base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1").strip()

        # OpenAI client pointed at xAI
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self.model = os.getenv("JT_MODEL", "grok-4-1-fast-non-reasoning").strip()

        # Style defaults – you can tweak later
        self.temperature = float(os.getenv("JT_TEMPERATURE", "1.1"))
        self.max_tokens = int(os.getenv("JT_MAX_TOKENS", "120"))
        self.top_p = float(os.getenv("JT_TOP_P", "0.95"))
        self.presence_penalty = float(os.getenv("JT_PRESENCE_PENALTY", "0.3"))
        self.frequency_penalty = float(os.getenv("JT_FREQUENCY_PENALTY", "0.15"))

    def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
        )

        choice = resp.choices[0]
        text = (choice.message.content or "").strip()

        return {
            "text": text,
            "model": getattr(resp, "model", self.model),
            "usage": getattr(resp, "usage", None),
        }
