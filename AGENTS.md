# Running this app

Run this app with Docker Compose from the `demo_yelp` directory. These commands return, so you can check the UI and API after them. `docker compose logs -f` follows container logs.

```bash
[ -f .env ] || cp .env.example .env
DOCKER_BUILDKIT=1 docker compose up -d --build
```

- UI: http://localhost:3000 (nginx image `local-guide-frontend`)
- API: http://localhost:5000 (container `local-guide-backend`)
- Zeus from inside the API container is `http://host.docker.internal:8080`. Compose sets `ZEUS_URL` to that value, which wins over `.env`.

The `[ -f .env ]` test leaves an existing `.env` in place. On a new checkout, set `LLM_API_KEY` and `ZEUS_PASSWORD` in `.env`. Keep secrets there. `config.json` stores environment-variable names only.

`config.json` must be a file in this directory. Compose bind-mounts it and bind-mounts `./.env` read-only. It does not use `env_file`, so a `$` in `ZEUS_PASSWORD` stays literal. A missing `config.json` is created as an empty directory in the container, and the API then fails to start.

The backend build context is the parent directory (`context: ..` in `docker-compose.yml`). That build needs the sibling checkout `../zeus_client_python`.

## After code changes

- `src/local_guide/` is bind-mounted. Uvicorn reloads those files. Leave the backend container running.
- The nginx image bakes the SPA. After frontend changes, run `docker compose build frontend && docker compose up -d frontend`, then hard-refresh http://localhost:3000.
- For Vite HMR, run `docker compose --profile dev up -d --build` and open http://localhost:5173. That service proxies `/api` to `http://backend:5000`.

## Tests

Run pytest in the host virtualenv `.venv`. The API image does not install pytest, and Compose does not mount `tests/`.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ../zeus_client_python
pip install -e ".[dev]" --no-deps
pytest -q
```

Frontend typecheck, when needed: `cd frontend && npx tsc --noEmit`.

## Host servers

Start `npm run dev`, `npm run preview`, or `python -m local_guide` on the host when the user asks for a host process. Review and browser checks use the Compose stack above.
