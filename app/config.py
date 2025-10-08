from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    app_name: str
    app_host: str
    app_port: int

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    kafka_broker: str
    kafka_topic: str
    kafka_group: str = "default-group"

    postgres_dsn: str

    class Config:
        env_file = "example.env"

settings = Settings()