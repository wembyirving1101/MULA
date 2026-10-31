# LARAS Operator on Hermes

FastAPI owns Mula's API contract and Operator instructions. A separate, real Hermes gateway owns model execution, its agent loop, persisted conversation history and context compression. Ollama remains the default model provider inside Hermes; FastAPI no longer calls Ollama directly or silently falls back to it.

The HTTP integration follows [Hermes' API server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server). Upstream is pinned in `hermes/revision.txt` to `c841bfcd0ad2ca5535589ce1cbcb06d7ac25c7cc`. Upgrade that revision deliberately and rerun the integration checks.

## Setup

Run from the repository root:

```sh
python3 -m venv server/.venv
server/.venv/bin/python -m pip install -r server/requirements-dev.txt
python3 server/scripts/setup_hermes.py
bash server/scripts/install_hermes.sh
```

If the existing backend virtual environment is installed, keep it. `setup_hermes.py` generates matching random server-side credentials in `server/.env.hermes` and `.runtime/hermes/.env`, and copies `server/hermes/config.yaml` into `.runtime/hermes/config.yaml`. It never overwrites existing configuration. Credentials and runtime state are ignored by Git; files holding credentials are created with owner-only permissions.

The installer downloads the pinned upstream checkout into `.runtime/hermes-source` and uses its locked dependency installation stage. Hermes manages its own Python and dependencies; they are not added to FastAPI's environment. The script skips browser/computer-use installation and does not install a global launcher or modify shell startup files. The upstream installer can still download its core runtime tools and dependencies.

### Model compatibility

The supplied profile selects `huihui_ai/qwen3-abliterated:latest` through `http://127.0.0.1:11434/v1` with the observed 40,960-token window.

Upstream Hermes enforces a 64,000-token startup minimum. `scripts/apply_hermes_profile.py` applies a small, reproducible exception against the pinned source revision. It allows only the explicitly enabled `agent.mula_compact_operator` API-server profile, the selected Qwen model, zero tools, and windows between 8,192 and 40,960. All other cases retain the upstream check. This is a local modification to Hermes, not an upstream configuration option. Adding tools requires reconsidering the context budget.

The patch is applied during install and startup. It checks the revision, preserves unrelated edits, and refuses unexpected source changes. Keep using `start_hermes.sh`; launching an unpatched Hermes installation directly will retain the original minimum.

Compression has an absolute trigger of 24,000 tokens and protects the most recent six messages. Summarization can lose details, and compression itself makes model calls; business records must remain in the application database. The 40,960-token window is capacity, not a fixed per-message token charge. Long conversations and compression quality still need workload testing.

If a gateway is already running, reload the profile with:

```sh
bash server/scripts/start_hermes.sh --replace
```

The old direct-Ollama FastAPI environment settings are no longer used.

## Start

After setup, use one command to launch the complete stack:

```sh
bash /Users/rafa/Desktop/LARAS/run.sh
```

The launcher reuses reachable services, starts missing ones, and opens the app. Leave it running; Ctrl+C stops the services it started. Logs live in `.runtime/logs`. Add `--no-open` to skip opening a browser.

### Individual services


In separate terminals, from the repository root:

```sh
# 1. Ollama must already be running and serving the configured model.
# 2. Dedicated Hermes gateway (binds to 127.0.0.1:8642).
bash server/scripts/start_hermes.sh
```

```sh
# 3. Application backend.
cd server
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --env-file .env.hermes
```

```sh
# 4. Existing UI.
cd client
npm run dev
```

If you already have a Hermes gateway elsewhere, set `HERMES_BASE_URL`, `HERMES_API_KEY` (matching its `API_SERVER_KEY`), `HERMES_MODEL` and optional `HERMES_TIMEOUT_SECONDS` using `server/.env.example`. Use a dedicated profile with the same restricted tools policy. A personal Hermes profile may expose terminal/file tools, private memory or unrelated integrations.

## API and continuity

`POST /api/agents/operator/chat` still accepts `message` (1–8,000 non-whitespace characters) and `stream` (default false). It requires an account session cookie. The backend assigns the account’s permanent conversation UUID; an optional `session_id` must match that UUID or the request is refused with 403:

```json
{"message":"My shop is Mula Cafe","session_id":"df2f78e5-abd6-43c2-8b10-145783ac2301","stream":false}
```

Every account has a server-owned UUID reused for every turn. Callers cannot start or read another conversation by changing the ID. Hermes receives a namespaced `X-Hermes-Session-Id` and loads its history. The browser sends only the new question. Relevant history still consumes model input tokens.

JSON responses retain `agent`, `reply`, `model`, and add `session_id` and `truncated`. `model` now names the Hermes gateway alias; inspect Hermes config for the underlying inference model.

Streaming remains newline-delimited JSON:

```json
{"type":"session","session_id":"df2f78e5-abd6-43c2-8b10-145783ac2301"}
{"type":"token","content":"Hello"}
{"type":"done","truncated":false}
```

Failures after headers are sent emit `type: error` with a safe `detail` and `status_code`. The adapter translates Hermes SSE, requires a successful terminal status and `[DONE]`, filters reasoning and internal status events, and reports partial/length-limited replies. Unexpected approval requests fail explicitly because this UI does not yet support them.

**Stop** closes the stream through Next.js and FastAPI to Hermes. The pinned gateway interrupts the agent when it detects the closed SSE connection; this is cooperative cancellation, not a rollback of completed work. No business-action tools are enabled here. Interrupted/failed turns may already be in Hermes history; retrying submits a new turn.

The UI reopens the account conversation after login and refresh. There is no New chat button. Application history is persisted in `.runtime/accounts.sqlite3`; Hermes retains its own model transcript. Old chats from before accounts were added are not assigned to a new account automatically.

## Health

- `GET /health`: application liveness, runtime name and configured gateway alias. Makes no upstream request.
- `GET /ready`: verifies authentication and Hermes chat capabilities. Returns 503 if unavailable/incompatible. It does **not** run model inference or certify the model's context window, throughput or quality.

## Files and extension points

- `src/features/operator/prompts/operator.md`: Operator role and current business limitations.
- `src/features/operator/agent.py`: role entry point, delegating execution to the runtime adapter.
- `src/features/operator/runtime.py`: Hermes HTTP/SSE transport, completion validation and error handling.
- `src/main.py`: Mula API composition, validation-error handling and health checks.
- `src/features/auth/`: account routes and storage, with feature tests.
- `src/features/operator/routes.py`: chat routes and account-owned conversation routing.
- `src/features/voice/`: authenticated speech routes, local TTS service and tests.
- `hermes/config.yaml`: template for the dedicated runtime profile.
- `.runtime/hermes`: private runtime configuration and durable Hermes state (ignored).

This migration intentionally implements only the existing Operator. The profile has empty API/CLI toolsets, no MCP servers and disabled cross-chat memory. Hermes delegation is available upstream but is not enabled or represented as an implemented Inventory/Procurement agent. Adding those requires specialist instructions, scoped business tools, tenant permissions and approval handling before enabling the corresponding Hermes toolsets. Keep business records in the application database rather than treating model memory as the source of truth.

## Checks

```sh
cd server
.venv/bin/python -m unittest discover -s . -t . -v
```

Tests use a simulated Hermes transport and make no model calls. For a live check, start both services, check `/ready`, send a unique fact with a session UUID, ask about it using the same UUID, and verify another UUID does not recall it. Also test Stop during generation. Credentials must stay on the server and out of screenshots/logs.

### Simple accounts

Create an account through the UI with a 3–40 character username and a 10–128 character password. Usernames are case-insensitive. The first version has one workspace per account, with no invitations, password reset or employee roles.

- `POST /api/auth/signup` and `/api/auth/login`: username/password JSON, returning public account information and an HttpOnly, SameSite=Strict cookie.
- `GET /api/auth/me`: current account; 401 if signed out or expired.
- `POST /api/auth/logout`: revokes the session and clears the cookie.
- `GET /api/conversation`: only the signed-in account’s saved chat.

Passwords use salted scrypt hashes. Opaque random sessions are stored as SHA-256 hashes and expire after seven days. Failed login attempts are limited to five per username per 15 minutes. The frontend proxy checks mutation origins and forwards private cookies server-side. Account creation remains open in this local first version.

The SQLite file defaults to `.runtime/accounts.sqlite3`; `LARAS_ACCOUNT_DB` overrides the path. Preserve it to preserve accounts and visible history. Set `LARAS_SECURE_COOKIES=true` when serving through HTTPS. Long-term shared Hermes memory is still disabled: account authentication alone does not isolate a shared Hermes profile’s personal memory.

Live validation after the compact-profile change: Qwen replied through Hermes and a second turn recalled a shop name using the same session UUID. Automated backend checks also verify that tools, other models and other platforms retain the upstream minimum. This validates short conversation execution; it is not a long-context quality or throughput benchmark.
