import os
import hashlib
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkeyformini-netflix-recommendation")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 Hours
SALT = "mini-netflix-salt-12345"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password: str) -> str:
    """
    Standard, robust salted SHA-256 password hash.
    Avoids passlib / bcrypt binary mismatch errors on Windows.
    """
    return hashlib.sha256((password + SALT).encode('utf-8')).hexdigest()

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency to get the current user. Returns the guest user if no token is supplied,
    allowing seamless Guest Mode navigation.
    """
    if not token or token == "undefined" or token == "null":
        # Return Guest User
        guest = db.query(User).filter(User.email == "guest@netflix.com").first()
        if not guest:
            # Create guest if not found
            guest = User(
                name="Guest User",
                email="guest@netflix.com",
                password_hash=get_password_hash("guest123"),
                preferred_genres=["Comedy", "Action"],
                preferred_languages=["English"],
                preferred_actors=[],
                preferred_directors=[],
                preferred_runtime="90-120 mins",
                preferred_mood="Feel-good"
            )
            db.add(guest)
            db.commit()
            db.refresh(guest)
        return guest

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired, please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
