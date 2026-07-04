"""
auth.py
-------------
Authentication & Role-Based Access Control (RBAC).

Responsibilities:
- Hash / verify passwords (bcrypt via passlib)
- Create & decode JWT access tokens (python-jose)
- FastAPI dependencies:
    get_current_user   -> validates JWT, loads the User from DB
    require_role(...)  -> factory that restricts an endpoint to given roles
"""

import os
from datetime import datetime, timedelta
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User, RoleEnum

# ---------------------------------------------------------------------
# Config (in production, keep SECRET_KEY only in environment variables /
# a secrets manager -- never hard-code it or commit it to git)
# ---------------------------------------------------------------------
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_super_secret_hackathon_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Points Swagger UI / clients at the /login endpoint for the auth flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ---------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT containing `data` plus an expiry claim."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode & validate a JWT. Raises JWTError if invalid/expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ---------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Decodes the bearer token from the Authorization header, looks up the
    user in the DB, and returns it. Used as a dependency on any protected
    route: `current_user: User = Depends(get_current_user)`.
    """
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def require_role(*allowed_roles: RoleEnum):
    """
    Dependency factory for RBAC.

    Usage:
        @router.get("/dashboard")
        def dashboard(user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.ANALYST))):
            ...

    Any authenticated user whose role is NOT in `allowed_roles` gets a 403.
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role.value}' is not permitted to "
                    f"access this resource. Required: "
                    f"{[r.value for r in allowed_roles]}"
                ),
            )
        return current_user

    return role_checker
