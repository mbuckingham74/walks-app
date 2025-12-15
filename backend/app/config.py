from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # MySQL
    mysql_host: str
    mysql_port: int = 3306
    mysql_user: str
    mysql_password: SecretStr
    mysql_database: str = "walks_tracker"

    # App
    debug: bool = False
    cors_origins: str = "http://localhost:5173"
    api_key: SecretStr = SecretStr("")  # Required for mutating endpoints

    # Business constants
    steps_per_mile: int = 2000
    daily_goal: int = 15000

    @property
    def database_url(self) -> URL:
        """Build database URL safely using URL.create.

        This properly handles special characters in passwords and avoids
        potential credential leakage in logs from f-string interpolation.
        """
        return URL.create(
            drivername="mysql+aiomysql",
            username=self.mysql_user,
            password=self.mysql_password.get_secret_value(),
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
        )

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "*" in origins:
            raise ValueError("CORS_ORIGINS cannot contain '*' when allow_credentials=True.")
        return origins

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
