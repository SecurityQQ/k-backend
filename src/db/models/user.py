from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    created_at: Optional[datetime] = Field(default=None)