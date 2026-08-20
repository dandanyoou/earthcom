from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    default_locale: Literal["ko", "en"]

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


@dataclass(frozen=True)
class LoginIdentity:
    user_id: UUID
    password_hash: str
    status: str
    token_version: int


@dataclass(frozen=True)
class SessionIdentity:
    user_id: UUID
    session_id: UUID
    token_version: int


class RotationStatus(StrEnum):
    ROTATED = "ROTATED"
    REUSED = "REUSED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class RotationOutcome:
    status: RotationStatus
    user_id: UUID | None = None
    session_id: UUID | None = None
    token_version: int | None = None


@dataclass(frozen=True)
class IssuedAuth:
    user_id: UUID
    access_token: str
    refresh_token: str
    expires_in: int
