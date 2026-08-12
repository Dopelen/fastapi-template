from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_producer
from app.config import settings
from app.db.postgres import get_session
from app.kafka.producer import KafkaProducer
from app.models.event import Event
from app.schemas.event import (
    EventInputSchema,
    EventKafkaProducerSchema,
    EventResponse,
    SendResponse,
    StatusResponse,
)

router = APIRouter()


@router.get("/", response_model=StatusResponse)
async def root():
    return StatusResponse(status="Ok")


@router.post("/send", response_model=SendResponse)
async def send_test_message(
    event: EventInputSchema,
    producer: KafkaProducer = Depends(get_producer),
):
    kafka_event = EventKafkaProducerSchema(**event.model_dump())
    try:
        await producer.send(settings.kafka_topic, kafka_event)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return SendResponse(status="sent", event=kafka_event)


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """
    Последние события из базы.
    limit и offset ограничены сверху.
    """
    result = await session.execute(
        select(Event).order_by(Event.id.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())
