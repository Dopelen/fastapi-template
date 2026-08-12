import json
import logging

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from app.config import settings
from app.kafka.utils import start_with_retries

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Отправка сообщений в Kafka.
    Экземпляр класса хранится в app.state: состояние привязано к приложению, а не к модулю,
    и в тестах подменяется через dependency_overrides без возни с global.
    """

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_broker,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await start_with_retries(self._producer, "producer")

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            logger.info("Producer остановлен")
            self._producer = None

    async def send(self, topic: str, value: BaseModel | dict, key: str | None = None) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka producer not started")

        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")

        logger.info("Отправка в Kafka: %s", value)
        await self._producer.send_and_wait(topic, value=value, key=key.encode() if key else None)
