from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from database import Base, get_db
import models  # Import after Base
from middleware import AnalyticsMiddleware
from utils import limiter  # Import limiter from utils
from routes.auth import router as auth_router
from routes.api import router as api_router
from routes.admin import router as admin_router
from routes.frontend import router as frontend_router

# FastAPI app
app = FastAPI(title="DataForge API")

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates & Static
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Apply middleware
app.add_middleware(AnalyticsMiddleware)

# Include routers
app.include_router(auth_router, prefix="/auth")
app.include_router(api_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")
app.include_router(frontend_router)

# WebSocket for real-time logs
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Real-time log: {data} at {datetime.now()}")
    except WebSocketDisconnect:
        pass

# Startup
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# Root for health
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "healthy"}
