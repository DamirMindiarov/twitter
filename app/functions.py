from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import UsersDB, MediaDB, TweetsDB


async def get_user(
    session: AsyncSession,
    username: str | None = None,
    user_id: int | None = None,
) -> UsersDB | None:
    """Делает запрос к БД, возвращает объект пользователя"""
    if username:
        user = await session.execute(
            select(UsersDB).where(UsersDB.name == username)
        )
    else:
        user = await session.execute(
            select(UsersDB).where(UsersDB.id == user_id)
        )
    return user.scalar()


async def del_media(media_id: int, session: AsyncSession) -> str | None:
    """Удаляет запись в БД об изображении"""
    filename = await session.execute(
        delete(MediaDB)
        .where(MediaDB.id == media_id)
        .returning(MediaDB.filename)
    )
    return filename.scalars().one_or_none()


async def get_tweet(tweet_id: int, session: AsyncSession) -> TweetsDB | None:
    tweet = await session.execute(
        select(TweetsDB).where(TweetsDB.id == tweet_id)
    )
    return tweet.scalar()


async def get_media(media_id: int, session: AsyncSession) -> MediaDB | None:
    media = await session.execute(
        select(MediaDB).where(MediaDB.id == media_id)
    )
    return media.scalar()
