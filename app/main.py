from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.kafka.consumer import start_kafka_consumer, stop_kafka_consumer, consume_messages, task
from app.kafka.producer import start_kafka_producer, stop_kafka_producer
from app.api.routers import router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_kafka_producer()
    await start_kafka_consumer()
    yield
    task.cancel()
    await task
    await stop_kafka_consumer()
    await stop_kafka_producer()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router)