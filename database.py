from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Env vars
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://todo_99ka_user:tPR9uvBxr27EADVUolBJ10emUPK8FMxh@dpg-d3qmgf0gjchc73bfnnng-a/todo_99ka")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
