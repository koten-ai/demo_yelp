# LocalAI (Yelp Demo)

Natural-language local business discovery over the Couchbase **`yelp-demo`** bucket, powered by [Zeus](https://github.com/koten-ai) and [`kotenai-zeus-client`](../zeus_client_python) (`run_agent`). React SPA UI follows Stitch designs in `../stitch_ai_local_guide/`.

## Features

- NL search + multi-turn chat against `yelp-demo/_default/_default`
- Business cards (rating, categories, price, geo) + Leaflet map
- Business detail with AI review insight (good / bad / best-for)
- Floating Zeus chat-trace panel (vendored JS)
- FastAPI backend tailored to the SPA; Vite React frontend

## Prerequisites

- Zeus Engine reachable with **yelp-demo** scope loaded/enabled
- LLM API key (xAI Grok by default)
- Python 3.11+ and Node 20+ (or Docker)

## Quick start (local)

```bash
# Backend
cd demo_yelp
cp config.example.json config.json
# edit config.json: llm_provider.api_key, zeus url/password
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m local_guide
```

```bash
# Frontend (separate terminal)
cd demo_yelp/frontend
npm install
npm run dev
```

Open http://localhost:5173 (proxies `/api` and `/static` to port 5000).

## Docker

From monorepo parent (`koten-ai/`):

```bash
cd demo_yelp
cp config.example.json config.json   # fill keys
docker compose up --build
```

App: http://localhost:5000 (API + built SPA).

## Configuration

| Setting | Description |
|---------|-------------|
| `zeus.url` | Zeus base URL (`ZEUS_URL` overrides) |
| `zeus.scope_credentials["yelp-demo/_default"]` | Basic auth for the sample scope |
| `default_mode` | Agent mode (`open` default) |
| `default_sample` | `yelp-demo` |
| `llm_provider.api_key` | Required |

## API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/search` | One agent turn `{query, chat_id?}` |
| GET | `/api/tool-order` | Trace panel tool axes |
| GET | `/api/health` | Liveness |
| GET | `/api/business/{id}` | Detail seed |
| POST | `/api/business/{id}/insight` | AI review summary |

Success search payload matches the Demo Builder kit contract (answer, results, trace, chat_id, session fields, …) with Yelp-oriented card fields.

## Example queries

1. `quiet coffee shops good for deep work`
2. `romantic italian dinner under $$$`
3. `dog-friendly parks or outdoor brunch`
4. Follow-up: `which of these are open late?`

## Development

```bash
pytest -q
cd frontend && npm run build
```

## Project layout

```
demo_yelp/
├── src/local_guide/     # FastAPI + agent wrapper
├── frontend/            # React SPA
├── tests/
├── config.example.json
└── docker-compose.yml
```

Built with the [Demo Builder Kit](../zeus_client_python/docs/demo-builder/). Reference: `../demo_travel_sample`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `no Zeus URL configured` | Set `zeus.url` or `ZEUS_URL` |
| `llm_provider has no api_key` | Edit `config.json` |
| Empty cards | Check Zeus data + mode catalog sync |
| Docker cannot reach Zeus | Use `host.docker.internal` |
| No photos | Academic Yelp dump often has none; placeholders are expected |
