"""
Обвязка тестов.
Инфраструктура не нужна: база подменяется на SQLite в памяти, а приложение
собирается из роутера напрямую, без lifespan - значит Kafka не поднимается
и подключаться никуда не надо.
"""

import os

# Настройки читаются при импорте app.config, а .env в репозитории нет - он
# в .gitignore. Значения проставляются здесь, до любого импорта из app,
# иначе Settings() упадёт на отсутствующих полях.
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("KAFKA_BROKER", "localhost:9092")
os.environ.setdefault("KAFKA_TOPIC", "test_topic")

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.routers import router
from app.db.postgres import Base, get_session
from app.models import event


@pytest.fixture
async def session_factory():
    # StaticPool нужен, чтобы все соединения смотрели в одну и ту же базу:
    # у SQLite ":memory:" своя база на каждое соединение.
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
async def client(session_factory):
    """Приложение собирается здесь, а не импортируется из app.main.

    Так тесты не запускают lifespan: не нужны ни Kafka, ни настоящая база.
    """
    application = FastAPI()
    application.include_router(router)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    application.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


class FakeProducer:
    """Заглушка вместо настоящего клиента Kafka: запоминает отправленное."""

    def __init__(self):
        self.sent = []

    async def send(self, topic, value, key=None):
        self.sent.append((topic, value))


@pytest.fixture
async def client_with_fake_producer(session_factory):
    """То же приложение, но с подставленным producer в app.state.

    Так выглядит выигрыш от переноса клиентов в state: заглушка кладётся
    рядом с приложением, без monkeypatch на модуль и без global.
    """
    application = FastAPI()
    application.include_router(router)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    application.dependency_overrides[get_session] = override_get_session

    fake = FakeProducer()
    application.state.kafka_producer = fake

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client, fake
