from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class Scan(SQLModel, table=True):
    __tablename__ = "scans"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    request_id: UUID = Field(foreign_key="requests.id", ondelete="CASCADE")
    type: str  # e.g. secrets, xss
    status: Optional[str] = Field(default="pending")
    created_at: Optional[datetime] = Field(default=None)