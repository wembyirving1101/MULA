from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ..auth import accounts
from . import service as speech

router = APIRouter()


class SpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=1200)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value or "\x00" in value:
            raise ValueError("Speech needs readable text.")
        return value


@router.post("/api/speech")
async def create_speech(request: SpeechRequest, account: dict = Depends(accounts.current_account)):
    audio = await speech.synthesize(request.text)
    return Response(audio, media_type="audio/wav", headers={"Cache-Control": "no-store"})
