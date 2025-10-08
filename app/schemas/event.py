from datetime import datetime
from pydantic import BaseModel, model_validator


class EventInputSchema(BaseModel):
    event_type: str = "test_event"
    payload: str | None = None


class EventKafkaProducerSchema(EventInputSchema):
    created_at: datetime | None = None

    @model_validator(mode="before")
    def set_created_at(cls, values):
        values["created_at"] = datetime.utcnow()
        return values

