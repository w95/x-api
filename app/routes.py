from fastapi import APIRouter, Depends, HTTPException, Query
from twscrape import API

from .deps import get_api
from .models import SearchResponse, TimelinePage, TweetOut, UserOut

router = APIRouter()


@router.get("/user/{name}", response_model=UserOut)
async def get_user(name: str, api: API = Depends(get_api)) -> UserOut:
    u = await api.user_by_login(name)
    if u is None:
        raise HTTPException(404, f'User "{name}" not found')
    return UserOut.from_twscrape(u)


@router.get("/user/{name}/tweets", response_model=TimelinePage)
async def get_user_tweets(
    name: str,
    limit: int = Query(20, ge=1, le=200),
    include_replies: bool = Query(False),
    api: API = Depends(get_api),
) -> TimelinePage:
    u = await api.user_by_login(name)
    if u is None:
        raise HTTPException(404, f'User "{name}" not found')

    source = api.user_tweets_and_replies(u.id, limit=limit) if include_replies else api.user_tweets(u.id, limit=limit)
    tweets: list[TweetOut] = []
    async for t in source:
        tweets.append(TweetOut.from_twscrape(t))
        if len(tweets) >= limit:
            break
    return TimelinePage(user=UserOut.from_twscrape(u), tweets=tweets, count=len(tweets))


@router.get("/tweet/{tweet_id}", response_model=TweetOut)
async def get_tweet(tweet_id: int, api: API = Depends(get_api)) -> TweetOut:
    t = await api.tweet_details(tweet_id)
    if t is None:
        raise HTTPException(404, f"Tweet {tweet_id} not found")
    return TweetOut.from_twscrape(t)


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(20, ge=1, le=200),
    api: API = Depends(get_api),
) -> SearchResponse:
    tweets: list[TweetOut] = []
    async for t in api.search(q, limit=limit):
        tweets.append(TweetOut.from_twscrape(t))
        if len(tweets) >= limit:
            break
    return SearchResponse(query=q, tweets=tweets, count=len(tweets))
