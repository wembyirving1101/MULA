# LARAS Operator AI

A small FastAPI service for LARAS's single conversational entry point. It uses a local
Ollama model to clarify operational requests, answer general questions, and suggest
next steps. Only the Operator AI is implemented and exposed.

## Setup and run

Use Python 3.10 or later. Start Ollama and confirm the model is installed:

```sh
ollama list
# Only if the model is missing:
ollama pull huihui_ai/qwen3-abliterated:latest
```

If Ollama is not running, start `ollama serve` in another terminal. Then run:

```sh
cd /Users/rafa/Desktop/LARAS/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

| Environment variable | Default |
| --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `OLLAMA_MODEL` | `huihui_ai/qwen3-abliterated:latest` |
| `OLLAMA_KEEP_ALIVE` | `15m` |
| `OLLAMA_NUM_CTX` | `4096` |
| `OLLAMA_NUM_PREDICT` | `384` |

The defaults need no configuration. To change them, export the variables before
starting the service, or use the example file:

```sh
cp .env.example .env
# Edit .env, then load it explicitly:
uvicorn app.main:app --reload --env-file .env
```

The application does not automatically load `.env`. Restart after configuration changes.

## Example request

```sh
curl -X POST http://localhost:8000/api/agents/operator/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"How can LARAS help me plan deliveries for my shop?"}'
```

Example response shape (the reply varies):

```json
{
  "agent": "operator",
  "reply": "I can help you plan delivery steps. What are you delivering, and when does it need to arrive?",
  "model": "huihui_ai/qwen3-abliterated:latest"
}
```

Each request is independent: there is no conversation history or memory. Include all
relevant context in `message`, including earlier details when answering a follow-up.
Messages must be strings of 1–8,000 characters and contain non-whitespace text. Extra
request fields are rejected.

## Streaming and chat interface

See the root README for the React + Next.js chat frontend at `http://localhost:3000`.
The same endpoint supports streaming when the body includes `"stream": true`:

```sh
curl -N http://localhost:8000/api/agents/operator/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What can you help with?","stream":true}'
```

Streaming responses use `application/x-ndjson`: one JSON event per line. Token events
contain `{"type":"token","content":"..."}`. Success ends with
`{"type":"done","truncated":false}`. `truncated: true` means the reply hit its
configured token limit. After streaming headers are sent, failures arrive as
`{"type":"error","detail":"...","status_code":503}` rather than a changed HTTP
status. Request validation still returns HTTP 422 before streaming starts. A closed
stream without `done` is incomplete. Disconnecting closes the upstream connection.

Thinking is disabled, the model stays loaded for 15 minutes after use, and generation
is bounded to a 4,096-token context and 384-token reply. Both modes share these
settings; see the root README for tuning and limitations.

Errors use FastAPI's `detail` field:

- `422`: invalid JSON or request fields, with validation details.
- `503`: Ollama unavailable or model missing, with recovery guidance.
- `504`: Ollama took longer than 120 seconds to respond.
- `502`: another Ollama HTTP error, invalid JSON, invalid message, or empty reply.

`GET /health` reports API liveness and configuration. It does not check Ollama
connectivity or model readiness. No other agent chat route exists.

## Editing and checks

- `app/main.py`: Operator endpoint, request validation, and API errors.
- `app/agents.py`: Operator prompt and entry function; future routing can start here.
- `app/ollama.py`: Ollama client and upstream errors, following the
  [Ollama chat API](https://docs.ollama.com/api/chat).
- `app/config.py`: environment configuration.

Run focused tests without a running Ollama instance:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Later steps

There is no Inventory Agent or other specialist agent, database, conversation memory,
authentication, employee permissions, RAG, or external integration. The Operator has
no tools or live business records and cannot execute business actions. Its prompt
explains those limits; future tools will need their own validation and authorization.
