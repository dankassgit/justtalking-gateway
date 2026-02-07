import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_reply(role_text, user_text):
    response = client.messages.create(
        model=os.getenv("DEFAULT_MODEL", "claude-sonnet-4.5"),
        max_tokens=120,
        temperature=1.0,
        system=role_text,
        messages=[
            {"role": "user", "content": user_text}
        ],
    )

    return response.content[0].text.strip()
