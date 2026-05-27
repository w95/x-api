# x-api

A small JSON-only HTTP API over X.com data, built with **FastAPI** on top of [twscrape](https://github.com/vladkens/twscrape).

No HTML, no RSS, no embeds, no JS — just JSON. Sits on a twscrape session pool, so upstream auth, rate-limit accounting, and parsing are someone else's problem.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/user/{name}` | User profile by handle |
| `GET` | `/api/user/{name}/tweets?limit=20&include_replies=false` | User timeline (or with replies) |
| `GET` | `/api/tweet/{id}` | Single tweet by id |
| `GET` | `/api/search?q=...&limit=20` | Tweet search |
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/docs` | Swagger UI (auto-generated) |
| `GET` | `/openapi.json` | OpenAPI 3 schema |

Response shapes are defined in [app/models.py](app/models.py) (`UserOut`, `TweetOut`, `MediaOut`, `TimelinePage`, `SearchResponse`).

## Prerequisites

- One or more **X.com cookie sessions** (`auth_token` + `ct0`). See [Getting sessions](#getting-sessions) below.
- Either **Docker** (recommended), or **Python 3.10+** locally.

## Quick start — Docker

```bash
# 1. drop one or more cookie sessions here, one per line (format below)
cp sessions.jsonl.example sessions.jsonl
$EDITOR sessions.jsonl   # replace the placeholders with real auth_token / ct0

# 2. build & run
docker compose up -d --build

# 3. hit it
curl http://127.0.0.1:8086/api/user/jack
open http://127.0.0.1:8086/docs
```

The service binds **127.0.0.1:8086 → container 8000**. Account state lives in a named volume (`x-api-db`) so restarts don't re-add sessions.

To stop: `docker compose down`. To wipe persistent state: `docker compose down -v`.

## Quick start — local

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8086
```

`X_API_DB` (default `./x-api.db`) controls where the twscrape SQLite state lives.

## Getting sessions

The `sessions.jsonl` file is one JSON object per line:

```json
{"kind":"cookie","username":"jack","auth_token":"<40-hex>","ct0":"<160-hex>"}
```

Only `auth_token` and `ct0` are required by twscrape (`username` is a label). See [sessions.jsonl.example](sessions.jsonl.example) for the exact shape.

**Manual (most reliable):** log into x.com in your browser, open DevTools → *Application → Cookies → https://x.com*, copy `auth_token` and `ct0`. Append a line to `sessions.jsonl`. Restart: `docker compose restart`.

**Programmatic:** twscrape ships its own login flows (username/password and cookie-based) — see the [twscrape README](https://github.com/vladkens/twscrape#add-accounts) and the [`twscrape` CLI](https://github.com/vladkens/twscrape#cli) (`twscrape add_accounts ...` / `twscrape login_accounts`). X's anti-bot challenges (passkey modal, Arkose) defeat most automated logins in practice; the manual path above is usually faster.

**Don't use your main account.** X bans sessions used for scraping. Use throwaways and rotate them.

To add **more than one** session for higher per-endpoint rate limit headroom, just append more lines — twscrape rotates automatically per endpoint.

## Architecture (one screen)

```
HTTP request  →  FastAPI route (app/routes.py)
                       ↓
                 twscrape.API method  (e.g. user_by_login, tweet_details, search)
                       ↓
                 session pool (SQLite at $X_API_DB)
                       ↓
                 X.com private GraphQL — request signed with the picked session's cookies + tid
                       ↓
                 twscrape parser → typed dataclass
                       ↓
                 pydantic model (app/models.py) → JSON
```

twscrape handles: session rotation, per-endpoint rate-limit accounting, retries, GraphQL feature flags, `x-client-transaction-id` generation, and the upstream JSON parser. Everything in `app/` is a thin shell on top.

## Layout

```
x-api/
├── app/
│   ├── deps.py         # twscrape API singleton (path from $X_API_DB)
│   ├── sessions.py     # loads sessions.jsonl into the pool on startup
│   ├── models.py       # pydantic UserOut / TweetOut / MediaOut / ...
│   ├── routes.py       # the 4 endpoints
│   └── main.py         # FastAPI app + lifespan + /healthz
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── sessions.jsonl.example  # template — copy to sessions.jsonl (gitignored)
```

## Caveats

- **No cursor pagination yet.** `limit` is honored but you get one upstream page (~20 items) at a time. If you need real paging, switch to twscrape's `*_raw` methods and forward the cursor.
- **`limit` is a soft cap** — twscrape returns one full upstream page before honoring it. We slice to `limit` server-side, so the response is exact; just know that the underlying fetch did more work than the cap implies.
- **Field drift.** X changes its private API shapes. If a field starts coming back as `None` or the wrong type, check twscrape's parser first (`pip install -U twscrape`).
- **Session bans.** A 0-session pool returns HTTP 500 from twscrape with a misleading message. If responses suddenly stop, check the container logs — chances are your session is banned and you need a new one.

## License

[MIT](LICENSE), matching the upstream [twscrape](https://github.com/vladkens/twscrape) library this project wraps.
