from pathlib import Path
from uuid import UUID

from .runtime import chat, stream_chat


OPERATOR_PROMPT = (Path(__file__).parent / "prompts" / "operator.md").read_text(encoding="utf-8")


async def operator_reply(message: str, session_id: UUID) -> tuple[str, bool]:
    return await chat(OPERATOR_PROMPT, message, session_id)


def operator_stream(message: str, session_id: UUID):
    # Return the iterator directly so disconnects close the Hermes connection.
    return stream_chat(OPERATOR_PROMPT, message, session_id)
