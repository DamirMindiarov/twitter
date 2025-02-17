from pydantic import BaseModel


class Result(BaseModel):
    result: str = "true"


class Followers(BaseModel):
    id: int
    name: str


class Following(BaseModel):
    id: int
    name: str


class User(BaseModel):
    id: int
    name: str
    followers: list[Followers]
    following: list[Following]


class UserOut(Result):
    user: User


class TweetIn(BaseModel):
    tweet_data: str
    tweet_media_ids: list[int]


class Tweet(TweetIn):
    user_id: int


class TweetOut(Result):
    tweet_id: int


class Attachments(BaseModel):
    link_media: str


class Author(BaseModel):
    id: int
    name: str


class Likes(BaseModel):
    user_id: int
    name: str


class TweetsForBand(BaseModel):
    id: int
    content: str
    attachments: list[str]
    author: Author
    likes: list[Likes]


class TweetsBand(Result):
    tweets: list[TweetsForBand]


class Medias(Result):
    media_id: int
