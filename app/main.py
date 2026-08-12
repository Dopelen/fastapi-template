import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import router
from app.config import settings
from app.db.postgres import init_db
from app.kafka.consumer import KafkaConsumer
from app.kafka.producer import KafkaProducer

# Без этой строки logger.info из наших модулей не виден: uvicorn настраивает
# только свои логгеры, а у корневого нет обработчика, и сообщения уходят в никуда.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.kafka_producer = KafkaProducer()
    await app.state.kafka_producer.start()
    app.state.kafka_consumer = KafkaConsumer()
    await app.state.kafka_consumer.start()

    yield

    await app.state.kafka_consumer.stop()
    await app.state.kafka_producer.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    # Запуск с машины: python -m app.main
    import uvicorn
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
