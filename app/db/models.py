from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Ban(Base):
    __tablename__ = "bans"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    status = Column(String, default="banned")
    unbanned_at = Column(DateTime, nullable=True)