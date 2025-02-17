import os
import pytest


@pytest.mark.users
def test_create_user(client, clear_db):
    username = "user100"
    response = client.get("/api/users/me", headers={"Api-Key": username})
    user_id = response.json()["user"]["id"]

    assert response.status_code == 200
    assert response.json() == {
        "result": "true",
        "user": {
            "followers": [],
            "following": [],
            "id": user_id,
            "name": username,
        },
    }


@pytest.mark.users
def test_get_user_by_id(client, clear_db):
    response = client.get(
        "/api/users/1",
    )
    assert response.status_code == 200
    assert response.json() == {
        "result": "true",
        "user": {
            "followers": [],
            "following": [],
            "id": 1,
            "name": "user001",
        },
    }


@pytest.mark.tweets
def test_add_tweet(client, clear_db):
    tweet = {"tweet_data": "message", "tweet_media_ids": []}
    response = client.post(
        "/api/tweets", json=tweet, headers={"Api-Key": "user001"}
    )

    assert response.status_code == 201
    assert response.json() == {"result": "true", "tweet_id": 1}


@pytest.mark.media
def test_save_media(client, clear_db):
    dir_name = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dir_name, "image_test.jpg")
    # with open(os.path.join(dir_name, "image_test.jpg"), "rb") as file:
    #     image = file.read()

    response = client.post("/api/medias", files={"file": open(path, 'rb')})

    assert response.status_code == 201
    assert response.json() == {"result": "true", "media_id": 1}



@pytest.mark.media
def test_add_tweet_with_media(client, clear_db):
    dir_name = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dir_name, "image_test.jpg")

    res = client.post("/api/medias", files={"file": open(path, 'rb')})
    media_id = res.json()["media_id"]

    tweet = {"tweet_data": "message", "tweet_media_ids": [media_id]}
    response = client.post(
        "/api/tweets", json=tweet, headers={"Api-Key": "user001"}
    )

    assert response.status_code == 201
    assert response.json() == {"result": "true", "tweet_id": 1}


@pytest.mark.tweets
def test_get_all_tweets(client, clear_db):
    dir_name = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dir_name, "image_test.jpg")

    res = client.post("/api/medias", files={"file": open(path, 'rb')})
    media_id = res.json()["media_id"]

    tweet = {"tweet_data": "message", "tweet_media_ids": [media_id]}
    client.post("/api/tweets", json=tweet, headers={"Api-Key": "user001"})

    response = client.get("/api/tweets", headers={"Api-Key": "user001"})

    assert response.status_code == 200
    assert response.json() == {
        "result": "true",
        "tweets": [
            {
                "id": 1,
                "content": "message",
                "attachments": [f"/api/medias/{media_id}"],
                "author": {"id": 1, "name": "user001"},
                "likes": [],
            }
        ],
    }


@pytest.mark.likes
def test_add_like(client, clear_db):
    tweet = {"tweet_data": "message", "tweet_media_ids": []}
    client.post("/api/tweets", json=tweet, headers={"Api-Key": "user001"})

    response = client.post(
        "/api/tweets/1/likes", headers={"Api-Key": "user001"}
    )

    assert response.status_code == 201
    assert response.json() == {"result": "true"}

    tweets = client.get("/api/tweets", headers={"Api-Key": "user001"})

    assert tweets.json() == {
        "result": "true",
        "tweets": [
            {
                "id": 1,
                "content": "message",
                "attachments": [],
                "author": {"id": 1, "name": "user001"},
                "likes": [{"user_id": 1, "name": "user001"}],
            }
        ],
    }


@pytest.mark.likes
def test_remove_like(client, clear_db):
    test_add_like(client, clear_db)
    response = client.delete(
        "/api/tweets/1/likes", headers={"Api-Key": "user001"}
    )

    assert response.status_code == 200
    assert response.json() == {"result": "true"}

    tweets = client.get("/api/tweets", headers={"Api-Key": "user001"})

    assert tweets.json() == {
        "result": "true",
        "tweets": [
            {
                "id": 1,
                "content": "message",
                "attachments": [],
                "author": {"id": 1, "name": "user001"},
                "likes": [],
            }
        ],
    }


@pytest.mark.follow
def test_follow(client, clear_db):
    new_user = "kate"
    client.get("/api/users/me", headers={"Api-Key": new_user})

    response = client.post(
        "/api/users/1/follow", headers={"Api-Key": new_user}
    )

    assert response.status_code == 201
    assert response.json() == {"result": "true"}

    user = client.get("/api/users/1")
    new_user = client.get("/api/users/2")

    assert user.json() == {
        "result": "true",
        "user": {
            "id": 1,
            "name": "user001",
            "followers": [{"id": 2, "name": "kate"}],
            "following": [],
        },
    }
    assert new_user.json() == {
        "result": "true",
        "user": {
            "id": 2,
            "name": "kate",
            "followers": [],
            "following": [{"id": 1, "name": "user001"}],
        },
    }


@pytest.mark.follow
def test_remove_follow(client, clear_db):
    test_follow(client, clear_db)

    response = client.delete(
        "/api/users/1/follow", headers={"Api-Key": "kate"}
    )
    user = client.get("/api/users/1")
    new_user = client.get("/api/users/2")

    assert response.status_code == 200
    assert response.json() == {"result": "true"}
    assert user.json() == {
        "result": "true",
        "user": {"id": 1, "name": "user001", "followers": [], "following": []},
    }
    assert new_user.json() == {
        "result": "true",
        "user": {"id": 2, "name": "kate", "followers": [], "following": []},
    }


@pytest.mark.tweets
def test_sort_all_tweets(client, clear_db):
    # add 2 tweets from user001
    tweet = {"tweet_data": "message", "tweet_media_ids": []}
    client.post("/api/tweets", json=tweet, headers={"Api-Key": "user001"})
    client.post("/api/tweets", json=tweet, headers={"Api-Key": "user001"})

    # add kate and tweet from kate
    client.get("/api/users/me", headers={"Api-Key": "kate"})
    client.post("/api/tweets", json=tweet, headers={"Api-Key": "kate"})

    # kate follow user001
    client.post("/api/users/1/follow", headers={"Api-Key": "kate"})

    # kate like tweet(id = 1, user = user001)
    client.post("/api/tweets/1/likes", headers={"Api-Key": "kate"})

    response = client.get("/api/tweets", headers={"Api-Key": "kate"})

    assert response.status_code == 200
    assert response.json() == {
        "result": "true",
        "tweets": [
            {
                "id": 1,
                "content": "message",
                "attachments": [],
                "author": {"id": 1, "name": "user001"},
                "likes": [{"user_id": 2, "name": "kate"}],
            },
            {
                "id": 2,
                "content": "message",
                "attachments": [],
                "author": {"id": 1, "name": "user001"},
                "likes": [],
            },
            {
                "id": 3,
                "content": "message",
                "attachments": [],
                "author": {"id": 2, "name": "kate"},
                "likes": [],
            },
        ],
    }
