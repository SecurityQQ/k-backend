from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class Content(SQLModel, table=True):
    __tablename__ = "contents"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    crawl_id: UUID = Field(foreign_key="crawls.id", ondelete="CASCADE")
    type: str  # e.g. html / js
    content_path: Optional[str] = Field(default=None)
    hash: Optional[str] = Field(default=None)
    raw: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)