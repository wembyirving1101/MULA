# Mula / LARAS

Mula's Operator chat now uses the actual [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent) runtime. LARAS remains the underlying system name.

```text
Next.js chat → LARAS FastAPI → Hermes gateway → Ollama / Qwen
                                  │
                                  └─ Agent loop, session history, context compression
```

The app has simple username/password accounts. Each account owns one persistent Operator conversation, reopened after login or refresh. Sign out replaces New chat. Passwords are hashed and login sessions use private cookies; accounts and the visible chat history are stored in `.runtime/accounts.sqlite3`.

This migration keeps Operator's existing planning scope. Inventory, Procurement, business tools, and autonomous actions have not been implemented. The dedicated Hermes profile starts with no tools and no cross-chat personal memory. This is the runtime foundation for adding scoped specialists later.

## Architecture

See [the current Mula harness architecture](docs/architecture/mula-harness.md) for the account boundary, Operator execution flow, storage, context management and current tool support.

The project groups application code by feature:

```text
LARAS/
├── public/                     # Static assets, including the Mula logo
├── src/
│   ├── app/                     # Next.js routes, layout and API entry points
│   ├── common/
│   │   ├── components/          # Shared UI components
│   │   ├── hooks/               # Shared hooks
│   │   ├── services/            # Shared server proxy
│   │   ├── styles/              # Global styles and theme
│   │   └── tests/
│   └── features/
│       ├── auth/                # Account UI and public index.ts
│       ├── operator/            # Core visualizer, streaming and tests
│       ├── voice/               # Speech playback and tests
│       └── workspace/           # Workspace screen
├── server/                     # Separate Python service
│   ├── src/
│   │   ├── main.py
│   │   ├── common/
│   │   └── features/            # Auth, Operator and voice routes/services/tests
│   ├── tests/
│   ├── scripts/
│   └── hermes/
├── scripts/                    # Whole-app launcher
├── docs/
└── .runtime/                   # Private configuration and durable state
```

Client features expose their public APIs through `index.ts`; server features expose their integration surfaces through `__init__.py`. Keep feature-specific components, services and tests with their feature. Put code in `common` when multiple features need it. Next.js routing remains in `src/app`, while feature implementations live in `src/features`.

The client application now lives at the repository root, with top-level `public/` and `src/`. The Python service lives in `server/`. Restart existing processes after this move. The one-line launcher, ports, HTTP endpoints, account database and runtime profile locations remain compatible. Manual server startup now uses `src.main:app`.

## Run

After the one-time setup in [backend setup](server/README.md), start everything with one line from any Terminal location:

```sh
bash /Users/rafa/Desktop/LARAS/run.sh
```

From the project folder, `./run.sh` works too. It starts Ollama if needed, then Hermes, FastAPI and the frontend, waits for them to become reachable, and opens http://127.0.0.1:3000. Existing services are reused. Leave this Terminal open; Ctrl+C stops only services started by this launcher. Logs are written under `.runtime/logs`. Use `./run.sh --no-open` to skip opening the browser.

The launcher uses the existing installation; it reports missing setup instead of downloading dependencies during every launch. If an old backend is still running without account endpoints, stop that Terminal first so port 8000 becomes available. The compact tool-free Operator profile uses the current Qwen model at its 40,960-token window.

## Workspace and AI voice

The workspace uses the supplied Mula logo, a dark charcoal/clay palette, and a layered circular Operator core. The core reacts to the actual playback waveform through Web Audio; reduced-motion preferences keep it still. Expand chat gives the saved conversation more space. Reports, My website and My team are marked as upcoming, since those features are not connected yet.

Voice mode reads each newly completed answer aloud. Select **Chat** or the speaker/mute button to stop audio immediately and disable automatic speech. This preference is remembered in this browser. Existing history is never read automatically; **Play reply** replays an answer when voice is enabled. Sending another message, signing out or hiding the tab stops current playback. Voice output is TTS only; microphone input is not implemented.

After updating from the text-only version, restart the running backend before using voice; the launcher deliberately reuses existing services, so an old process will not load the new speech endpoint automatically.

The initial free provider is macOS's built-in `say` engine on the backend machine, using its configured system voice. No paid API, model download or new dependency is required. Audio is generated in a private temporary directory, returned as uncached WAV through the authenticated `/api/speech` proxy, and deleted after generation. The frontend removes code/Markdown syntax and splits long answers into chunks; each speech request is limited to 1,200 characters, one synthesis job per backend process, with a 30-second generation timeout. Muting cancels client requests and playback; an already running server job can finish within that bound if its connection closes. Replies remain readable if voice fails.

This provider needs **a macOS backend**; browsers on other devices can use that backend. A Linux/GPU production deployment needs a replacement speech provider. The endpoint does not forward conversation text to a third-party TTS service. Speech starts after the text reply completes, and long replies may pause between chunks. Browser audio permission is unlocked by Send/Voice/Play reply interactions.

## Verify

```sh
cd server
.venv/bin/python -m unittest discover -s . -t . -v
```

```sh
# From the repository root
npm run typecheck
npm test
npm run build
```

The backend tests simulate the documented Hermes HTTP boundary, including session routing, interrupted streams, authentication failures, reasoning filtering and cancellation. They do not substitute for a live Hermes/model test.

## Deployment boundary

This version provides local accounts and server-enforced conversation ownership. One account represents one workspace. Employee invitations, roles, password recovery and separate Hermes memory profiles are not implemented yet. Cross-chat personal memory remains disabled until profile isolation is implemented. For HTTPS hosting, set `LARAS_SECURE_COOKIES=true`, protect the database and keep Hermes private.
