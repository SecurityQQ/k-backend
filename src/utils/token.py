import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..core.config import settings

class TokenUtils:
    """Utility class for token encoding and decoding operations"""
    
    @staticmethod
    def generate_raw_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def encode_jwt_token(
        payload: Dict[str, Any],
        expires_in_days: int = 30
    ) -> str:
        """Encode a JWT token with payload and expiration"""
        
        # Add expiration time
        payload["exp"] = datetime.utcnow() + timedelta(days=expires_in_days)
        payload["iat"] = datetime.utcnow()
        
        # Encode token
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token
    
    @staticmethod
    def decode_jwt_token(token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
        scopes: Optional[list[str]] = None,
        expires_in_days: int = None
    ) -> str:
        """Create an access token with user information"""
        
        if expires_in_days is None:
            expires_in_days = settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS
        
        payload = {
            "user_id": str(user_id),
            "email": email,
            "scopes": scopes or [],
            "type": "access"
        }
        
        return TokenUtils.encode_jwt_token(payload, expires_in_days)
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """Verify and decode an access token"""
        payload = TokenUtils.decode_jwt_token(token)
        
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        
        return payload
    
    @staticmethod
    def create_refresh_token(
        user_id: str,
        expires_in_days: int = None
    ) -> str:
        """Create a refresh token"""
        
        if expires_in_days is None:
            expires_in_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        
        payload = {
            "user_id": str(user_id),
            "type": "refresh"
        }
        
        return TokenUtils.encode_jwt_token(payload, expires_in_days)
    
    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """Verify and decode a refresh token"""
        payload = TokenUtils.decode_jwt_token(token)
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        return payload