from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, JSON, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    pass


class UsersDB(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    followers: Mapped[list] = mapped_column(ARRAY(JSON))
    following: Mapped[list] = mapped_column(ARRAY(JSON))

    tweets: Mapped[list["TweetsDB"]] = relationship(
        "TweetsDB", back_populates="user", uselist=True, lazy="selectin"
    )

    def __str__(self):
        return f"{self.name=} {self.following=} {self.followers=}"


class TweetsDB(Base):
    __tablename__ = "tweets"
    id: Mapped[int] = mapped_column(primary_key=True)
    tweet_data: Mapped[str]
    tweet_media_ids: Mapped[list[int]] = mapped_column(ARRAY(INTEGER))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    likes: Mapped[list[dict]] = mapped_column(ARRAY(JSONB))

    user: Mapped["UsersDB"] = relationship(
        "UsersDB", back_populates="tweets", uselist=False, lazy="selectin"
    )

    def __str__(self):
        return f"{self.id=} {self.tweet_data=} {self.tweet_media_ids=} {self.user_id=} {self.likes=}"


class MediaDB(Base):
    __tablename__ = "medias"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
