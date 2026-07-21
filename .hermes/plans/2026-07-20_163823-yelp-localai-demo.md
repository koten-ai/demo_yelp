# LocalAI (Yelp Demo) Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a productized local-business discovery demo (LocalAI) that uses `kotenai-zeus-client` (`../zeus_client_python`) against Couchbase bucket `yelp-demo`, with a React SPA UI matching `../stitch_ai_local_guide/`, and a backend API tailored to that UI.

**Architecture:** Monorepo app under `demo_yelp/`: FastAPI backend owns config bootstrap, `run_agent`, chat store, result mappers, and SPA static serving; React (Vite) SPA implements Stitch screens (landing, search results + map, conversational search, business details) and embeds vendored `zeus_client_chat_trace.js`. Backend follows Demo Builder Kit phases; UI follows TravelPlan API contract plus Yelp-specific card/detail fields.

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, uvicorn, httpx, `kotenai-zeus-client @ file:../zeus_client_python`
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS (Stitch / Vivid Logic tokens)
- Data: Zeus Engine → `yelp-demo/_default/_default` (Yelp academic dataset: business, review, tip, checkin, user)
- Trace: vendored `zeus_client_chat_trace` bundle
- Deploy: Docker Compose (backend serves built SPA; CORS for local Vite dev)

**Primary references (do not invent parallel agent frameworks):**
- Demo Builder Kit: `../zeus_client_python/docs/demo-builder/` (`BUILDING_A_DEMO.md`, `AGENTS.md`, `RECIPES.md`, `API_CONTRACT.md`, `UI_CONTRACT.md`, `TRACE_PANEL.md`, `DOMAIN_CUSTOMIZATION.md`, `ACCEPTANCE.md`, `templates/`)
- Reference app: `../demo_travel_sample/src/travel_planner/`
- UI design: `../stitch_ai_local_guide/` + `vivid_logic/DESIGN.md`
- Trace widget: `../zeus_client_chat_trace/`
- Data load notes: `../Zeus/yelp-demo.txt`

---

## Current context / assumptions

| Item | Value |
|------|--------|
| Workspace | `/home/michael/koten-ai/demo_yelp` (empty git repo today) |
| Zeus client | Sibling path `../zeus_client_python` (package name `kotenai-zeus-client`) |
| Sample keyspace | `yelp-demo` / `_default` / `_default` |
| Auth | Same pattern as TravelPlan: basic per-scope (`zeus.scope_credentials["yelp-demo/_default"]`) |
| Agent mode | Start with `open` (domain-agnostic V2 catalog); sync catalogs on startup. Prefer `analytics` only if operator confirms it is enabled on the scope |
| LLM | xAI Grok via `llm_provider` in `config.json` (never commit keys) |
| UI brand | LocalAI — indigo/teal Vivid Logic; Inter + JetBrains Mono; Material Symbols |
| Yelp docs | Keys like `biz:yelp:%business_id%`, `rev:yelp:%review_id%`; fields typically include `name`, `stars`, `review_count`, `categories`, `address`/`city`/`state`, `latitude`/`longitude`, `hours`, `is_open`, `attributes` (price), `type`, plus related Review docs |
| Images | Yelp academic dump usually has **no** photo URLs → always support empty `image` + client placeholder |
| Non-goals (YAGNI v1) | Real OAuth login, write reviews, live GPS backend geocoding service, CDN-only trace, inventing Zeus HTTP paths outside the client library |

---

## Proposed approach

### Backend (FastAPI, kit-aligned)

Copy TravelPlan module responsibilities, adapted for async FastAPI lifespan (recipe R02b) instead of Flask + background loop:

| Module | Role |
|--------|------|
| `zeus_config.py` | Set `ZEUS_CLIENT_CONFIG_DIR`, `ZEUS_CHAT_REQUESTS_DIR`, `CHAT_LOG_PATH` **before** any `import zeus_client` |
| `app.py` | FastAPI app, CORS, routes, optional SPA mount |
| `search.py` | Domain `run_agent` wrapper + multi-turn chat_id |
| `output_schema.py` | Allowlist fields for Business / Review (and generic fallbacks) |
| `results_parser.py` | Waterfall: `zeus_data` → trace → markdown fallback → business cards |
| `answer_parser.py` | Markdown/JSON answer → structured fallback (reuse TravelPlan patterns) |
| `chat_store.py` | In-memory + JSONL multi-turn + `zeus_session_id` / `zeus_round` |
| `detail.py` | Optional business detail assembly for detail route |
| `static/` | Vendored `zeus_client_chat_trace.js` (+ map) for SPA to load |

Hard rules from kit:
1. Env before `import zeus_client`
2. Real Zeus + real LLM
3. Prefer library APIs: `run_agent`, `load_config`, `resolve_*`, `sync_chat_requests`, `build_tool_order`
4. App owns chat store; pass durable session fields
5. `output_schema` for cards — never dump full docs to UI
6. Vendor chat-trace JS
7. No secrets in git

### Frontend (React SPA from Stitch)

Four routes mapped to Stitch HTML:

| Route | Stitch source | Purpose |
|-------|---------------|---------|
| `/` | `localai_visual_search_ui` | Hero NL search + AI recommended strip |
| `/search` | `localai_search_results` | Results list, filters, AI area summary, map pane |
| `/chat` | `localai_conversational_search` | Multi-turn discovery chat + inline business chips |
| `/business/:id` | `localai_business_details` | Profile, AI review summary, reviews list |

Design system from `vivid_logic/DESIGN.md` → Tailwind theme extension.

### API surface (backend tailored to UI)

Keep TravelPlan-compatible core so trace widget stays drop-in, then extend for LocalAI:

| Method | Path | UI consumer |
|--------|------|-------------|
| `POST` | `/api/search` | All NL turns (landing, results refine, chat) |
| `GET` | `/api/tool-order` | Trace panel axes |
| `GET` | `/api/health` | Ops / compose healthcheck |
| `GET` | `/api/business/{business_id}` | Detail page seed (structured card + optional recent reviews if present in last turn / light agent get) |
| `POST` | `/api/business/{business_id}/insight` | AI review summary turn (good/bad/best-for) using same chat/session stack |
| `GET` | `/` + assets | Production: serve Vite `dist/` |

**`POST /api/search` success body** — same required keys as Demo Builder `API_CONTRACT.md`, with richer `results[]` items for Yelp:

```json
{
  "chat_id": "yelp_a1b2c3d4e5f6",
  "query": "quiet coffee shops open now for deep work",
  "answer": "…",
  "structured_answer": {},
  "structured_response": {},
  "results": [
    {
      "name": "Lumina Roasters",
      "description": "…",
      "image": "",
      "business_id": "abc123",
      "rating": "4.8",
      "review_count": "1284",
      "categories": "Coffee & Bakery",
      "price": "$$",
      "is_open": "true",
      "hours_today": "Open until 7:00 PM",
      "location": "Philadelphia, PA",
      "address": "…",
      "city": "Philadelphia",
      "state": "PA",
      "latitude": "39.95",
      "longitude": "-75.16",
      "url": ""
    }
  ],
  "trace": {},
  "tool_order": { "v1": [], "v2": [] },
  "target": "yelp-demo/_default/_default",
  "api_version": "v2",
  "mode": "open",
  "model": "…",
  "provider": "xai",
  "zeus_connection": "default",
  "zeus_url": "http://…",
  "session_id": "…",
  "session_round": 1,
  "contract_status": "match"
}
```

Card rules:
- Always emit at least `name`, `description`, `image` (image may be `""`)
- Max 20 results
- Prefer `business_id` / `id` / `doc_key` for detail navigation
- All card values **strings** (TravelPlan convention) except UI may parse numbers client-side

### Domain prompt (search wrapper)

```text
Find local businesses that match these preferences in the yelp-demo knowledge graph.
Use Zeus V2 search, find, get, or pipeline as needed on real data (Business and related Review entities).
Prefer results with name, categories, stars/rating, review_count, address/city/state,
latitude/longitude, hours/is_open, and price attributes when available.
Do not invent businesses missing from Zeus results.
Summarize why each match fits the user intent.

User preferences:
{query}
```

### Result waterfall (R07)

1. `zeus_data_to_results(structured.zeus_data)`
2. else `extract_businesses(trace)`
3. else `structured_answer_to_results(structured_answer)`

### Config sketch (`config.example.json`)

```json
{
  "build_version": "0.1.0",
  "zeus": {
    "url": "http://host.docker.internal:8080",
    "auth_mode": "basic",
    "username": "demo_1",
    "password": "",
    "scope_credentials": {
      "yelp-demo/_default": { "username": "demo_1", "password": "" }
    },
    "scope_contracts": {
      "yelp-demo/_default": {
        "open": { "contract_id": "open_v2", "contract_hash": "" },
        "analytics": { "contract_id": "analytics_v4", "contract_hash": "" }
      }
    },
    "enable_durable_sessions": true
  },
  "llm_provider": {
    "label": "xAI Grok",
    "base_url": "https://api.x.ai/v1",
    "api_key": "",
    "models": ["grok-4-1-fast-non-reasoning", "grok-4-1-fast-reasoning"]
  },
  "chat_requests_sync": {
    "scopes": "from_contracts",
    "modes": ["open", "analytics"],
    "on_startup": true
  },
  "default_api_version": "v2",
  "default_mode": "open",
  "default_sample": "yelp-demo",
  "samples": {
    "yelp-demo": {
      "bucket": "yelp-demo",
      "scope": "_default",
      "collection": "_default"
    }
  }
}
```

---

## Target tree

```text
demo_yelp/
├── src/local_guide/
│   ├── __init__.py              # configure_zeus_client() first
│   ├── __main__.py
│   ├── paths.py
│   ├── zeus_config.py
│   ├── app.py                   # FastAPI factory + routes + SPA
│   ├── search.py
│   ├── detail.py
│   ├── async_lifecycle.py       # lifespan: init_http, sync catalogs, load chats
│   ├── chat_store.py
│   ├── output_schema.py
│   ├── results_parser.py
│   ├── answer_parser.py
│   └── static/
│       ├── zeus_client_chat_trace.js
│       └── zeus_client_chat_trace.js.map   # optional
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css            # Vivid Logic tokens
│       ├── api/client.ts
│       ├── api/types.ts
│       ├── lib/normalize.ts
│       ├── lib/trace.ts
│       ├── components/
│       │   ├── layout/AppShell.tsx
│       │   ├── search/SearchBar.tsx
│       │   ├── search/FilterChips.tsx
│       │   ├── results/BusinessCard.tsx
│       │   ├── results/ResultsList.tsx
│       │   ├── results/AreaSummary.tsx
│       │   ├── map/ResultsMap.tsx
│       │   ├── chat/ChatThread.tsx
│       │   ├── chat/ChatComposer.tsx
│       │   ├── detail/BusinessHero.tsx
│       │   ├── detail/AiReviewSummary.tsx
│       │   ├── detail/ReviewList.tsx
│       │   └── common/{RatingStars,PriceLevel,OpenBadge,EmptyState,ErrorBanner,Loading}.tsx
│       ├── pages/
│       │   ├── LandingPage.tsx
│       │   ├── SearchResultsPage.tsx
│       │   ├── ConversationalSearchPage.tsx
│       │   └── BusinessDetailsPage.tsx
│       └── state/session.ts     # chat_id persistence
├── data/
│   ├── chat_requests/           # synced/bundled catalogs
│   └── .gitkeep
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_results_parser.py
│   ├── test_answer_parser.py
│   ├── test_output_schema.py
│   └── test_search_unit.py
├── scripts/
│   └── vendor_trace.sh
├── config.example.json
├── config.json                  # gitignored
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── .dockerignore
└── README.md
```

---

## Step-by-step plan

### Task 1: Scaffold repo layout + ignore rules

**Objective:** Create empty project skeleton and git hygiene.

**Files:**
- Create: `.gitignore`, `.dockerignore`, `data/.gitkeep`, `src/local_guide/paths.py`
- Create: directory placeholders listed in target tree

**Step 1: Write `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.coverage
htmlcov/
config.json
data/chats.jsonl
data/chat_requests/**
!data/chat_requests/.gitkeep
frontend/node_modules/
frontend/dist/
*.egg-info/
dist/
build/
.env
.DS_Store
```

**Step 2: Add `paths.py`**

```python
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent
```

**Step 3: Commit**

```bash
git add .gitignore .dockerignore data/.gitkeep src/local_guide/paths.py
git commit -m "chore: scaffold demo_yelp layout and ignore rules"
```

---

### Task 2: Packaging — `pyproject.toml` + package init (env-before-import)

**Objective:** Installable backend package wired to sibling Zeus client.

**Files:**
- Create: `pyproject.toml`
- Create: `src/local_guide/__init__.py`
- Create: `src/local_guide/zeus_config.py`
- Create: `src/local_guide/__main__.py`

**Step 1: `pyproject.toml` (from kit template, FastAPI-first)**

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "local-guide"
version = "0.1.0"
description = "LocalAI Yelp discovery demo powered by Zeus + kotenai-zeus-client"
requires-python = ">=3.11"
dependencies = [
    "fastapi==0.115.6",
    "uvicorn[standard]==0.34.0",
    "httpx==0.28.1",
    "python-multipart==0.0.20",
    "kotenai-zeus-client @ file:../zeus_client_python",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0", "pytest-asyncio>=0.24"]

[project.scripts]
local-guide = "local_guide.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
local_guide = ["static/*", "static/**/*"]

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"
markers = [
    "integration: tests that require live Zeus or LLM services",
]
```

**Step 2: `zeus_config.py`**

```python
from __future__ import annotations
import os
from local_guide.paths import PROJECT_ROOT

def configure_zeus_client() -> None:
    """Set env vars BEFORE any zeus_client import (constants read env at import)."""
    os.environ.setdefault("ZEUS_CLIENT_CONFIG_DIR", str(PROJECT_ROOT))
    os.environ.setdefault(
        "ZEUS_CHAT_REQUESTS_DIR",
        str(PROJECT_ROOT / "data" / "chat_requests"),
    )
    os.environ.setdefault("CHAT_LOG_PATH", str(PROJECT_ROOT / "data" / "chats.jsonl"))
```

**Step 3: `__init__.py`**

```python
from local_guide.zeus_config import configure_zeus_client

configure_zeus_client()
__version__ = "0.1.0"
```

**Step 4: `__main__.py`**

```python
import os
import uvicorn

def main() -> None:
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(
        "local_guide.app:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT") == "dev",
    )

if __name__ == "__main__":
    main()
```

**Step 5: Install editable**

```bash
cd /home/michael/koten-ai/demo_yelp
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: install succeeds; `python -c "import local_guide; print(local_guide.__version__)"` → `0.1.0`

**Step 6: Commit**

```bash
git add pyproject.toml src/local_guide/
git commit -m "feat: package local-guide with zeus_client env bootstrap"
```

---

### Task 3: Config example for `yelp-demo`

**Objective:** Operator-ready config template (no secrets).

**Files:**
- Create: `config.example.json` (content in approach section above)
- Ensure `config.json` is gitignored

**Step 1:** Write `config.example.json` exactly as sketch (yelp-demo sample, mode `open`).

**Step 2:** Document operator copy:

```bash
cp config.example.json config.json
# fill llm_provider.api_key, zeus passwords, zeus.url
```

**Step 3: Commit**

```bash
git add config.example.json
git commit -m "feat: add yelp-demo config.example.json"
```

---

### Task 4: Chat store (multi-turn persistence)

**Objective:** Port TravelPlan chat store with yelp chat_id prefix later in search.

**Files:**
- Create: `src/local_guide/chat_store.py`
- Test: `tests/test_chat_store.py` (optional thin) or cover via search tests

**Step 1:** Copy structure from `demo_travel_sample/src/travel_planner/chat_store.py`:
- `CHATS`, `chat_lock`, `persist_chat`, `load_chats_from_jsonl`, `append_chat_event`
- Resolve `CHAT_LOG_PATH` via env / `PROJECT_ROOT / "data" / "chats.jsonl"`

**Step 2: Commit**

```bash
git add src/local_guide/chat_store.py
git commit -m "feat: multi-turn chat store with JSONL persistence"
```

---

### Task 5: `output_schema` for Business + Review (TDD)

**Objective:** Allowlist card/detail fields only.

**Files:**
- Test: `tests/test_output_schema.py`
- Create: `src/local_guide/output_schema.py`

**Step 1: Failing test**

```python
from local_guide.output_schema import DEMO_OUTPUT_SCHEMA

def test_business_schema_has_card_fields():
    biz = set(DEMO_OUTPUT_SCHEMA["Business"])
    for key in ("name", "stars", "review_count", "categories", "city", "latitude", "longitude"):
        assert key in biz

def test_review_schema_has_text_and_stars():
    rev = set(DEMO_OUTPUT_SCHEMA["Review"])
    assert "text" in rev and "stars" in rev
```

**Step 2:** Run `pytest tests/test_output_schema.py -v` → FAIL (module missing).

**Step 3: Implementation**

```python
from __future__ import annotations

_CARD = (
    "id", "doc_key", "entity_type", "business_id",
    "name", "title",
    "description", "summary", "brief", "overview", "snippet", "text",
    "categories", "category",
    "stars", "rating", "review_count", "review_count_str",
    "address", "city", "state", "postal_code", "location",
    "latitude", "longitude", "lat", "lon", "lng",
    "hours", "is_open", "open_now",
    "attributes", "price", "price_range", "RestaurantsPriceRange2",
    "image", "image_url", "photo", "thumbnail",
    "url", "website", "link",
    "type",
)

_REVIEW = (
    "id", "doc_key", "entity_type", "review_id", "business_id", "user_id",
    "stars", "rating", "text", "date",
    "useful", "funny", "cool",
    "name",  # reviewer display if joined
)

DEMO_OUTPUT_SCHEMA: dict[str, list[str]] = {
    "Business": list(_CARD),
    "business": list(_CARD),
    "Review": list(_REVIEW),
    "review": list(_REVIEW),
    # fallbacks if scope brief uses different labels
    "Hotel": list(_CARD),
    "Destination": list(_CARD),
}
```

**Step 4:** `pytest tests/test_output_schema.py -v` → PASS

**Step 5: Commit**

```bash
git add src/local_guide/output_schema.py tests/test_output_schema.py
git commit -m "feat: yelp Business/Review output_schema allowlist"
```

---

### Task 6: Results parser (TDD)

**Objective:** Normalize Zeus rows/traces into LocalAI business cards.

**Files:**
- Test: `tests/test_results_parser.py`
- Create: `src/local_guide/results_parser.py`

**Step 1: Failing tests (examples)**

```python
from local_guide.results_parser import zeus_data_to_results, extract_businesses

def test_zeus_data_maps_yelp_business():
    rows = [{
        "entity_type": "Business",
        "business_id": "b1",
        "name": "Lumina Roasters",
        "stars": 4.8,
        "review_count": 1284,
        "categories": "Coffee & Tea, Bakeries",
        "city": "Philadelphia",
        "state": "PA",
        "address": "123 Main",
        "latitude": 39.95,
        "longitude": -75.16,
        "is_open": 1,
        "attributes": {"RestaurantsPriceRange2": "2"},
    }]
    cards = zeus_data_to_results(rows)
    assert len(cards) == 1
    c = cards[0]
    assert c["name"] == "Lumina Roasters"
    assert c["business_id"] == "b1"
    assert c["rating"] == "4.8"
    assert "description" in c and "image" in c
    assert c["latitude"] == "39.95"
    assert c["price"] in {"2", "$$", "$2"}  # pick one mapping and stick to it

def test_dedupe_by_name_or_id():
    rows = [
        {"name": "A", "business_id": "1"},
        {"name": "A", "business_id": "1"},
    ]
    assert len(zeus_data_to_results(rows)) == 1
```

**Step 2:** Implement mapper (adapt TravelPlan `results_parser.py`):
- `NAME_KEYS`, `DESC_KEYS`, `IMAGE_KEYS`
- Map `stars`/`rating` → `rating` string
- Map `review_count` → string
- Categories: join list or pass string
- Price: from `price`, `price_range`, or `attributes.RestaurantsPriceRange2` → display `$`/`$$`/`$$$`/`$$$$` when numeric 1–4
- Geo: `latitude`/`lat`, `longitude`/`lon`/`lng`
- `is_open`: normalize 0/1/true/false → `"true"`/`"false"`
- `business_id` from `business_id` | `id` | strip `biz:yelp:` prefix from `doc_key` when present
- `MAX_RESULTS = 20`
- Blob JSON-in-description merge heuristic (copy TravelPlan)

**Step 3:** `pytest tests/test_results_parser.py -v` → PASS

**Step 4: Commit**

```bash
git add src/local_guide/results_parser.py tests/test_results_parser.py
git commit -m "feat: parse Zeus rows into LocalAI business cards"
```

---

### Task 7: Answer parser fallback (TDD)

**Objective:** Markdown/JSON answer → cards when structured Zeus rows missing.

**Files:**
- Create: `src/local_guide/answer_parser.py` (port from TravelPlan, rename destinations→businesses where needed)
- Test: `tests/test_answer_parser.py` with a Yelp-shaped numbered list fixture

**Step 1:** Port `parse_markdown_answer` + `structured_answer_to_results` from TravelPlan.

**Step 2:** Tests for numbered list with name/location/rating bullets; empty/unstructured → `None`.

**Step 3:** Commit

```bash
git commit -m "feat: markdown answer parser fallback for business lists"
```

---

### Task 8: Async lifecycle (FastAPI lifespan)

**Objective:** `init_http`, startup catalog sync, load chats, clean shutdown.

**Files:**
- Create: `src/local_guide/async_lifecycle.py`

**Step 1: Implementation sketch**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from local_guide.paths import PROJECT_ROOT
from local_guide.zeus_config import configure_zeus_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_zeus_client()
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)

    from zeus_client import close_http, init_http, load_config, logger, sync_chat_requests
    from local_guide.chat_store import load_chats_from_jsonl

    await init_http()
    load_chats_from_jsonl()
    try:
        cfg = await load_config()
        sync_cfg = cfg.get("chat_requests_sync") or {}
        if sync_cfg.get("on_startup"):
            try:
                result = await sync_chat_requests(cfg)
                logger.info("catalog sync synced=%s skipped=%s errors=%s",
                            len(result.synced), len(result.skipped), len(result.errors))
            except Exception as e:
                logger.warning("startup chat_requests sync failed: %s", e)
    except Exception as e:
        logger.warning("startup config load failed: %s", e)

    yield
    await close_http()
```

**Step 2: Commit**

```bash
git commit -m "feat: FastAPI lifespan for http client and catalog sync"
```

---

### Task 9: `search.py` domain wrapper (TDD with mocked `run_agent`)

**Objective:** Full agent turn returning API_CONTRACT success shape.

**Files:**
- Create: `src/local_guide/search.py`
- Test: `tests/test_search_unit.py`

**Step 1: Failing test** — mock `run_agent` to return fake answer/trace/structured; assert keys and `chat_id` prefix `yelp_`.

**Step 2: Implementation** — port `_search_async` from TravelPlan `search.py` with these deltas:
- `PROMPT_PREFIX` = LocalAI domain prompt
- `chat_id = chat_id or ("yelp_" + uuid.uuid4().hex[:12])`
- `default_mode` / `default_sample` from config (`open` / `yelp-demo`)
- `output_schema=DEMO_OUTPUT_SCHEMA`
- `structured=True`
- Waterfall: `zeus_data_to_results` → `extract_businesses` → `structured_answer_to_results`
- Return full success dict including `tool_order=build_tool_order(CHATS)`

**Step 3:** Unit test PASS without live Zeus.

**Step 4: Commit**

```bash
git commit -m "feat: local discovery run_agent search wrapper"
```

---

### Task 10: Business detail + insight helpers

**Objective:** Support detail page without over-fetching full graph dumps.

**Files:**
- Create: `src/local_guide/detail.py`
- Extend tests

**Behavior:**
1. `get_business_card(business_id)` — if last chat results contain id, return that card; else run a short agent message: `Get business {id} and return name, categories, stars, hours, address, geo.`
2. `run_business_insight(business_id, chat_id=None)` — agent turn: summarize reviews good/bad/best-for; parse into:

```json
{
  "business_id": "…",
  "summary": "…",
  "the_good": ["…"],
  "the_bad": ["…"],
  "best_for": ["…"],
  "reviews": [{"author":"…","stars":"5","text":"…","date":"…"}],
  "chat_id": "…",
  "trace": {},
  "answer": "…"
}
```

Prefer structured_answer / zeus_data Review rows; never invent review text if Zeus returned none (state empty lists).

**Commit:** `feat: business detail and AI insight endpoints helpers`

---

### Task 11: FastAPI routes + CORS + error mapping

**Objective:** HTTP API for SPA.

**Files:**
- Create: `src/local_guide/app.py`
- Test: `tests/test_app.py` with `TestClient`, mock search

**Step 1: Routes**

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from local_guide.async_lifecycle import lifespan
from local_guide.chat_store import CHATS
from local_guide.search import run_search

class SearchBody(BaseModel):
    query: str = Field(min_length=1)
    chat_id: str | None = None

def create_app() -> FastAPI:
    app = FastAPI(title="LocalAI", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health():
        return {"ok": True}

    @app.post("/api/search")
    async def api_search(body: SearchBody):
        q = body.query.strip()
        if not q:
            raise HTTPException(400, detail={"error": "empty query"})
        result = await run_search(q, body.chat_id)  # make run_search async for FastAPI
        if result.get("error"):
            status = 502 if "network error" in result["error"] else 400
            raise HTTPException(status, detail=result)
        return result

    @app.get("/api/tool-order")
    async def tool_order():
        from zeus_client import build_tool_order
        return build_tool_order(CHATS)

    # detail + insight routes similarly

    # SPA: if frontend/dist exists, mount assets and SPA fallback
    return app

app = create_app()
```

**Error JSON:** Prefer `{ "error": "…" }` body shape SPA checks (`detail` unwrapped in exception handler if needed):

```python
@app.exception_handler(HTTPException)
async def http_error(request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(exc.detail, status_code=exc.status_code)
    return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code)
```

**Step 2: Tests**
- empty query → 400 `empty query`
- mocked search → 200 all required keys
- tool-order → `{v1, v2}`

**Step 3: Commit**

```bash
git commit -m "feat: FastAPI search, tool-order, health, CORS"
```

---

### Task 12: Vendor chat-trace bundle

**Objective:** Offline-capable trace panel for SPA.

**Files:**
- Create: `scripts/vendor_trace.sh`
- Create: `src/local_guide/static/zeus_client_chat_trace.js` (built artifact)

**Step 1: Script**

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TRACE_SRC="${TRACE_SRC:-$ROOT/../zeus_client_chat_trace}"
cd "$TRACE_SRC"
npm ci
npm run build
mkdir -p "$ROOT/src/local_guide/static"
cp -f dist/zeus_client_chat_trace.js "$ROOT/src/local_guide/static/"
cp -f dist/zeus_client_chat_trace.js.map "$ROOT/src/local_guide/static/" 2>/dev/null || true
echo "vendored → src/local_guide/static/"
```

**Step 2:** Run script; ensure FastAPI mounts:

```python
static_dir = PACKAGE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
```

**Step 3: Commit vendored JS + script**

```bash
git commit -m "chore: vendor zeus_client_chat_trace for LocalAI SPA"
```

---

### Task 13: Scaffold React + Tailwind (Vivid Logic tokens)

**Objective:** Vite React-TS app with design tokens from Stitch DESIGN.md.

**Files:** under `frontend/`

**Step 1:**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install react-router-dom
```

**Step 2:** Configure Vite proxy to backend:

```ts
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/static": "http://127.0.0.1:5000",
    },
  },
});
```

**Step 3:** `index.css` — map DESIGN.md colors (`primary #3525cd`, `primary-container #4f46e5`, `secondary #006b5f`, surfaces, etc.), Inter + JetBrains Mono + Material Symbols links in `index.html`.

**Step 4: Commit**

```bash
git commit -m "feat: scaffold React Vite SPA with Vivid Logic tokens"
```

---

### Task 14: API client + types + normalize

**Objective:** Typed frontend contract matching backend.

**Files:**
- `frontend/src/api/types.ts`
- `frontend/src/api/client.ts`
- `frontend/src/lib/normalize.ts`
- `frontend/src/lib/trace.ts`
- `frontend/src/state/session.ts`

**types.ts** — `SearchResponse`, `BusinessCard`, `InsightResponse`, error union.

**client.ts**

```ts
export async function search(query: string, chatId?: string | null): Promise<SearchResponse> {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, chat_id: chatId ?? undefined }),
  });
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || res.statusText);
  return data as SearchResponse;
}
```

**normalize.ts** — map API card → UI model (`title`, `rating` number, `priceLabel`, placeholder image SVG when empty).

**trace.ts**

```ts
export function ensureTraceScript() {
  if (document.getElementById("zeus-trace-script")) return;
  // Prefer injecting toolOrder when known; never block UI on /api/tool-order
  window.ZeusTraceConfig = window.ZeusTraceConfig || {};
  const s = document.createElement("script");
  s.id = "zeus-trace-script";
  s.src = "/static/zeus_client_chat_trace.js";
  s.async = true;
  document.body.appendChild(s);
}

export function appendTrace(query: string, data: SearchResponse) {
  ensureTraceScript();
  const w = window as any;
  if (typeof w.appendTraceCard === "function") w.appendTraceCard(query, data);
}
```

**session.ts** — `localStorage` key `localai.chat_id`.

**Commit:** `feat: SPA API client, normalize, trace helpers`

---

### Task 15: Shared UI components

**Objective:** Cards, ratings, badges, states matching Stitch.

**Components (implement from Stitch HTML structure, not pixel-perfect OCR):**
- `BusinessCard` — image/placeholder, name, stars, review_count, categories, price, open badge, short why-it-fits (`description`), bookmark icon optional (local state only)
- `RatingStars` — teal accent per DESIGN.md (not yellow)
- `PriceLevel`, `OpenBadge`
- `SearchBar` — large rounded search, AI gradient submit
- `FilterChips` — client-side filter on current results: Open Now, Price, category contains (v1 **client-only**; does not re-query Zeus unless user submits new NL query)
- `AreaSummary` — glassmorphic AI summary from `answer` / `structured_answer.context|tip`
- `ErrorBanner`, `EmptyState`, `Loading`
- `AppShell` — nav: Home / Nearby(disabled or → search) / Discover(/chat) / Saved(localStorage stubs ok)

**Commit:** `feat: LocalAI shared presentational components`

---

### Task 16: Landing page (`/`)

**Objective:** Port `localai_visual_search_ui` behavior.

**Files:** `frontend/src/pages/LandingPage.tsx`

- Hero: “Find your next favorite spot with AI”
- Search submits → `search()` → save `chat_id` → navigate `/search` with results in router state or query cache
- Optional “AI Recommended” section: show last results from session storage if any

**Commit:** `feat: landing page with NL search`

---

### Task 17: Search results page (`/search`)

**Objective:** Port `localai_search_results`.

**Files:** `SearchResultsPage.tsx`, `ResultsMap.tsx`, `ResultsList.tsx`

Layout:
- Left: filters + scrollable cards
- Right (desktop): map pane
- Top: AI area summary strip
- Refine: secondary search input continues same `chat_id`

**Map v1:** Use **Leaflet** + OpenStreetMap tiles (no API key). Plot markers from `latitude`/`longitude`; fit bounds; click marker → highlight card. If no coords, show empty map state with list still usable.

```bash
npm install leaflet react-leaflet
npm install -D @types/leaflet
```

**Commit:** `feat: search results list + map + AI summary`

---

### Task 18: Conversational search page (`/chat`)

**Objective:** Port `localai_conversational_search`.

**Files:** `ConversationalSearchPage.tsx`, `ChatThread.tsx`, `ChatComposer.tsx`

- Multi-turn: always send stored `chat_id`
- Each assistant turn: show markdown/plain `answer` + horizontal/stacked mini `BusinessCard`s from `results`
- Call `appendTrace` each successful turn
- “New Search” clears `chat_id`

**Commit:** `feat: conversational multi-turn discovery UI`

---

### Task 19: Business details page (`/business/:id`)

**Objective:** Port `localai_business_details`.

**Files:** detail components + page

On mount:
1. Prefer card passed via router state
2. Else `GET /api/business/:id`
3. Parallel `POST /api/business/:id/insight` for AI Review Summary (good/bad/best-for)
4. Render hero (name, rating, review_count, open, distance placeholder), AI summary glass card, recent reviews list
5. Back to search link

**Commit:** `feat: business details + AI review summary`

---

### Task 20: Wire router + app shell + loading/error UX

**Objective:** Complete SPA navigation and a11y minimums.

**Files:** `App.tsx`, `main.tsx`

```tsx
<BrowserRouter>
  <Routes>
    <Route element={<AppShell />}>
      <Route path="/" element={<LandingPage />} />
      <Route path="/search" element={<SearchResultsPage />} />
      <Route path="/chat" element={<ConversationalSearchPage />} />
      <Route path="/business/:id" element={<BusinessDetailsPage />} />
    </Route>
  </Routes>
</BrowserRouter>
```

- Disable submit while in flight
- Labels on inputs
- Focus error banner on failure (nice-to-have)

**Commit:** `feat: router shell and UX states`

---

### Task 21: Production static serve from FastAPI

**Objective:** Single-port deploy serves API + SPA.

**In `app.py` after API routes:**

```python
dist = PROJECT_ROOT / "frontend" / "dist"
if dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        # do not swallow /api or /static
        index = dist / "index.html"
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
```

**Build order:** `cd frontend && npm run build` before Docker image copy.

**Commit:** `feat: serve Vite dist from FastAPI`

---

### Task 22: Docker + compose

**Objective:** One-command run like TravelPlan.

**Files:** `Dockerfile`, `docker-compose.yml`

**Dockerfile sketch** (build context monorepo parent `..` so client path works):

```dockerfile
# stage: frontend build
FROM node:20-alpine AS febuild
WORKDIR /fe
COPY demo_yelp/frontend/package*.json ./
RUN npm ci
COPY demo_yelp/frontend/ ./
RUN npm run build

# stage: python
FROM python:3.12-slim
WORKDIR /app
COPY zeus_client_python /zeus_client_python
COPY demo_yelp /app
RUN pip install --no-cache-dir -e /zeus_client_python && pip install --no-cache-dir -e /app
COPY --from=febuild /fe/dist /app/frontend/dist
ENV ZEUS_CLIENT_CONFIG_DIR=/app
ENV ZEUS_CHAT_REQUESTS_DIR=/app/data/chat_requests
ENV CHAT_LOG_PATH=/app/data/chats.jsonl
ENV PORT=5000
EXPOSE 5000
CMD ["python", "-m", "local_guide"]
```

**compose:** port 5000, `ZEUS_URL=http://host.docker.internal:8080`, mount `config.json` + `data/`, `extra_hosts: host.docker.internal:host-gateway`.

**Commit:** `feat: Docker image and compose for LocalAI`

---

### Task 23: README + example queries

**Objective:** Operator docs mirroring TravelPlan README structure.

**Contents:**
- What it is (LocalAI + yelp-demo + Zeus)
- Prerequisites: Zeus with `yelp-demo` enabled/loaded, LLM key
- Quick start Docker + local (backend + `npm run dev`)
- Config table
- API table
- Example queries:
  1. `quiet coffee shops good for deep work`
  2. `romantic italian dinner under $$$`
  3. `dog-friendly parks or outdoor brunch`
  4. Follow-up: `which of these are open late?`
- Troubleshooting matrix from kit ACCEPTANCE
- Note: academic Yelp may lack photos; placeholders expected

**Commit:** `docs: README for LocalAI yelp demo`

---

### Task 24: Full test suite + acceptance checklist

**Objective:** Definition of done.

**Automated:**

```bash
source .venv/bin/activate
pytest -q
# frontend optional:
cd frontend && npm run build
```

**Manual smoke (ACCEPTANCE):**
- [ ] `cp config.example.json config.json` + keys
- [ ] Zeus reachable; scope `yelp-demo/_default` enabled
- [ ] `python -m local_guide` starts
- [ ] `GET /api/health` → ok
- [ ] `POST /api/search` sample query → `answer` or `results`, `trace`, `chat_id`
- [ ] Follow-up same `chat_id` works when durable sessions on
- [ ] SPA landing → results cards
- [ ] Map markers when geo present
- [ ] Chat multi-turn
- [ ] Business detail + insight
- [ ] Trace panel opens via floating control; `appendTraceCard` after search
- [ ] Docker compose up --build works

**Commit:** `test: acceptance coverage for parsers and API`

---

## Best-practice checklist (explicit)

### Backend
- [x] Env-before-import for zeus_client
- [x] FastAPI lifespan resources (httpx client)
- [x] Pydantic request models + consistent error JSON
- [x] CORS locked to dev origins (not `*` with credentials in prod notes)
- [x] No secrets in git; `config.example.json` only
- [x] Structured logging via zeus_client logger
- [x] Unit tests with mocked `run_agent`
- [x] Output schema allowlist (no full doc leak)
- [x] Chat lock per `chat_id` for concurrent turns
- [x] Graceful catalog sync failure (warn, still boot)

### Frontend
- [x] TypeScript types for API
- [x] Proxy in dev; relative `/api` in prod
- [x] Design tokens centralized
- [x] Trace script non-blocking; toolOrder never gates UI
- [x] Placeholder images; empty/error/loading states
- [x] Client-side filters don't pretend to be server truth
- [x] Accessible labels; disabled submit while loading
- [x] Code-split pages if bundle grows (optional)

---

## Files likely to change (summary)

| Area | Paths |
|------|--------|
| Backend core | `src/local_guide/*.py` |
| Static trace | `src/local_guide/static/zeus_client_chat_trace.js` |
| Config | `config.example.json` |
| Frontend | `frontend/src/**` |
| Ops | `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `README.md` |
| Tests | `tests/**` |

**Do not modify** (only read/copy patterns): `../zeus_client_python` source (except installing), Zeus engine, Stitch HTML originals (reference only).

---

## Risks, tradeoffs, open questions

| Risk | Mitigation |
|------|------------|
| No dedicated `local_discovery` chat_request mode | Use `open` + strong domain prompt; allow config switch to `analytics` |
| Scope brief entity names differ (`business` vs `Business`) | Dual keys in `output_schema` + flexible parser |
| Missing images / hours / geo in subset of docs | Placeholders; list works without map |
| Insight endpoint latency (second LLM turn) | Detail page shows shell immediately; insight loads async |
| Contract hash drift | Empty hash for demo + startup sync; document verify script later |
| FastAPI vs Flask divergence from TravelPlan | Follow kit R02b; keep JSON contract identical |
| Large yelp-demo corpus → slow/noisy search | Prompt asks for top relevant; `MAX_RESULTS=20`; operator may need Zeus indexes healthy |
| Map provider choice | Leaflet+OSM for zero keys; swap MapLibre later if needed |

**Open questions (non-blocking defaults chosen):**
1. Default mode `open` vs `analytics` — **default `open`**
2. Saved/bookmarks — **localStorage only in v1**
3. Distance — **optional client haversine if browser geolocation granted; else omit**
4. Whether insight must be separate route vs chat follow-up only — **both: dedicated route for detail page UX**

---

## Implementation order reminder

```text
0  Inputs confirmed (this plan)
1  Scaffold + pyproject + zeus_config
2  config.example
3  chat_store
4  output_schema (TDD)
5  results_parser (TDD)
6  answer_parser (TDD)
7  lifespan
8  search wrapper (TDD)
9  detail/insight
10 FastAPI routes
11 Vendor trace
12 React scaffold + tokens
13 API client
14 Components
15 Pages (landing → results → chat → detail)
16 SPA static serve
17 Docker
18 README
19 Acceptance
```

Each task: failing test when applicable → minimal code → pass → commit.

---

## Execution handoff

Plan complete and saved. Ready to execute using subagent-driven-development — dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?
