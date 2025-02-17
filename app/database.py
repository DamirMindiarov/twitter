from sqlalchemy.ext.asyncio import (
    create_async_engine,
)

db_url_async = "postgresql+asyncpg://admin:admin@database:5432/twitter"

engine_async = create_async_engine(url=db_url_async)
