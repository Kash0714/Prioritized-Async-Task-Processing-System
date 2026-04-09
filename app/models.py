import uuid
from sqlalchemy import Column, String, Integer, JSON
from app.db import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payload = Column(JSON)
    priority = Column(String)
    status = Column(String, default="PENDING")
    retry_count = Column(Integer, default=0)
    last_error = Column(String, nullable=True)