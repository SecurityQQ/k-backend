from fastapi import Request, HTTPException, Depends
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.models.user_token import UserToken
from src.db.models.user import User
from src.utils.token import TokenUtils
import os

DATABASE_URL = os.getenv("DATABASE_URL")

# Sync engine for migrations (Alembic)
sync_engine = create_engine(DATABASE_URL, echo=True)

# Async engine for production (convert to asyncpg if needed)
async_db_url = DATABASE_URL
if DATABASE_URL and "postgresql://" in DATABASE_URL:
    async_db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(async_db_url, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_and_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    """Dependency to get async database session"""
    async with async_session() as session:
        yield session


def get_db():
    """Get database session context manager"""
    return async_session()


async def get_user_from_request(request: Request, session: AsyncSession = Depends(get_session)):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        token_type, token = auth_header.split(" ")
        if token_type != "Bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token_hash = TokenUtils.hash_token(token)

    statement = select(User).join(UserToken, User.id == UserToken.user_id).where(UserToken.token_hash == token_hash)

    result = await session.execute(statement)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
