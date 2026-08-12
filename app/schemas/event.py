from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    """
    Время в UTC со смещением.
    """
    return datetime.now(timezone.utc)


class EventInputSchema(BaseModel):
    """Что присылает клиент в POST /send."""
    event_type: str = "test_event"
    payload: str | None = None


class EventKafkaProducerSchema(EventInputSchema):
    """Что уходит в Kafka: то же самое плюс отметка времени."""
    created_at: datetime = Field(default_factory=utcnow)


class EventResponse(BaseModel):
    """Что отдаёт GET /events.
    from_attributes разрешает собирать модель прямо из ORM-объекта,
    без ручного перекладывания полей.
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: str
    payload: str | None
    created_at: datetime


class StatusResponse(BaseModel):
    status: str


class SendResponse(BaseModel):
    status: str
    event: EventKafkaProducerSchema
