from fastapi import Request, Response
from sqlalchemy.orm import Session
import json
from database import get_db
import models

class AnalyticsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Create a Request object from the scope
        request = Request(scope, receive=receive)
        # Call the next middleware or application
        response = await self.app(scope, receive, send)
        
        # Apply analytics logic for specific API endpoints
        if request.url.path.startswith(("/api/upload", "/api/v2")) and request.method in ["POST", "GET"]:
            db: Session = next(get_db())
            try:
                user_id = getattr(request.state, 'user_id', None) if hasattr(request.state, 'user_id') else None
                details = json.dumps({"path": str(request.url), "method": request.method})
                analytic = models.Analytics(user_id=user_id, event_type="api_call", details=details)
                db.add(analytic)
                db.commit()
            except Exception:
                pass  # Silent fail
        return response
