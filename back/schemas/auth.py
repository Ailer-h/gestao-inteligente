from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    password: SecretStr = Field(min_length=1, max_length=4096)


class AuthUser(BaseModel):
    id: UUID
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str = Field(min_length=1)
    token_type: str
    expires_in: int
    refresh_token: str = Field(min_length=1)
    user: AuthUser
