from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import glob
from app import get_current_user
from database import get_db
from models import User, Upload

router = APIRouter()

@router.get("/")
def admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    users = db.query(User).all()
    total_uploads = db.query(Upload).count()
    total_storage = sum(os.path.getsize(f) for f in glob.glob("uploads/*") if os.path.exists(f))
    premium_count = db.query(User).filter(User.is_premium == True).count()
    return {
        "users": [{"id": u.id, "username": u.username, "uploads_count": db.query(Upload).filter(Upload.user_id == u.id).count(), "is_premium": u.is_premium} for u in users],
        "stats": {
            "total_users": len(users),
            "total_uploads": total_uploads,
            "total_storage_gb": round(total_storage / (1024**3), 2),
            "premium_count": premium_count
        }
    }

@router.delete("/user/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        uploads = db.query(Upload).filter(Upload.user_id == user_id).all()
        for u in uploads:
            if u.file_url:
                os.remove(u.file_url)
            db.delete(u)
        db.delete(user)
        db.commit()
    return {"success": True}
