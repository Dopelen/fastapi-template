import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, TopicPartition

from app.config import settings
from app.db.postgres import AsyncSessionLocal
from app.kafka.utils import start_with_retries
from app.models.event import Event

logger = logging.getLogger(__name__)


class KafkaConsumer:
    """
    Чтение сообщений из Kafka и запись их в базу.
    Экземпляр хранится в app.state, а не в глобальных переменных модуля.
    """

    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_broker,
            group_id=settings.kafka_group,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await start_with_retries(self._consumer, "consumer")
        self._task = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        """
        Сначала снимаем задачу, потом закрываем consumer.
        Наоборот нельзя - задача в этот момент итерируется по нему и получит
        ошибку вместо штатной отмены.
        """
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._consumer is not None:
            await self._consumer.stop()
            logger.info("Consumer остановлен")
            self._consumer = None

    async def _consume(self) -> None:
        logger.info("Consumer слушает топик %s", settings.kafka_topic)
        try:
            async for msg in self._consumer:
                try:
                    await save_to_db(msg.value)
                    logger.info("Сохранено сообщение %s", msg.offset)
                except Exception:
                    logger.exception("Не удалось обработать сообщение %s, пропускаем", msg.offset)
                await self._consumer.commit(
                    {TopicPartition(msg.topic, msg.partition): msg.offset + 1}
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Цикл чтения Kafka остановлен из-за ошибки")
            raise


async def save_to_db(data: dict) -> None:
    async with AsyncSessionLocal() as session:
        session.add(Event(event_type=data.get("event_type"), payload=data.get("payload")))
        await session.commit()
