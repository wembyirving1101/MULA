import os
import re
from fastapi import APIRouter, Cookie, Depends, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from . import accounts

router = APIRouter()


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_.-]{3,40}", value):
            raise ValueError("Use 3–40 letters, numbers, dots, underscores or hyphens.")
        return value


def set_login(response: Response, token: str):
    response.set_cookie(accounts.COOKIE, token, httponly=True, samesite="strict",
                        secure=os.getenv("LARAS_SECURE_COOKIES") == "true",
                        max_age=accounts.SESSION_SECONDS, path="/")


@router.post("/api/auth/signup", status_code=201)
def signup(credentials: Credentials, response: Response):
    token, account = accounts.create_account(credentials.username, credentials.password)
    set_login(response, token)
    return account


@router.post("/api/auth/login")
def login(credentials: Credentials, response: Response):
    token, account = accounts.authenticate(credentials.username, credentials.password)
    set_login(response, token)
    return account


@router.get("/api/auth/me")
def me(account: dict = Depends(accounts.current_account)):
    return account


@router.post("/api/auth/logout")
def logout(response: Response, mula_session: str | None = Cookie(default=None)):
    accounts.logout(mula_session)
    response.delete_cookie(accounts.COOKIE, path="/", httponly=True, samesite="strict")
    return {"status": "ok"}


