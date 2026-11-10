# LocalAI (Yelp Demo)

Vite + React SPA for local business discovery. Home and Explore post `POST /api/search`, which loads the live Zeus catalog and runs one agent turn. Business details still read the bundled sample catalog in `frontend/src/data/catalog.json` (100 businesses; the first is Trend Eye Care). Photos are static files under `frontend/public/business-images`. Ask AI posts the same search route with insight synthesis.

Home, Explore, and Ask AI need the API process, a Zeus URL, and `LLM_API_KEY`.

## Features

- Home and Explore search the live Zeus catalog through `POST /api/search`
- Business cards (rating, categories, price, hours, open/closed) and a Leaflet map on Explore
- Explore filters for open now, price (`$`–`$$$$`), and category
- Ask AI keeps a multi-turn chat. A follow-up that says “which”, “those”, “these”, “them”, “narrow”, or “only” searches inside the previous turn’s results. A query containing “open” keeps places marked open
- Ask AI **AI summary** switch: on writes a short summary above the cards; off shows the matching places only
- Business page with a photo carousel, three generated review blurbs, and a generated good / bad / best-for summary
- Header count is the number of `Business` documents in the database

Home and Explore search goes through `frontend/src/api/client.ts` to `POST /api/search`. Suggestions, reviews, and insights in that file still use the sample catalog. The SearchBar can debounce a local typeahead (`enableSuggest`), and no page turns that on.

## Prerequisites

- Docker with BuildKit
- Sibling checkout `../zeus_client_python` (the Compose backend build context is the parent directory)
- `config.json` in this directory as a file
- A `.env` file with `LLM_API_KEY` and `ZEUS_PASSWORD`

## Quick start

Reload, the frontend rebuild, and the Vite dev profile are in [`AGENTS.md`](AGENTS.md).

```bash
cd demo_yelp
[ -f .env ] || cp .env.example .env   # leaves an existing .env in place
# set LLM_API_KEY and ZEUS_PASSWORD in .env when the file is new
DOCKER_BUILDKIT=1 docker compose up -d --build
```

- nginx UI: http://localhost:3000
- API: http://localhost:5000

`docker compose logs -f` follows the containers.

## Example queries

These match businesses in the 100-row catalog (Coffee & Tea, parks, Philadelphia, Tampa, and similar).

1. `coffee in Philadelphia`
2. `italian dinner`
3. `parks in Tampa`
4. On Ask AI, follow up with `which of these are open?`

## Catalog and photos

`frontend/src/data/catalog.json` is an array of business cards. Fields include `business_id`, `name`, `categories`, `rating`, `review_count`, `price`, `hours_today`, `is_open`, `address`, `city`, `state`, `latitude`, `longitude`, `description`, `image`, and `images`.

Photos live next to the SPA and are copied into the Vite build:

```text
frontend/public/business-images/
  manifest.json
  biz:<business_id>/
    1.png
    2.png
    3.png
```

Catalog image fields are relative (`/business-images/biz:<id>/1.png`). Vite and the nginx image serve `public/` at the site root, so those URLs resolve with no API.

`scripts/upload_business_images_spaces.sh` can copy that tree to the DigitalOcean Space `koten-yelp-demo-photos`. `scripts/finalize_business_images.py` rebuilds `manifest.json` and can stamp Couchbase. Neither script changes what the SPA loads. The catalog keeps the relative paths above.

| Variable | Purpose |
|----------|---------|
| `DO_SPACES_KEY` / `DO_SPACES_SECRET` | Required by the upload script |
| `DO_SPACES_PHOTOS_BUCKET` | Default `koten-yelp-demo-photos` |
| `DO_SPACES_PHOTOS_REGION` | Default `nyc3` |
| `BUSINESS_IMAGES_BASE_URL` | Optional absolute prefix (no trailing slash) passed to finalize when rewriting the manifest |
| `FINALIZE_SKIP_COUCHBASE` | `1` to rebuild the manifest only |

## Docker

`Dockerfile.frontend` builds the SPA and serves it with nginx, including `business-images` from `frontend/public`.

```bash
cd demo_yelp
docker build -f Dockerfile.frontend -t local-guide-frontend .
```

nginx still proxies `/api/` and `/static/` to `BACKEND_UPSTREAM`. Home, Explore, and Ask AI post `/api/search` through that proxy. Business detail does not.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_UPSTREAM` | `http://backend:5000` | nginx `proxy_pass` target (no trailing slash) |
| `NGINX_ENVSUBST_FILTER` | `BACKEND_` | Limit envsubst to backend knobs |

Compose start, API reload, and the Vite dev profile are in [`AGENTS.md`](AGENTS.md).

## Project layout

```text
demo_yelp/
├── AGENTS.md                 # coding agents run the app with Docker Compose
├── frontend/                 # React SPA, catalog, and photos
│   ├── src/data/catalog.json
│   ├── src/api/client.ts     # Zeus search, sample reviews, insight
│   └── public/business-images/
├── src/local_guide/          # FastAPI + Zeus client (Home, Explore, Ask AI)
├── scripts/                  # image upload / finalize helpers
├── docker/                   # nginx template for Dockerfile.frontend
├── Dockerfile.frontend
├── Dockerfile.backend
├── tests/                    # Python API tests
├── .env.example              # copy to .env; secret lines stay empty
├── config.json               # secret-free sentinels (no API key)
└── docker-compose.yml
```

## Python API

`src/local_guide` is still a FastAPI app over the Couchbase `yelp-demo` bucket via [`kotenai-zeus-client`](../zeus_client_python) (`run_agent`, `run_search`, `run_verb` / `run_find`). `pyproject.toml` depends on the sibling checkout `file:../zeus_client_python`. The Docker release target still installs git tag `0.3.0-alpha` until a `0.3.1` tag exists. `pytest` covers this package, not the SPA.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/search` | One agent turn `{query, chat_id?, ai_process_result?}` |
| GET | `/api/suggest?q=&limit=` | No-LLM typeahead (`run_search`) |
| GET | `/api/tool-order` | Trace panel tool axes |
| GET | `/api/health` | Liveness, `zeus_client_version`, corpus size |
| GET | `/api/business/{id}` | Detail via V2 `find` |
| GET | `/api/business/{id}/reviews` | Reviews via V2 `find` |
| POST | `/api/business/{id}/insight` | AI review summary |

Home, Explore, and Ask AI call the agent. Open the SPA with `?debug=true` (`1`, `yes`, and `on` count too). That loads `zeus_client_chat_trace/latest` from the CDN. The lightning toggle is bottom-left. Hub for that panel is `http://zeus-dev.local:9091`, not public Zeus `:8080`. A truthy debug flag on `POST /api/search` sets rewind for that turn only and the chat page mounts one Turn traces card. Home and Explore use the live Zeus catalog and do not mount a trace card. Suggest and business detail stay on the local catalog.

The script URL is `https://koten-static-cdn.nyc3.cdn.digitaloceanspaces.com/zeus_client_chat_trace/latest/zeus_client_chat_trace.js`. `scripts/vendor_trace.sh` is an obsolete stub and exits with an error. The bundle is not vendored into `src/local_guide/static/`.

`config.json` is committed and secret-free. Copy `.env.example` to `.env` when `.env` is absent (`[ -f .env ] || cp .env.example .env`), then set `LLM_API_KEY` and `ZEUS_PASSWORD`. An existing `.env` stays as it is. Do not put the API key or the Zeus password in `config.json`. The file stores env **names** (`zeus.password_env` = `ZEUS_PASSWORD`, `llm.api_key_env` = `LLM_API_KEY`) and sentinels (`zeus.auth_mode` = `ZEUS_AUTH_MODE`, `zeus.username` = `ZEUS_USERNAME`, `settings.mode` = `ZEUS_MODE`, `llm.base_url` = `LLM_BASE_URL`, `llm.model` = `LLM_MODEL`). The data target is `yelp-demo` / `_default` / `_default`.

| Name | Description |
|------|-------------|
| `ZEUS_URL` | Zeus base URL. Compose sets `http://host.docker.internal:8080`, which wins over `.env` |
| `ZEUS_AUTH_MODE` | `basic` or `bearer`. Replaces the `ZEUS_AUTH_MODE` sentinel when `ZEUS_URL` is set |
| `ZEUS_USERNAME` | Basic auth user (`demo_1` in `.env.example`) |
| `ZEUS_PASSWORD` | Basic auth password. Only the name `ZEUS_PASSWORD` is stored in `config.json` |
| `ZEUS_BUCKET` / `ZEUS_SCOPE` / `ZEUS_COLLECTION` | `yelp-demo` / `_default` / `_default` |
| `ZEUS_MODE` | Agent mode. Replaces the `ZEUS_MODE` sentinel. `.env.example` uses `analytics` |
| `LLM_BASE_URL` | Replaces the `LLM_BASE_URL` sentinel (`https://api.x.ai/v1` in `.env.example`) |
| `LLM_MODEL` | Replaces the `LLM_MODEL` sentinel (`grok-4.5-latest` in `.env.example`) |
| `LLM_API_KEY` | Required for agent turns. Set it in `.env`, not in `config.json` |
| `COUCHBASE_QUERY_URL` / `COUCHBASE_USERNAME` / `COUCHBASE_PASSWORD` | N1QL hydrate for suggest and business detail |

| Symptom | Fix |
|---------|-----|
| `no Zeus URL configured` | Set `ZEUS_URL` |
| `LLM_API_KEY is not set` | Set `LLM_API_KEY` in `.env` |
| Docker API cannot reach Zeus | Use `host.docker.internal` |
| SPA has no photos | Files belong under `frontend/public/business-images/biz:<id>/{1,2,3}.png` |

## Host processes

Use these when Compose is not the process under test. `pytest` stays here: the API image does not install pytest, and Compose does not mount `tests/`.

```bash
cd demo_yelp
[ -f .env ] || cp .env.example .env
# set LLM_API_KEY and ZEUS_PASSWORD in .env when the file is new
python3 -m venv .venv && source .venv/bin/activate
pip install -e ../zeus_client_python
pip install -e ".[dev]" --no-deps
pytest -q
```

```bash
cd demo_yelp
source .venv/bin/activate
python -m local_guide    # http://localhost:5000
```

Host SPA (Node.js 20+). Vite proxies `/api` and `/static` to `VITE_API_PROXY`, or to `http://127.0.0.1:5000` when that variable is unset.

```bash
cd demo_yelp/frontend
npm install
npm run dev       # http://localhost:5173
```

```bash
cd demo_yelp/frontend
npm run build     # output in frontend/dist
npm run preview
```
