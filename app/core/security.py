import bcrypt
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.core.redis_client import redis_client
import logging
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# Cache password verification results for performance (5 second cache)
CACHE_TTL = 5

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with salt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


async def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify plain password against hashed password (runs in thread pool).
    ⚡ Non-blocking bcrypt verification for better performance
    
    Args:
        plain: Plain text password from user
        hashed: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        pwd_bytes = plain.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        # Run bcrypt in thread pool to avoid blocking
        return await run_in_threadpool(bcrypt.checkpw, pwd_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional custom expiry duration
        
    Returns:
        JWT access token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT refresh token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional custom expiry duration
        
    Returns:
        JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload dict, or None if invalid
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Token validation error: {str(e)}")
        return None


async def increment_failed_login(identifier: str) -> int:
    """
    Increment failed login attempts counter.
    Resets after 15 minutes.
    
    Args:
        identifier: Phone or email
        
    Returns:
        Current attempt count
    """
    key = f"login_fail:{identifier}"
    attempts = await redis_client.incr(key)
    
    # Set expiry on first attempt (15 minutes = 900 seconds)
    if attempts == 1:
        await redis_client.expire(key, 900)
    
    logger.info(f"Failed login attempt {attempts} for {identifier}")
    return attempts


async def is_blocked(identifier: str) -> bool:
    """
    Check if user account is blocked due to too many failed login attempts.
    Blocks after 5 failed attempts for 15 minutes.
    
    Args:
        identifier: Phone or email
        
    Returns:
        True if blocked, False otherwise
    """
    key = f"login_fail:{identifier}"
    attempts = await redis_client.get(key)
    blocked = int(attempts or 0) >= 5
    
    if blocked:
        logger.warning(f"Account locked for {identifier} - {attempts} failed attempts")
    
    return blocked


async def blacklist_token(token: str, expires_in: int):
    """
    Blacklist token to invalidate it for logout.
    
    Args:
        token: JWT token to blacklist
        expires_in: Token expiry time in seconds
    """
    try:
        await redis_client.setex(f"blacklist:{token}", expires_in, "true")
        logger.info("Token blacklisted for logout")
    except Exception as e:
        logger.error(f"Blacklist token error: {str(e)}")


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted.
    
    Args:
        token: JWT token to check
        
    Returns:
        True if blacklisted, False otherwise
    """
    return await redis_client.exists(f"blacklist:{token}") > 0
