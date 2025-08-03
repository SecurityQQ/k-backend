from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from .models.request import Request

async def get_request_by_id(db: AsyncSession, request_id: str, user_id: int) -> Optional[Request]:
    """Get a request by its ID and user ID"""
    result = await db.execute(
        select(Request).where(Request.id == request_id, Request.user_id == user_id)
    )
    return result.scalars().first() 