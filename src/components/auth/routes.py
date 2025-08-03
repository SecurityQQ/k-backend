from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Any

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid

from src.db.database import get_session, get_user_from_request
from src.db.models.user import User
from src.utils.token import TokenUtils
from .schema import CreateUserRequest, CreateTokenRequest, CreateJWTTokenRequest, VerifyTokenRequest, VerifyJWTTokenRequest, RefreshJWTTokenRequest
from .lib.token_service import TokenService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/user")
async def create_user(
    req: CreateUserRequest,
    session: AsyncSession = Depends(get_session)
):
    """Create a new user"""
    # Check if user already exists
    existing_user = await TokenService.get_user_from_request(req, session)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    # Create new user
    user = User(
        id=uuid.uuid4(),
        email=req.email,
        created_at=datetime.utcnow()
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }

@router.get("/user")
async def get_user(
    user: Any = Depends(get_user_from_request)
):
    """Return the output of get_user_id_from_request for debugging"""
    return user

@router.post("/token")
async def create_token(
    req: CreateTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """Create a new hash-based token for user (legacy)"""
    try:
        return await TokenService.create_token(req, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/jwt-token")
async def create_jwt_token(
    req: CreateJWTTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """Create a new JWT token for user"""
    # Find user by email
    user = await TokenService.get_user_from_request(req, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Create JWT access token
    access_token = TokenUtils.create_access_token(
        user_id=user.id,
        email=user.email,
        scopes=req.scopes,
        expires_in_days=req.expires_in_days
    )
    # Create refresh token
    refresh_token = TokenUtils.create_refresh_token(
        user_id=user.id,
        expires_in_days=90
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": req.expires_in_days * 24 * 3600  # in seconds
    }

@router.post("/verify")
async def verify_token(
    req: VerifyTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """Verify a hash-based token and return user info (legacy)"""
    try:
        return await TokenService.verify_token(req, session)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/verify-jwt")
async def verify_jwt_token(req: VerifyJWTTokenRequest):
    """Verify a JWT token and return user info"""
    try:
        payload = TokenUtils.verify_access_token(req.token)
        return {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "scopes": payload["scopes"],
            "expires_at": datetime.fromtimestamp(payload["exp"])
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/refresh")
async def refresh_jwt_token(
    req: RefreshJWTTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """Refresh JWT token using refresh token"""
    try:
        # Verify refresh token
        payload = TokenUtils.verify_refresh_token(req.refresh_token)
        user_id = payload["user_id"]
        # Get user info using a simple object with user_id
        class UserIdRequest:
            def __init__(self, user_id):
                self.user_id = user_id
        
        user_req = UserIdRequest(user_id)
        user = await TokenService.get_user_from_request(user_req, session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Create new access token
        access_token = TokenUtils.create_access_token(
            user_id=user.id,
            email=user.email,
            expires_in_days=30
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 30 * 24 * 3600
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))