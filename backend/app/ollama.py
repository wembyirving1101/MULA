import json
from collections.abc import AsyncIterator
from http.client import HTTPException as HTTPClientError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import httpx

from .config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_KEEP_ALIVE,
    OLLAMA_NUM_CTX, OLLAMA_NUM_PREDICT,
)


class OllamaError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


def chat_payload(system_prompt: str, user_message: str, stream: bool) -> dict:
    # Both API modes use the same Qwen settings to avoid different behavior in the UI.
    return {
        "model": OLLAMA_MODEL,
        "stream": stream,
        # Request only the conversational answer from the Qwen reasoning model.
        "think": False,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {
            "num_ctx": OLLAMA_NUM_CTX,
            "num_predict": OLLAMA_NUM_PREDICT,
            # Qwen's recommended sampling settings for non-thinking chat.
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 20,
            "min_p": 0.0,
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }


def upstream_http_error(status_code: int) -> OllamaError:
    if status_code == 404:
        return OllamaError(
            f"Ollama model '{OLLAMA_MODEL}' was not found. "
            f"Run 'ollama pull {OLLAMA_MODEL}' on the Ollama host, "
            "or set OLLAMA_MODEL to an installed model."
        )
    # Do not forward arbitrary upstream response bodies to API consumers.
    return OllamaError(
        f"Ollama returned HTTP {status_code}. Check the Ollama service and model.",
        status_code=502,
    )


def chat(system_prompt: str, user_message: str) -> str:
    payload = chat_payload(system_prompt, user_message, stream=False)
    request = Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise upstream_http_error(error.code) from error
    except TimeoutError as error:
        raise OllamaError(
            "Ollama did not respond within 120 seconds. Try again.", status_code=504
        ) from error
    except URLError as error:
        raise OllamaError(
            f"Cannot reach Ollama at {OLLAMA_BASE_URL}. Start Ollama and try again."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise OllamaError("Ollama returned invalid JSON.", status_code=502) from error
    except (OSError, HTTPClientError) as error:
        raise OllamaError("The connection to Ollama failed. Try again.") from error

    # Validate the upstream structure before accessing nested fields.
    if not isinstance(result, dict):
        raise OllamaError("Ollama returned an invalid response.", status_code=502)
    response_message = result.get("message")
    if not isinstance(response_message, dict):
        raise OllamaError("Ollama returned an invalid message.", status_code=502)
    message = response_message.get("content")
    if not isinstance(message, str) or not message.strip():
        raise OllamaError("Ollama returned an empty response.", status_code=502)
    return message.strip()


async def stream_chat(system_prompt: str, user_message: str) -> AsyncIterator[dict]:
    """Read Ollama NDJSON incrementally, forwarding only public answer text."""
    payload = chat_payload(system_prompt, user_message, stream=True)
    has_content = False
    try:
        # The async connection closes on completion, failure, or browser disconnect.
        async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=10)) as client:
            async with client.stream(
                "POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload
            ) as response:
                if response.status_code != 200:
                    raise upstream_http_error(response.status_code)
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    if not isinstance(chunk, dict):
                        raise OllamaError("Ollama returned an invalid response.", 502)
                    if chunk.get("error"):
                        raise OllamaError("Ollama failed during generation. Try again.", 502)
                    message = chunk.get("message")
                    if not isinstance(message, dict):
                        raise OllamaError("Ollama returned an invalid message.", 502)
                    content = message.get("content", "")
                    if not isinstance(content, str):
                        raise OllamaError("Ollama returned invalid answer text.", 502)
                    if content:
                        if content.strip():
                            has_content = True
                        yield {"type": "token", "content": content}
                    if chunk.get("done") is True:
                        if not has_content:
                            raise OllamaError("Ollama returned an empty response.", 502)
                        yield {
                            "type": "done",
                            "truncated": chunk.get("done_reason") == "length",
                        }
                        return
        # A closed socket without a terminal event must not look like a full reply.
        raise OllamaError("Ollama stopped before finishing the reply. Try again.", 502)
    except httpx.TimeoutException as error:
        raise OllamaError("Ollama timed out while generating the reply. Try again.", 504) from error
    except httpx.RequestError as error:
        raise OllamaError(
            f"Cannot reach Ollama at {OLLAMA_BASE_URL}. Start Ollama and try again."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise OllamaError("Ollama returned invalid JSON.", 502) from error
