"""Authentication and security utilities."""
from datetime import datetime, timedelta
from typing import Optional
import uuid
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import UserDB
from config.settings import settings

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)

# JWT settings
SECRET_KEY = settings.secret_key if hasattr(settings, 'secret_key') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserCreate(BaseModel):
    """User creation model."""
    email: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt."""
    try:
        # Convert string password to bytes
        password_bytes = plain_password.encode('utf-8')
        # Convert stored hash to bytes if it's a string
        if isinstance(hashed_password, str):
            hash_bytes = hashed_password.encode('utf-8')
        else:
            hash_bytes = hashed_password
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt. Truncates to 72 bytes for bcrypt compatibility."""
    # Bcrypt has a 72 byte limit - truncate password if necessary
    password_bytes = password.encode('utf-8')[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string for database storage
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_user(db: Session, user_create: UserCreate) -> UserDB:
    """Create a new user."""
    # Check if user exists
    existing_user = db.query(UserDB).filter(UserDB.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = UserDB(
        user_id=f"user_{uuid.uuid4().hex[:16]}",
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        full_name=user_create.full_name,
        is_active=1
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[UserDB]:
    """Authenticate a user."""
    user = db.query(UserDB).filter(UserDB.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[UserDB]:
    """Get the current authenticated user from JWT token."""
    if not token:
        return None
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = db.query(UserDB).filter(UserDB.user_id == token_data.user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: Optional[UserDB] = Depends(get_current_user)
) -> UserDB:
    """Get the current active user (raises exception if not authenticated)."""
    if current_user is None or not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or inactive user"
        )
    
    return current_user


def get_current_user_optional(
    current_user: Optional[UserDB] = Depends(get_current_user)
) -> Optional[UserDB]:
    """Get the current user if authenticated, None otherwise (no exception)."""
    return current_user


def get_company_id_from_token(token: str = Depends(oauth2_scheme)) -> Optional[str]:
    """Extract company_id from JWT token."""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("company_id")
    except JWTError:
        return None


def get_user_role_from_token(token: str = Depends(oauth2_scheme)) -> Optional[str]:
    """Extract role from JWT token."""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role")
    except JWTError:
        return None


def require_role(allowed_roles: list[str]):
    """
    Dependency to require specific roles.
    
    Usage:
        @app.get("/admin", dependencies=[Depends(require_role(["owner"]))])
    """
    def role_checker(
        current_user: UserDB = Depends(get_current_active_user),
        role: Optional[str] = Depends(get_user_role_from_token)
    ):
        if not role or role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user
    
    return role_checker


def enforce_tenant_isolation(
    company_id: str,
    token_company_id: Optional[str] = Depends(get_company_id_from_token)
):
    """
    Verify that the requested company_id matches the token's company_id.
    
    Prevents cross-tenant data access.
    """
    if not token_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Company context required"
        )
    
    if company_id != token_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access data from different company"
        )
    
    return True

