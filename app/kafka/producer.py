import asyncio
from aiokafka import AIOKafkaProducer
import json
from aiokafka.errors import KafkaConnectionError
from pydantic import BaseModel

from app.config import settings


producer: AIOKafkaProducer | None = None

async def start_kafka_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_broker,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    for attempt in range(10):
        try:
            await producer.start()
            print("Kafka producer started!")
            return
        except KafkaConnectionError:
            print(f"Kafka not ready, retrying {attempt + 1}/10...")
            await asyncio.sleep(3)
    raise RuntimeError("Could not connect to Kafka")


async def stop_kafka_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None


async def send_message(topic: str, value: BaseModel | dict, key: str = None):
    """Отправка сообщения в Kafka, сериализация только один раз"""
    if not producer:
        raise RuntimeError("Kafka producer not started")

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")

    print(f"Sending to Kafka: {value}")
    await producer.send_and_wait(topic, value=value, key=key.encode() if key else None)