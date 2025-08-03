from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class Request(SQLModel, table=True):
    __tablename__ = "requests"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    url: str
    status: str = Field(default="pending")
    params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    created_at: Optional[datetime] = Field(default=None)