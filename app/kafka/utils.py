"""Общее для producer и consumer."""

import asyncio
import logging

from aiokafka.errors import KafkaConnectionError

logger = logging.getLogger(__name__)

RETRIES = 10
DELAY_SECONDS = 3


async def start_with_retries(client, name: str) -> None:
    """
    Запускает клиента Kafka, переживая недоступность брокера так как Kafka поднимается дольше приложения.
    """
    for attempt in range(1, RETRIES + 1):
        try:
            await client.start()
            logger.info("%s подключён к Kafka", name)
            return
        except KafkaConnectionError:
            logger.warning("Kafka недоступна, попытка %s/%s для %s", attempt, RETRIES, name)
            await asyncio.sleep(DELAY_SECONDS)

    raise RuntimeError(f"{name}: не удалось подключиться к Kafka за {RETRIES} попыток")
