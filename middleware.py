from fastapi import Request, Response
from sqlalchemy.orm import Session
import json
from database import get_db  # Import from database.py
import models

class AnalyticsMiddleware:
    def __init__(self, app):
        self.app = app

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(("/api/upload", "/api/v2")) and request.method in ["POST", "GET"]:
            db: Session = next(get_db())
            try:
                user_id = getattr(request.state.user, 'id', None) if hasattr(request.state, 'user') else None
                details = json.dumps({"path": str(request.url), "method": request.method})
                analytic = models.Analytics(user_id=user_id, event_type="api_call", details=details)
                db.add(analytic)
                db.commit()
            except:
                pass  # Silent fail
        return response
