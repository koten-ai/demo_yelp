# LocalAI (Yelp Demo)

Vite + React SPA for local business discovery. Home, Explore, Ask AI, and business details all read the bundled sample catalog in `frontend/src/data/catalog.json` (100 businesses; the first is Trend Eye Care). Photos are static files under `frontend/public/business-images`.

Running the UI needs Node.js only. It does not use a Zeus engine, an LLM key, or the FastAPI service in `src/local_guide`.

## Features

- Keyword search over the sample catalog (name, categories, city, address, description), ranked with rating and review count
- Business cards (rating, categories, price, hours, open/closed) and a Leaflet map on Explore
- Explore filters for open now, price (`$`–`$$$$`), and category
- Ask AI keeps a multi-turn chat. A follow-up that says “which”, “those”, “these”, “them”, “narrow”, or “only” searches inside the previous turn’s results. A query containing “open” keeps places marked open
- Ask AI **AI summary** switch: on writes a short summary above the cards; off shows the matching places only
- Business page with a photo carousel, three generated review blurbs, and a generated good / bad / best-for summary
- Header count comes from the catalog (`100 businesses`)

Search, suggestions, reviews, and insights are implemented in `frontend/src/api/client.ts`. The SearchBar can debounce a local typeahead (`enableSuggest`), and no page turns that on.

## Prerequisites

- Node.js 20+

## Quick start

```bash
cd demo_yelp/frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite server does not proxy `/api` or `/static`.

Production build:

```bash
cd demo_yelp/frontend
npm run build   # output in frontend/dist
npm run preview
```

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

nginx still proxies `/api/` and `/static/` to `BACKEND_UPSTREAM`. The current SPA never requests those paths.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_UPSTREAM` | `http://backend:5000` | nginx `proxy_pass` target (no trailing slash) |
| `NGINX_ENVSUBST_FILTER` | `BACKEND_` | Limit envsubst to backend knobs |

`docker-compose.yml` also starts the Python API on host port **5000** and the nginx UI on host port **3000**. That API container is unused by this UI. Compose still expects `config.json` and a sibling `../zeus_client_python` checkout because the backend image installs `kotenai-zeus-client`. The optional `dev` profile runs Vite on **5173** with `VITE_API_PROXY` set; the dev server ignores that variable and still serves the local catalog.

```bash
# UI image only — see docker build above.

# Full compose stack (Zeus API + nginx UI)
cp config.example.json config.json   # fill keys if you want the API process to start
DOCKER_BUILDKIT=1 docker compose up --build
```

- nginx UI: http://localhost:3000
- API (unused by the SPA): http://localhost:5000
- Vite profile `dev`: http://localhost:5173

## Project layout

```text
demo_yelp/
├── frontend/                 # React SPA, catalog, and photos
│   ├── src/data/catalog.json
│   ├── src/api/client.ts     # in-browser search, reviews, insight
│   └── public/business-images/
├── src/local_guide/          # FastAPI + Zeus client (not called by the SPA)
├── scripts/                  # image upload / finalize helpers
├── docker/                   # nginx template for Dockerfile.frontend
├── Dockerfile.frontend
├── Dockerfile.backend
├── tests/                    # Python API tests
├── config.example.json
└── docker-compose.yml
```

## Python API (not called by the SPA)

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

There is no chat-trace panel in the SPA. `scripts/vendor_trace.sh` is an obsolete stub and exits with an error. The vendored `zeus_client_chat_trace.js` bundle is not in `src/local_guide/static/`.

To run the API anyway:

```bash
cd demo_yelp
cp config.example.json config.json
# edit config.json: llm_provider.api_key, zeus url/password
python3 -m venv .venv && source .venv/bin/activate
pip install -e ../zeus_client_python
pip install -e ".[dev]" --no-deps
python -m local_guide    # http://localhost:5000
```

| Setting | Description |
|---------|-------------|
| `zeus.url` | Zeus base URL (`ZEUS_URL` overrides). `config.example.json` uses `http://host.docker.internal:8080` |
| `zeus.scope_credentials["yelp-demo/_default"]` | Basic auth for the sample scope |
| `default_mode` | `analytics` in `config.example.json` |
| `default_sample` | `yelp-demo` |
| `llm_provider.api_key` | Required for agent turns |

```bash
pytest -q
```

| Symptom | Fix |
|---------|-----|
| `no Zeus URL configured` | Set `zeus.url` or `ZEUS_URL` |
| `llm_provider has no api_key` | Edit `config.json` |
| Docker API cannot reach Zeus | Use `host.docker.internal` |
| SPA has no photos | Files belong under `frontend/public/business-images/biz:<id>/{1,2,3}.png` |
