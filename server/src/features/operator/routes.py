import json
from contextlib import aclosing
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ..auth import accounts
from ...common.config import HERMES_MODEL
from .agent import operator_reply, operator_stream
from .runtime import HermesError

router = APIRouter()


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=8000)
    stream: bool = False
    session_id: UUID | None = None

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
    session_id: UUID
    truncated: bool = False


@router.post("/api/agents/operator/chat", response_model=ChatResponse)
async def chat_with_operator(request: ChatRequest, account: dict = Depends(accounts.current_account)) -> ChatResponse | StreamingResponse:
    session_id = UUID(account["conversation_id"])
    if request.session_id is not None and request.session_id != session_id:
        raise HTTPException(403, "This conversation belongs to another account.")
    accounts.add_message(account["id"], "user", request.message)
    reply_id = accounts.add_message(account["id"], "assistant", "", "Reply interrupted.")
    if request.stream:
        return StreamingResponse(
            operator_events(request.message, session_id, reply_id),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
        )
    try:
        reply, truncated = await operator_reply(request.message, session_id)
    except HermesError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    note = None
    if truncated:
        note = "Reply reached its length limit."
    accounts.save_reply(reply_id, reply, note)
    return ChatResponse(reply=reply, model=HERMES_MODEL, session_id=session_id, truncated=truncated)


async def operator_events(message: str, session_id: UUID, reply_id: int):
    # Once headers are sent, stream failures must be explicit events, not HTTP errors.
    parts = []
    note = "Reply interrupted."
    try:
        yield json.dumps({"type": "session", "session_id": str(session_id)}) + "\n"
        async with aclosing(operator_stream(message, session_id)) as events:
            async for event in events:
                if event["type"] == "token":
                    parts.append(event["content"])
                if event["type"] == "done":
                    note = None
                    if event.get("truncated"):
                        note = "Reply reached its length limit."
                yield json.dumps(event, ensure_ascii=False) + "\n"
    except HermesError as error:
        yield json.dumps({
            "type": "error", "detail": str(error), "status_code": error.status_code
        }) + "\n"

    finally:
        accounts.save_reply(reply_id, "".join(parts), note)


@router.get("/api/conversation")
def conversation(account: dict = Depends(accounts.current_account)):
    return {"session_id": account["conversation_id"], "messages": accounts.history(account["id"])}


