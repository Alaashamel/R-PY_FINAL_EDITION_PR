from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password, handling legacy or malformed hashes gracefully."""
    if not hashed_password or not isinstance(hashed_password, str):
        return False
    
    # Normalize hash: remove escape characters and fix common corruption
    cleaned = hashed_password.strip().replace('\\', '').replace('/$/', '$')
    
    # If cleaned hash doesn't start with standard bcrypt prefix, try to recover
    if not cleaned.startswith('$2'):
        # Try to prepend missing bcrypt prefix if it looks like base64-like hash
        # Bcrypt hashes are 60 chars: $2b$12$<22 chars salt><31 chars hash>
        if len(cleaned) >= 53 and '$' not in cleaned:
            # Maybe it's a raw bcrypt hash missing the `$2b$12$` prefix
            # Without knowing the exact cost, assume $2b$12$ (standard)
            # But we can't reliably reconstruct - better to rehash on next login
            pass
    
    try:
        return pwd_context.verify(plain_password, cleaned)
    except Exception:
        # If verification fails with cleaned hash, try original
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
