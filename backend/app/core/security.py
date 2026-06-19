import secrets
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from jose import jwt
from passlib.context import CryptContext  # type: ignore

from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# For production, move this to settings
SECRET_KEY = settings.API_KEY if hasattr(settings, "API_KEY") else "dev-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials - Invalid API Key",
        )
    return api_key


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
