from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from sqlalchemy.orm import Session
import os
import uuid
import glob
from datetime import datetime, timedelta
import zipfile
from io import BytesIO
from utils import get_current_user, api_key_auth
from database import get_db
from models import Upload, User, Analytics

router = APIRouter()

def check_quota(user: User, file_size: int, db: Session):
    if user.is_premium:
        return True
    current_storage = sum(os.path.getsize(f) for f in glob.glob(f"uploads/*_{user.id}_*") if os.path.exists(f))
    return current_storage + file_size <= user.storage_limit

@router.post("/upload")
async def upload(
    type_: str = Form(..., alias="type"),
    content: str = Form(None),
    file: UploadFile = File(None),
    share: bool = Form(False),
    ttl_hours: int = Form(24, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    if type_ not in ["text", "image", "video", "document"]:
        raise HTTPException(400, "Invalid type")
    if type_ == "text" and not content:
        raise HTTPException(400, "Content required for text")
    if type_ != "text" and not file:
        raise HTTPException(400, "File required")

    item_id = int(uuid.uuid4().int % (10**9))
    file_url = None
    share_link = None
    share_token = None
    share_expires_at = None

    if type_ != "text":
        contents = await file.read()
        if not check_quota(current_user, len(contents), db):
            raise HTTPException(403, "Storage limit exceeded. Upgrade to premium!")
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        file_url = f"uploads/{item_id}_{current_user.id}.{ext}"
        with open(file_url, "wb") as f:
            f.write(contents)
        if share:
            share_token = str(uuid.uuid4())
            share_expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            share_link = f"/api/share/{item_id}?token={share_token}"

    new_upload = Upload(
        user_id=current_user.id,
        type=type_,
        file_url=file_url,
        content=content if type_ == "text" else None,
        share_token=share_token,
        share_expires_at=share_expires_at
    )
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    # Log to analytics
    details = json.dumps({"upload_id": new_upload.id, "type": type_})
    db.add(Analytics(user_id=current_user.id, event_type="upload", details=details))
    db.commit()
    return {
        "success": True,
        "item_id": new_upload.id,
        "access_url": f"/api/v2/{current_user.username}?uploads={new_upload.id}",
        "share_link": share_link
    }

@router.get("/v2/{username}")
async def get_upload(
    username: str,
    uploads: int = Query(...),
    user = Depends(api_key_auth),
    db: Session = Depends(get_db)
):
    if user.username != username:
        raise HTTPException(403, "Access denied")
    upload = db.query(Upload).filter(Upload.id == uploads, Upload.user_id == user.id).first()
    if not upload:
        raise HTTPException(404, "Upload not found")
    response = {
        "owner": username,
        "type": upload.type,
        "created_at": upload.created_at.isoformat()
    }
    if upload.type == "text":
        response["content"] = upload.content
    else:
        response["file_url"] = f"/{upload.file_url}"
    return response

@router.get("/share/{item_id}")
def get_shared(item_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == item_id, Upload.share_token == token).first()
    if not upload or (upload.share_expires_at and upload.share_expires_at < datetime.utcnow()):
        raise HTTPException(404, "Share link invalid or expired")
    if upload.type == "text":
        return {"content": upload.content}
    return FileResponse(upload.file_url, filename=f"shared_{item_id}{os.path.splitext(upload.file_url)[1]}")

@router.delete("/delete/{item_id}")
def delete_upload(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upload = db.query(Upload).filter(Upload.id == item_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(404, "Upload not found")
    if upload.file_url and os.path.exists(upload.file_url):
        os.remove(upload.file_url)
    db.delete(upload)
    db.commit()
    return {"success": True}

@router.get("/analytics")
def get_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    uploads_count = db.query(Upload).filter(Upload.user_id == current_user.id).count()
    analytics = db.query(Analytics).filter(Analytics.user_id == current_user.id).all()
    storage_used = sum(os.path.getsize(f) for f in glob.glob(f"uploads/*_{current_user.id}_*") if os.path.exists(f))
    labels = [a.event_type for a in analytics[-10:]]
    counts = [1 for _ in labels]
    return {
        "uploads_count": uploads_count,
        "storage_used": storage_used,
        "labels": labels,
        "datasets": [{"data": counts}]
    }

@router.get("/export")
def export_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id).all()
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for upload in uploads:
            if upload.content:
                zip_file.writestr(f"{upload.id}.txt", upload.content)
            elif upload.file_url:
                zip_file.write(upload.file_url, f"{upload.id}{os.path.splitext(upload.file_url)[1]}")
    zip_buffer.seek(0)
    return FileResponse(zip_buffer, media_type="application/zip", filename="dataforge_export.zip")
