from fastapi.templating import Jinja2Templates
import os

# Templates
templates = Jinja2Templates(directory="templates")

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)
