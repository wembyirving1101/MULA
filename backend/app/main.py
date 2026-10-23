import json
from contextlib import aclosing
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .agents import operator_reply, operator_stream
from .config import OLLAMA_BASE_URL, OLLAMA_MODEL
from .ollama import OllamaError


app = FastAPI(title="LARAS AI Backend", version="0.1.0")


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=8000)
    stream: bool = False

    @field_validator("message")
    @classmethod
    def reject_blank_message(cls, value: str) -> str:
        # Whitespace alone satisfies a length check but is not a user request.
        value = value.strip()
        if not value:
            raise ValueError("Message must contain non-whitespace text.")
        return value


class ChatResponse(BaseModel):
    agent: Literal["operator"] = "operator"
    reply: str
    model: str


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "provider": "ollama",
        "model": OLLAMA_MODEL,
        "ollama_base_url": OLLAMA_BASE_URL,
    }


@app.post("/api/agents/operator/chat", response_model=ChatResponse)
def chat_with_operator(request: ChatRequest) -> ChatResponse | StreamingResponse:
    if request.stream:
        return StreamingResponse(
            operator_events(request.message),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
        )
    # A synchronous route lets FastAPI run the blocking Ollama call in its thread pool.
    try:
        reply = operator_reply(request.message)
    except OllamaError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    return ChatResponse(reply=reply, model=OLLAMA_MODEL)


async def operator_events(message: str):
    # Once headers are sent, stream failures must be explicit events, not HTTP errors.
    try:
        async with aclosing(operator_stream(message)) as events:
            async for event in events:
                yield json.dumps(event, ensure_ascii=False) + "\n"
    except OllamaError as error:
        yield json.dumps({
            "type": "error", "detail": str(error), "status_code": error.status_code
        }) + "\n"
