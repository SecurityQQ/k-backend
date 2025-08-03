from sqlmodel import SQLModel, Field, Column
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import ARRAY, String


class UserToken(SQLModel, table=True):
    __tablename__ = "user_tokens"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    token_hash: str = Field(unique=True, index=True)
    scopes: Optional[List[str]] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    created_at: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    revoked_at: Optional[datetime] = Field(default=None)