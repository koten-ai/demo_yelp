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

Images are split for staging/production reuse:

| File | Image role |
|------|------------|
| `Dockerfile.backend` | FastAPI + Zeus client (build context: monorepo parent) |
| `Dockerfile.frontend` | Vite build + nginx SPA; proxies `/api` + `/static` → API |

```bash
cd demo_yelp
cp config.example.json config.json   # fill keys

# Local stack (API :5000, nginx UI :3000)
docker compose up --build

# Optional Vite HMR on :5173
docker compose --profile dev up --build
```

- UI (nginx / staging-shaped): http://localhost:3000  
- API direct: http://localhost:5000  
- Vite dev (profile `dev`): http://localhost:5173  

(Compose maps nginx to host **3000** so it does not collide with a local Zeus engine on 8080.)

### Build images alone (CI / staging / prod)

```bash
# From monorepo parent (koten-ai/)
docker build -f demo_yelp/Dockerfile.backend -t local-guide-backend:TAG .

# From this directory
docker build -f Dockerfile.frontend -t local-guide-frontend:TAG .
```

Frontend runtime env:

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_UPSTREAM` | `http://backend:5000` | nginx `proxy_pass` target (no trailing slash; use your staging service DNS in other envs) |
| `NGINX_ENVSUBST_FILTER` | `BACKEND_` | limit envsubst to backend knobs |

Same-origin via nginx means the browser talks only to the frontend origin; CORS is mainly for Vite/local API access.

### Why two Dockerfiles (not one entrypoint)

- Independent tags/rollouts for API vs UI  
- Smaller backend image (no Node toolchain at runtime)  
- Edge can be nginx, Cloud Run+CDN, or ingress — same backend image  
- Local HMR stays a Compose profile (`frontend-dev`), not baked into prod images  

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
├── docker/              # nginx template for Dockerfile.frontend
├── Dockerfile.backend
├── Dockerfile.frontend
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
