from sqlmodel import SQLModel, Field, Column
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.dialects.postgresql import JSONB


class ScanContent(SQLModel, table=True):
    __tablename__ = "scan_content"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    scan_id: UUID = Field(foreign_key="scans.id", ondelete="CASCADE")
    content_id: UUID = Field(foreign_key="contents.id", ondelete="CASCADE")
    finding: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    severity: Optional[str] = Field(default="low")