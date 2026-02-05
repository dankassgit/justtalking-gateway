JustTalking — Google Gateway v2 (20-role config)

Edit only:
- config/roles/*.txt (20 role files)
- config/variant_map.json (40 contacts: ids + voices + style + preview URLs)
- config/routing.json (default Claude Sonnet 4.5; Flirt/Hot Mess -> Grok)

Set env vars in Cloud Run:
- DEFAULT_MODEL=claude-sonnet-4-5
- GROK_MODEL=grok-4
- ANTHROPIC_API_KEY=...
- XAI_API_KEY=...

Endpoints:
- GET /health
- POST /v1/turn { "persona_id":"flirt_female", "text":"hello", "first_name":"Dan" }
