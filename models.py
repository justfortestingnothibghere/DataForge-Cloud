from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    api_key = Column(String, unique=True, index=True)
    profile_photo = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    storage_limit = Column(Integer, default=1073741824)  # 1GB
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    uploads = relationship("Upload", back_populates="owner")

class Upload(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # text, image, video, document
    file_url = Column(String, nullable=True)
    content = Column(Text, nullable=True)  # for text
    share_token = Column(String, nullable=True)  # for sharing
    share_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="uploads")

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String)  # upload, api_call, etc.
    details = Column(Text)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)