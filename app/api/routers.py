from datetime import datetime

from fastapi import APIRouter
from app.config import settings
from app.kafka.producer import send_message
from app.schemas.event import EventKafkaProducerSchema, EventInputSchema

router = APIRouter()

@router.get("/")
async def root():
    return {"status": "Ok"}


@router.post("/send")
async def send_test_message(event: EventInputSchema):
    kafka_event = EventKafkaProducerSchema(**event.model_dump())
    await send_message(settings.kafka_topic, kafka_event)
    return {"status": "sent", "event": kafka_event.model_dump(mode="json")}