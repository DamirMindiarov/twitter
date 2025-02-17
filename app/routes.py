import os
import random
from contextlib import asynccontextmanager
from typing import Optional, Union

import aiofiles
from fastapi import FastAPI, Request, UploadFile, Response, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database import engine_async
from app.db_models import Base, UsersDB, TweetsDB, MediaDB
from app.functions import get_user, del_media, get_tweet, get_media
from app.routes_models import (
    UserOut,
    TweetOut,
    TweetIn,
    Result,
    TweetsBand,
    TweetsForBand,
    Author,
    Likes,
    Following,
    Followers,
    Medias,
)


async def create_db():
    async with engine_async.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session() -> async_sessionmaker:
    return async_sessionmaker(bind=engine_async, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/api/users/me")
async def func_1(
    request: Request, async_session: async_sessionmaker = Depends(get_session)
) -> UserOut:
    """Получает header Api-Key, добавляет его в таблицу Users,
    если пользователь с таким именем существует - возвращает его данные"""
    api_key = request.headers.get("Api-Key")

    async with async_session() as session:
        user_info = await get_user(username=api_key, session=session)
        if not user_info:
            user_info = UsersDB(name=api_key, followers=[], following=[])
            session.add(user_info)
            await session.commit()

    user = UserOut(user=user_info.to_dict())
    return user


@app.get("/api/users/{user_id}")
async def func_2(
    user_id: int, async_session: async_sessionmaker = Depends(get_session)
) -> UserOut | None:
    """Получить пользователя по его id"""
    async with async_session() as session:
        user = await get_user(session=session, user_id=user_id)

    return UserOut(user=user.to_dict()) if user else None


@app.post("/api/tweets", status_code=201)
async def func_3(
    request: Request,
    tweet: TweetIn,
    async_session: async_sessionmaker = Depends(get_session),
) -> TweetOut | None:
    """Добавляет твит в БД"""
    username = request.headers.get("Api-Key")

    async with async_session() as session:
        user = await get_user(username=username, session=session)

        if not user:
            return None

        tw = TweetsDB(
            tweet_data=tweet.tweet_data,
            tweet_media_ids=tweet.tweet_media_ids,
            user_id=user.id,
            likes=[],
        )
        await session.refresh(user)
        user.tweets.append(tw)
        await session.commit()

    return TweetOut(tweet_id=user.tweets[-1].id) if user else None


@app.get("/api/tweets")
async def func_4(
    request: Request, async_session: async_sessionmaker = Depends(get_session)
) -> TweetsBand | None:
    """Возвращает ленту твитов"""
    username = request.headers.get("Api-Key")

    async with async_session() as session:
        user = await get_user(username=username, session=session)

        if not user:
            return None

        list_id_following_users = [json["id"] for json in user.following]

        all_tw = await session.execute(
            select(TweetsDB).order_by(
                TweetsDB.user_id.in_(list_id_following_users).desc(),
                func.cardinality(TweetsDB.likes).desc(),
            )
        )
        all_tweets = all_tw.scalars().all()

        tweet_band = TweetsBand(tweets=[])
        for tweet in all_tweets:
            tweet_for_band = TweetsForBand(
                id=tweet.id,
                content=tweet.tweet_data,
                attachments=[
                    "/api/medias/{id_media}".format(id_media=i)
                    for i in tweet.tweet_media_ids
                ],
                author=Author(id=tweet.user_id, name=tweet.user.name),
                likes=[Likes(**like_info) for like_info in tweet.likes],
            )
            tweet_band.tweets.append(tweet_for_band)

    return tweet_band


@app.post("/api/medias", status_code=201)
async def func_5(
    file: UploadFile, async_session: async_sessionmaker = Depends(get_session)
) -> Medias | None:
    """Сохраняет полученное изображение, добавляет в БД его название"""
    filename: str | None = file.filename
    if filename:
        path = os.path.join("db", "images", filename)

        while os.path.isfile(path):
            fn = os.path.splitext(os.path.basename(path))[0]
            add = f"{random.randint(0, 9)}"
            path = path.replace(fn, fn + add)
            filename = os.path.basename(path)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        async with aiofiles.open(path, "wb") as out_file:
            image = await file.read()
            await out_file.write(image)

    async with async_session() as session:
        media = MediaDB(filename=os.path.basename(filename))

        if not media:
            return None

        session.add(media)
        await session.commit()

    return Medias(media_id=media.id)


@app.get("/api/medias/{id_media}", status_code=200)
async def func_6(
    id_media: int, async_session: async_sessionmaker = Depends(get_session)
) -> Response:
    """Возвращает изображение по его id"""
    async with async_session() as session:
        file = await get_media(media_id=id_media, session=session)

        if not file:
            return Response()

        filename = file.filename

    async with aiofiles.open(
        os.path.join("db", "images", filename), "rb"
    ) as out_file:
        image = await out_file.read()

    return Response(content=image)


class TweetIndexError(Exception):
    """Исключение о том, что у пользователя нет твита
    к которому он хочет обратиться"""

    def __init__(self, name: str):
        self.name = name
        self.type = "TweetIndexError"


@app.delete("/api/tweets/{tweet_id}", status_code=200)
async def func_7(
    request: Request,
    tweet_id: int,
    async_session: async_sessionmaker = Depends(get_session),
) -> Result | None:
    """Удаляет твит из БД"""
    async with async_session() as session:
        username = request.headers.get("Api-Key")
        user = await get_user(username=username, session=session)

        if not user:
            return None

        await session.refresh(user)

        for tweet in user.tweets:
            if tweet.id == tweet_id:
                await session.execute(
                    delete(TweetsDB).where(TweetsDB.id == tweet_id)
                )
                filenames = [
                    await del_media(media_id, session=session)
                    for media_id in tweet.tweet_media_ids
                ]
                for filename in filenames:
                    if filename:
                        path = os.path.join("db", "images", filename)
                        os.remove(path)
                break
        else:
            raise TweetIndexError(name="У пользователя нет твита с таким id")
        await session.commit()

    return Result()


@app.post("/api/tweets/{tweet_id}/likes", status_code=201)
async def func_8(
    request: Request,
    tweet_id: int,
    async_session: async_sessionmaker = Depends(get_session),
) -> Result | None:
    """Добавляет лайк к твиту"""
    username = request.headers.get("Api-Key")

    async with async_session() as session:
        user = await get_user(username=username, session=session)

        if not user:
            return None

        tweet = await get_tweet(tweet_id=tweet_id, session=session)

        if not tweet:
            return None

        tweet.likes.append({"user_id": user.id, "name": user.name})

        await session.execute(
            update(TweetsDB)
            .where(TweetsDB.id == tweet_id)
            .values(likes=tweet.likes)
        )
        await session.commit()

    return Result()


@app.delete("/api/tweets/{tweet_id}/likes")
async def func_9(
    request: Request,
    tweet_id: int,
    async_session: async_sessionmaker = Depends(get_session),
) -> Result | None:
    """Удаляет лайк из твита"""
    username = request.headers.get("Api-Key")

    async with async_session() as session:
        user = await get_user(username=username, session=session)

        if not user:
            return None

        tweet = await get_tweet(tweet_id=tweet_id, session=session)

        if not tweet:
            return None

        tweet.likes.remove({"user_id": user.id, "name": user.name})

        await session.execute(
            update(TweetsDB)
            .where(TweetsDB.id == tweet_id)
            .values(likes=tweet.likes)
        )
        await session.commit()

    return Result()


@app.post("/api/users/{user_id}/follow", status_code=201)
async def func_10(
    request: Request,
    user_id: int,
    async_session: async_sessionmaker = Depends(get_session),
) -> Result | None:
    """Пользователь подписывается на другого(обновляется информация о
    подписках в БД)
    У пользователя на которого подписались, обновляется информация о
    его подписчиках в БД
    """
    username = request.headers.get("Api-Key")

    async with async_session() as session:
        user_1 = await get_user(username=username, session=session)
        user_2 = await get_user(user_id=user_id, session=session)

        if not user_1 or not user_2:
            return None

        user_1.following.append(
            Following(id=user_2.id, name=user_2.name).__dict__
        )
        await session.execute(
            update(UsersDB)
            .where(UsersDB.id == user_1.id)
            .values(following=user_1.following)
        )

        user_2.followers.append(
            Followers(id=user_1.id, name=user_1.name).__dict__
        )
        await session.execute(
            update(UsersDB)
            .where(UsersDB.id == user_2.id)
            .values(followers=user_2.followers)
        )
        await session.commit()

    return Result()


@app.delete("/api/users/{user_id}/follow")
async def func_11(
    request: Request,
    user_id: int,
    async_session: async_sessionmaker = Depends(get_session),
) -> Result | None:
    """Пользователь отписывается от другого(обновляется информация о
    подписках в БД)
    У пользователя от которого отписались, обновляется информация о
    его подписчиках в БД
    """
    username = request.headers.get("Api-Key")

    async with async_session() as session:
        user_1 = await get_user(username=username, session=session)
        user_2 = await get_user(user_id=user_id, session=session)

        if not user_1 or not user_2:
            return None

        user_1.following.remove(
            Following(id=user_2.id, name=user_2.name).__dict__
        )
        await session.execute(
            update(UsersDB)
            .where(UsersDB.id == user_1.id)
            .values(following=user_1.following)
        )

        user_2.followers.remove(
            Followers(id=user_1.id, name=user_1.name).__dict__
        )
        await session.execute(
            update(UsersDB)
            .where(UsersDB.id == user_2.id)
            .values(followers=user_2.followers)
        )
        await session.commit()

    return Result()


@app.exception_handler(TweetIndexError)
def func_12(exc: TweetIndexError, *args, **kwargs) -> JSONResponse:
    """Возвращает тип и сообщение исключения TweetIndexError"""
    return JSONResponse(
        status_code=400,
        content={
            "result": "false",
            "error_type": exc.type,
            "error_message": exc.name,
        },
    )


@app.exception_handler(Exception)
def func_13(exc: Exception, *args, **kwargs) -> JSONResponse:
    """Возвращает тип и сообщение исключения"""
    return JSONResponse(
        status_code=400,
        content={
            "result": "false",
            "error_type": repr(exc),
            "error_message": str(exc),
        },
    )
