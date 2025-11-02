from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
from ..app import get_db, create_access_token, get_password_hash
from ..models import User

router = APIRouter()

class UserSignup(BaseModel):
    name: str
    username: str
    email: str
    password: str
    profile_photo: str = None

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/signup")
@router.app.state.limiter.limit("5/minute")
def signup(user: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username taken")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email taken")
    hashed_pw = get_password_hash(user.password)
    api_key = str(uuid.uuid4())
    new_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        password_hash=hashed_pw,
        api_key=api_key,
        profile_photo=user.profile_photo,
        is_premium=False,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "api_key": api_key, "token_type": "bearer"}

@router.post("/login")
@router.app.state.limiter.limit("10/minute")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "api_key": db_user.api_key, "token_type": "bearer"}

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "username": current_user.username,
        "email": current_user.email,
        "api_key": current_user.api_key,
        "is_premium": current_user.is_premium,
        "profile_photo": current_user.profile_photo
    }

@router.post("/upgrade")
def upgrade(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.is_premium = True
    current_user.storage_limit = 999999999999  # Effectively unlimited
    db.commit()
    return {"message": "Upgraded to premium! Contact WhatsApp +91 8011971924 for payment confirmation."}