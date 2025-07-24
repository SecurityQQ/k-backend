"""Schema definitions for crawl website component"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class CrawlTarget(BaseModel):
    """Target URL configuration for crawling"""
    url: HttpUrl = Field(..., description="The website URL to crawl")
    max_depth: int = Field(default=2, ge=1, le=5, description="Maximum crawling depth")
    max_pages: int = Field(default=20, ge=1, le=100, description="Maximum pages to crawl")
    javascript_timeout: int = Field(default=5000, ge=1000, le=30000, description="JavaScript timeout in ms")
    follow_external_links: bool = Field(default=False, description="Whether to follow external links")
    respect_robots_txt: bool = Field(default=True, description="Whether to respect robots.txt")


class FormData(BaseModel):
    """Discovered form information"""
    action: str
    method: str
    inputs: List[Dict[str, Any]]


class PageData(BaseModel):
    """Individual page crawl data"""
    url: str
    depth: int
    html_length: int
    text_length: int
    html_content: str
    text_content: str
    forms: List[FormData]
    js_files: List[str]
    js_content: Dict[str, str] = {}  # URL -> content mapping
    links: List[str]
    api_endpoints: List[str]
    status_code: int
    crawl_time: datetime


class CrawlStatus(str, Enum):
    """Crawl status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlResult(BaseModel):
    """Complete crawl results"""
    crawl_id: str
    target: CrawlTarget
    status: CrawlStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    pages_crawled: int = 0
    total_forms: int = 0
    total_js_files: int = 0
    total_api_endpoints: int = 0
    unique_js_files: int = 0
    unique_endpoints: int = 0
    pages: List[PageData] = []
    errors: List[str] = []
    error: Optional[str] = None

    def get_summary(self) -> str:
        """Get a human-readable summary of crawl results"""
        if self.status == CrawlStatus.FAILED and self.error:
            return f"Crawl failed: {self.error}"
        
        summary = f"Crawled {self.pages_crawled} pages"
        if self.total_forms > 0:
            summary += f", found {self.total_forms} forms"
        if self.unique_js_files > 0:
            summary += f", {self.unique_js_files} JS files"
        if self.unique_endpoints > 0:
            summary += f", {self.unique_endpoints} API endpoints"
        
        return summary


class CrawlChatRequest(BaseModel):
    """Request for chatting with crawler agent"""
    message: str = Field(..., description="Message to send to the crawler agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[str] = Field(None, description="Additional context for the conversation")


class CrawlChatResponse(BaseModel):
    """Response from crawler agent chat"""
    response: str
    session_id: str
    pages_discovered: Optional[int] = None
    forms_found: Optional[int] = None
    actions_taken: List[str] = []
    timestamp: datetime


class QuickCrawlRequest(BaseModel):
    """Request for quick crawl"""
    url: HttpUrl = Field(..., description="URL to quickly crawl")
    javascript_timeout: int = Field(default=3000, description="JavaScript timeout in ms")


class RenderPageRequest(BaseModel):
    """Request for rendering a single page"""
    url: HttpUrl = Field(..., description="URL to render")
    wait_time: int = Field(default=3000, description="Time to wait for JavaScript in ms") 