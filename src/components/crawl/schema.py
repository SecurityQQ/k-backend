from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from enum import Enum
from datetime import datetime


class CrawlStatusEnum(str, Enum):
    PENDING = "pending"
    CRAWLING = "crawling"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_pages: Optional[int] = None
    max_depth: Optional[int] = None
    delay_between_requests: Optional[float] = None
    respect_robots_txt: Optional[bool] = None
    follow_redirects: Optional[bool] = None


class CrawlResponse(BaseModel):
    success: bool
    request_id: str
    message: str
    status: str


class CrawlStatusResponse(BaseModel):
    request_id: str
    status: str
    total_pages: int
    completed: int
    failed: int
    total_content: int
    created_at: Optional[str] = None


class CrawlStatistics(BaseModel):
    total_pages: int
    completed_pages: int
    failed_pages: int
    total_content_items: int
    start_time: Optional[datetime] = None

