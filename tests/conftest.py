import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from starlette.routing import _DefaultLifespan

from app.db_models import UsersDB, Base
from app.routes import app, get_session

docker_db = """
docker run --name database 
-e POSTGRES_USER=admin 
-e POSTGRES_PASSWORD=admin 
-e POSTGRES_DB=twitter 
-v ./db:/var/lib/postgresql/data -d 
--network nw -p 5433:5432 postgres
"""

db_url_async = "postgresql+asyncpg://admin:admin@localhost:5433/twitter"
db_url_sync = "postgresql+psycopg2://admin:admin@localhost:5433/twitter"
engine_async = create_async_engine(url=db_url_async)
engine_sync = create_engine(url=db_url_sync)
session = sessionmaker(bind=engine_sync)()


def new_get_session():
    return async_sessionmaker(bind=engine_async, expire_on_commit=False)


app.dependency_overrides[get_session] = new_get_session

@pytest.fixture(scope="module")
def client():
    app.router.lifespan_context = _DefaultLifespan(app.router)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def clear_db():
    Base.metadata.create_all(bind=engine_sync)
    session.add(UsersDB(name="user001", followers=[], following=[]))
    session.commit()
    yield
    Base.metadata.drop_all(bind=engine_sync)