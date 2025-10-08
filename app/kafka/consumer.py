import asyncio
from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.db.postgres import AsyncSessionLocal
from app.models.event import Event
import json

consumer: AIOKafkaConsumer | None = None
task: asyncio.Task | None = None


async def start_kafka_consumer():
    global consumer, task
    consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_broker,
        value_deserializer=lambda v: json.loads(v.value.decode("utf-8")),
        enable_auto_commit=True,
        auto_offset_reset="earliest"
    )
    await consumer.start()

    task = asyncio.create_task(consume_messages())


async def stop_kafka_consumer():
    global consumer, task
    if consumer:
        await consumer.stop()
        consumer = None
    if task:
        task.cancel()
        task = None


async def save_to_db(data: dict):
    async with AsyncSessionLocal() as session:
        event = Event(
            event_type=data.get("event_type"),
            payload=json.dumps(data.get("payload")) if data.get("payload") else None
        )
        session.add(event)
        await session.commit()


async def consume_messages():
    global consumer
    async for msg in consumer:
        try:
            await save_to_db(msg)
        except Exception as e:
            print(f"Ошибка при обработке сообщения: {e}")