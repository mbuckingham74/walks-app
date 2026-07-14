import functools
import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = None
async_session = None


def init_engine():
    global engine, async_session
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=False,
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def retry_on_connection_error(max_retries: int = 1):
    """Decorator to retry async DB operations on connection errors.

    aiomysql has known incompatibility with SQLAlchemy's pool_pre_ping,
    so we retry on OperationalError to handle stale connections.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except OperationalError as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.warning(
                            f"DB connection error (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying: {e}"
                        )
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # create_all() does not modify existing columns. Upgrade persistent
        # installations that originally created these cache values as TEXT.
        result = await conn.execute(text("""
            SELECT TABLE_NAME, DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND COLUMN_NAME = 'stats_json'
              AND TABLE_NAME IN ('stats_cache', 'detailed_stats_cache')
        """))
        column_types = {row[0]: row[1].lower() for row in result.all()}
        migrations = {
            "stats_cache": text(
                "ALTER TABLE stats_cache MODIFY COLUMN stats_json MEDIUMTEXT NOT NULL"
            ),
            "detailed_stats_cache": text(
                "ALTER TABLE detailed_stats_cache "
                "MODIFY COLUMN stats_json MEDIUMTEXT NOT NULL"
            ),
        }
        for table_name, statement in migrations.items():
            if column_types.get(table_name) not in {"mediumtext", "longtext"}:
                logger.info("Upgrading %s.stats_json to MEDIUMTEXT", table_name)
                await conn.execute(statement)


async def dispose_engine():
    await engine.dispose()
