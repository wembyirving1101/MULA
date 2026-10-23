# LARAS

A local chat with the Operator AI. The interface uses React and Next.js; the existing
FastAPI backend talks to `huihui_ai/qwen3-abliterated:latest` through Ollama.

## Start chatting

Start Ollama and confirm the model is installed with `ollama list`. Then open two terminals.

Backend:

```sh
cd /Users/rafa/Desktop/LARAS/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend (Node.js 22.18 or later):

```sh
cd /Users/rafa/Desktop/LARAS/frontend
npm install
npm run dev
```

Open [LARAS chat](http://localhost:3000). Type a message and press Enter. Shift + Enter
adds a line. Replies appear as they are generated; Stop cancels an active reply.
New chat clears the screen. Messages stay only in page state and disappear on refresh.
Each request is independent: include the relevant details again in follow-ups.

The Next.js server relays requests to FastAPI, so the browser needs no CORS setup.
To use a different backend address, copy `frontend/.env.example` to
`frontend/.env.local`, edit `LARAS_BACKEND_URL`, and restart Next.js.

## Qwen responsiveness

The backend explicitly disables thinking, requests streaming, keeps the model loaded
for 15 minutes after use, uses a 4,096-token context, and limits replies to 384 tokens.
Sampling uses Qwen's non-thinking recommendations. These are defaults for concise
operational chat, not measured guarantees for every computer.

Override these settings through the backend environment (see `backend/.env.example`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_KEEP_ALIVE` | `15m` | Avoid repeated model loads during a chat session |
| `OLLAMA_NUM_CTX` | `4096` | Bound context memory; minimum 1,024 |
| `OLLAMA_NUM_PREDICT` | `384` | Bound reply length; increase for longer answers |

Use `uvicorn app.main:app --reload --env-file .env` to explicitly load `backend/.env`.
A reply that reaches its token limit is labeled as incomplete in the chat.
The first request after Ollama unloads the model can still be slower. An 8B model's
generation speed depends on available GPU and memory. Use `ollama ps` to inspect
whether the model runs on GPU or CPU. No hardware settings are changed automatically.

References: [Ollama chat API](https://docs.ollama.com/api/chat),
[Ollama runtime configuration](https://docs.ollama.com/faq),
[Qwen3 non-thinking guidance](https://huggingface.co/Qwen/Qwen3-8B#best-practices).

## Checks

```sh
cd /Users/rafa/Desktop/LARAS/backend
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

```sh
cd /Users/rafa/Desktop/LARAS/frontend
npm run typecheck
node --experimental-strip-types --test tests/stream.test.mjs
npm run build
```

For production frontend mode, run `npm run build` then `npm start`. Keep FastAPI and
Ollama running locally. There are no business actions, specialist agents, persistent
memory, database, authentication, permissions, or external integrations.
