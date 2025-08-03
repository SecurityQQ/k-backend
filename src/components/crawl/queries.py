"""Database queries for crawl website component"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlmodel import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models.request import Request
from ...db.models.crawl import Crawl
from ...db.models.content import Content
from ...db.config import CrawlStatus, ContentType, RequestStatus

async def create_request(db: AsyncSession, request_id: str, url: str, user_id: str, params: Optional[dict] = None) -> Request:
    """Create a new request record"""
    request = Request(
        id=request_id,
        url=url,
        status=RequestStatus.PENDING,
        user_id=user_id,
        params=params,
        created_at=datetime.utcnow()
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def get_request(db: AsyncSession, request_id: str) -> Optional[Request]:
    """Get request by ID"""
    result = await db.execute(select(Request).where(Request.id == request_id))
    return result.scalars().first()


async def get_crawls_for_request(db: AsyncSession, request_id: str) -> List[Crawl]:
    """Get all crawls for a request"""
    result = await db.execute(select(Crawl).where(Crawl.request_id == request_id))
    return result.scalars().all()


async def get_content_count_for_request(db: AsyncSession, request_id: str) -> int:
    """Get total content count for a request"""
    result = await db.execute(text("""
        SELECT COUNT(*) FROM contents c 
        JOIN crawls cr ON c.crawl_id = cr.id 
        WHERE cr.request_id = :request_id
    """), {"request_id": request_id})
    return result.scalar() or 0


async def update_request_status(db: AsyncSession, request_id: str, status: RequestStatus):
    """Update request status by request_id"""
    result = await db.execute(select(Request).where(Request.id == request_id))
    request = result.scalars().first()
    if request:
        request.status = status
        await db.commit()


async def create_crawl(db: AsyncSession, request_id: str, url: str) -> Crawl:
    """Create a new crawl record"""
    crawl = Crawl(
        id=uuid.uuid4(),
        request_id=request_id,
        url=url,
        status=CrawlStatus.CRAWLING,
        created_at=datetime.utcnow()
    )
    db.add(crawl)
    await db.commit()
    await db.refresh(crawl)
    return crawl


async def update_crawl_status(db: AsyncSession, crawl: Crawl, status: str):
    """Update crawl status"""
    crawl.status = status
    await db.commit()


async def create_content(db: AsyncSession, crawl_id: str, content_type: str, content_hash: str, raw_content: str):
    """Create content record"""
    content = Content(
        id=uuid.uuid4(),
        crawl_id=crawl_id,
        type=content_type,
        hash=content_hash,
        raw=raw_content,
        created_at=datetime.utcnow()
    )
    db.add(content)
    await db.commit()