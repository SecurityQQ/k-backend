from pydantic import BaseModel
from typing import Optional, List


# Request models
class CreateUserRequest(BaseModel):
    email: str

class CreateTokenRequest(BaseModel):
    email: str
    scopes: Optional[List[str]] = None
    expires_in_days: int = 30

class CreateJWTTokenRequest(BaseModel):
    email: str
    scopes: Optional[List[str]] = None
    expires_in_days: int = 30

class VerifyTokenRequest(BaseModel):
    token: str

class VerifyJWTTokenRequest(BaseModel):
    token: str

class RefreshJWTTokenRequest(BaseModel):
    refresh_token: str
