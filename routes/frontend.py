from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
import uuid
from app import templates
from utils import create_access_token, get_password_hash, verify_password, get_current_user
from database import get_db
from models import User, Upload

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_post(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or not verify_password(password, db_user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    token = create_access_token({"sub": username})
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
async def signup_post(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username taken"})
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email taken"})
    profile_photo_url = None
    if profile_photo:
        item_id = int(uuid.uuid4().int % (10**9))
        ext = profile_photo.filename.split('.')[-1] if '.' in profile_photo.filename else 'jpg'
        profile_photo_url = f"uploads/profile_{item_id}.{ext}"
        contents = await profile_photo.read()
        with open(profile_photo_url, "wb") as f:
            f.write(contents)

    hashed_pw = get_password_hash(password)
    api_key = str(uuid.uuid4())
    new_user = User(
        name=name,
        username=username,
        email=email,
        password_hash=hashed_pw,
        api_key=api_key,
        profile_photo=profile_photo_url
    )
    db.add(new_user)
    db.commit()
    token = create_access_token({"sub": username})
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id).all()
    import glob
    storage_used = sum(os.path.getsize(f) for f in glob.glob(f"uploads/*_{current_user.id}_*") if os.path.exists(f))
    analytics_data = {
        "labels": ["Uploads", "API Calls"],
        "datasets": [{"data": [len(uploads), 5]}]
    }
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "uploads": uploads,
        "storage_used": storage_used,
        "analytics": analytics_data
    })

@router.get("/admin", response_class=HTMLResponse)
def admin_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    users = db.query(User).all()
    import glob
    total_storage = sum(os.path.getsize(f) for f in glob.glob("uploads/*") if os.path.exists(f))
    stats = {
        "total_users": len(users),
        "total_uploads": db.query(Upload).count(),
        "total_storage_gb": round(total_storage / (1024**3), 2),
        "premium_count": db.query(User).filter(User.is_premium == True).count()
    }
    analytics_data = {
        "labels": ["Premium", "Free"],
        "datasets": [{"data": [stats["premium_count"], stats["total_users"] - stats["premium_count"]]}]
    }
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "stats": stats,
        "analytics": analytics_data
    })

@router.get("/guide", response_class=HTMLResponse)
def guide_page(request: Request):
    return templates.TemplateResponse("guide.html", {"request": request})

@router.get("/user-docs", response_class=HTMLResponse)
def docs_page(request: Request):
    return templates.TemplateResponse("user-docs.html", {"request": request})

@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response
