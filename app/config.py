from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FastAPI Template"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    kafka_broker: str
    kafka_topic: str
    kafka_group: str = "default-group"

    sql_echo: bool = False

    @property
    def postgres_dsn(self) -> str:
        """Строка подключения собирается из частей, а не задаётся отдельно.

        quote_plus нужен для пароля со спецсимволами: "p@ss/word" без
        экранирования разорвёт строку подключения по "@" и "/".

        "+asyncpg" выбирает драйвер. Без него SQLAlchemy возьмёт синхронный
        psycopg2, и асинхронный движок не заведётся.
        """
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return f"postgresql+asyncpg://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
