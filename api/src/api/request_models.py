from pydantic import BaseModel, Field

class LoginRequestModel(BaseModel):
    email: str
    password: str

class CheckSessionRequestModel(BaseModel):
    session_id: str
    session_token: str

class UpdateUserRequestModel(BaseModel):
    username: str | None = Field(None, alias="username")
    email: str | None = Field(None, alias="email")
    password: str | None = Field(None, alias="password")
    first_name: str | None = Field(None, alias="first_name")
    last_name: str | None = Field(None, alias="last_name")
    role_id: str | None = Field(None, alias="role_id")