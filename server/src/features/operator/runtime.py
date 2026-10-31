"""Adapter for the real Hermes gateway; Hermes owns the agent loop and history."""

import json
from contextlib import aclosing
from uuid import UUID

import httpx

from ...common.config import HERMES_API_KEY, HERMES_BASE_URL, HERMES_MODEL, HERMES_TIMEOUT_SECONDS


class HermesError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


def request_headers(session_id: UUID | None = None) -> dict[str, str]:
    if not HERMES_API_KEY:
        raise HermesError("Hermes is not configured. Run the backend's Hermes setup first.")
    headers = {"Authorization": f"Bearer {HERMES_API_KEY}"}
    if session_id is not None:
        # Without an explicit ID, Hermes derives identity from prompt text. That
        # could join unrelated chats with the same opening. Never rely on it here.
        headers["X-Hermes-Session-Id"] = f"mula-operator-{session_id}"
    return headers


def check_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    if response.status_code in {401, 403}:
        raise HermesError("Hermes authentication failed. Check the backend and gateway API keys.")
    if response.status_code == 404:
        raise HermesError("Hermes API endpoint is unavailable. Check the gateway URL and version.")
    if response.status_code in {409, 429}:
        raise HermesError("Hermes is busy or the conversation is unavailable. Try again shortly.", response.status_code)
    raise HermesError("Hermes could not complete the request. Check the gateway logs.", 502)


async def sse_events(response: httpx.Response):
    """Parse SSE frames, including comments, CRLF and multiline data fields."""
    event_name = "message"
    data = []
    size = 0
    async for line in response.aiter_lines():
        if not line:
            if data:
                yield event_name, "\n".join(data)
            event_name = "message"
            data = []
            size = 0
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if separator and value.startswith(" "):
            value = value[1:]
        if field == "event":
            event_name = value
        elif field == "data":
            size += len(value)
            if size > 1_000_000:
                raise HermesError("Hermes returned an oversized stream event.", 502)
            data.append(value)
    # SSE requires a blank line to dispatch. A partial final frame is discarded.


async def stream_chat(system_prompt: str, message: str, session_id: UUID):
    payload = {
        "model": HERMES_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "stream": True,
        "model_options": {"reasoning": {"enabled": False}},
    }
    headers = request_headers(session_id)
    saw_text = False
    finish_reason = None
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(HERMES_TIMEOUT_SECONDS, connect=10),
            follow_redirects=False,
        ) as client:
            async with client.stream(
                "POST", f"{HERMES_BASE_URL}/v1/chat/completions", json=payload, headers=headers
            ) as response:
                check_status(response)
                if "text/event-stream" not in response.headers.get("content-type", ""):
                    raise HermesError("Hermes did not return an event stream.", 502)
                async with aclosing(sse_events(response)) as events:
                    async for event_name, data in events:
                        if event_name == "approval.request":
                            # The current UI cannot approve tool actions. Close the
                            # upstream stream so Hermes interrupts the waiting agent.
                            raise HermesError("This action needs an approval interface that is not connected yet.", 502)
                        if event_name in {"hermes.tool.progress", "hermes.status"}:
                            continue
                        if event_name != "message":
                            raise HermesError("Hermes returned an unsupported stream event.", 502)
                        if data == "[DONE]":
                            if finish_reason not in {"stop", "length"} or not saw_text:
                                raise HermesError("Hermes ended without a complete reply.", 502)
                            yield {"type": "done", "truncated": finish_reason == "length"}
                            return
                        try:
                            chunk = json.loads(data)
                            choices = chunk["choices"]
                            if not isinstance(choices, list):
                                raise ValueError("Invalid choices")
                            if not choices:
                                if isinstance(chunk.get("usage"), dict) and "error" not in chunk:
                                    continue
                                raise ValueError("Missing choice")
                            choice = choices[0]
                            delta = choice["delta"]
                            if not isinstance(delta, dict):
                                raise ValueError("Invalid delta")
                            content = delta.get("content")
                            reason = choice.get("finish_reason")
                            if content is not None and not isinstance(content, str):
                                raise ValueError("Invalid content")
                            if finish_reason is not None:
                                raise ValueError("Content after terminal choice")
                            if reason is not None and reason not in {"stop", "length"}:
                                raise ValueError("Unsuccessful finish")
                            # Partial answers may carry diagnostics, which must not
                            # expose raw provider errors or reasoning to the UI.
                            if "error" in chunk and reason != "length":
                                raise ValueError("Upstream error")
                            finish_reason = reason
                        except (ValueError, KeyError, IndexError, TypeError) as error:
                            raise HermesError("Hermes returned an invalid or unsuccessful reply. Check the gateway logs.", 502) from error
                        if content:
                            saw_text = saw_text or bool(content.strip())
                            yield {"type": "token", "content": content}
                raise HermesError("The Hermes connection ended before the reply finished.", 502)
    except httpx.TimeoutException as error:
        raise HermesError("Hermes timed out. Try again or check the model service.", 504) from error
    except httpx.RequestError as error:
        raise HermesError("Cannot reach Hermes. Start the Hermes gateway and check its URL.") from error


async def chat(system_prompt: str, message: str, session_id: UUID) -> tuple[str, bool]:
    parts = []
    truncated = False
    # Both response formats use one execution path and identical failure semantics.
    async with aclosing(stream_chat(system_prompt, message, session_id)) as events:
        async for event in events:
            if event["type"] == "token":
                parts.append(event["content"])
            elif event["type"] == "done":
                truncated = event["truncated"]
    return "".join(parts).strip(), truncated


async def check_readiness() -> None:
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
            response = await client.get(f"{HERMES_BASE_URL}/v1/capabilities", headers=request_headers())
            check_status(response)
            try:
                payload = response.json()
                if payload.get("platform") != "hermes-agent" or payload["features"].get("chat_completions") is not True:
                    raise ValueError("Incompatible gateway")
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                raise HermesError("The gateway does not expose the required Hermes chat API.") from error
    except httpx.RequestError as error:
        raise HermesError("Cannot reach Hermes. Start the Hermes gateway.") from error
