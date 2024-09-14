from pydantic import BaseModel

class LoginRequestModel(BaseModel):
    email: str
    password: str

class CheckSessionRequestModel(BaseModel):
    session_id: str
    session_token: str