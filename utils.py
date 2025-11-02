import uuid
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from passlib.context import CryptContext
from bcrypt import hashpw, gensalt, checkpw
import os
from datetime import datetime, timedelta
from database import get_db
import models

# Env vars
SECRET_KEY = os.getenv("SECRET_KEY", str(uuid.uuid4()))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# JWT utils
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    request: Request = None,
    db: Session = Depends(get_db)
):
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def api_key_auth(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Authorization required")
    api_key = auth.split(" ")[1]
    user = db.query(models.User).filter(models.User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key")
    request.state.user = user  # Store for middleware
    return user
