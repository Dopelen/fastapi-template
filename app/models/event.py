from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.postgres import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String, index=True, nullable=False)
    payload = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())