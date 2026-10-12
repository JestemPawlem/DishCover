from functools import lru_cache

from pydantic import computed_field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_user: str = 'postgres'
    db_password: SecretStr = SecretStr('postgres')
    db_host: str = 'localhost'
    db_port: int = 5432
    db_name: str = 'recipes_db'
    db_url: str | None = None

    jwt_secret_key: SecretStr = SecretStr('insecure-dev-secret-change-in-production')
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 60

    dummy_password_hash: str = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

    @computed_field
    def sync_database_url(self) -> str:
        if self.db_url:
            return self.db_url
        raw_password = self.db_password.get_secret_value()
        return f'postgresql://{self.db_user}:{raw_password}@{self.db_host}:{self.db_port}/{self.db_name}'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()