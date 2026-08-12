from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine: AsyncEngine = create_async_engine(settings.postgres_dsn, echo=settings.sql_echo)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    # Импорт внутри функции, а не наверху файла: models/event.py сам импортирует
    # отсюда Base, и на уровне модуля вышел бы циклический импорт.
    from app.models import event
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI: одна сессия на запрос.
    """
    async with AsyncSessionLocal() as session:
        yield session
