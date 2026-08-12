from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Event(Base):
    """
    Событие, прочитанное потребителем из Kafka.
    """
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payload: Mapped[str | None] = mapped_column(String, nullable=True)
    # nullable=False добавлен намеренно.
    # схема ответа объявляет created_at обязательным
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
