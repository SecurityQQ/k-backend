from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class Crawl(SQLModel, table=True):
    __tablename__ = "crawls"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    request_id: UUID = Field(foreign_key="requests.id", ondelete="CASCADE")
    url: str
    status: Optional[str] = Field(default="pending")
    created_at: Optional[datetime] = Field(default=None)