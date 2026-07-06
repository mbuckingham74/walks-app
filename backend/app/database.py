import functools
import logging

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


async def dispose_engine():
    await engine.dispose()
