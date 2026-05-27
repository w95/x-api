from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


def _location_str(loc) -> str:
    if isinstance(loc, dict):
        return loc.get("location") or ""
    return loc or ""


class UserOut(BaseModel):
    id: str
    username: str
    fullname: str
    bio: str = ""
    location: str = ""
    url: str = ""
    userPic: str = ""
    banner: str = ""
    followers: int = 0
    following: int = 0
    tweets: int = 0
    likes: int = 0
    media: int = 0
    listed: int = 0
    verified: bool = False
    blue: bool = False
    protected: bool = False
    joinDate: Optional[datetime] = None
    pinnedTweetIds: List[str] = []

    @classmethod
    def from_twscrape(cls, u) -> "UserOut":
        return cls(
            id=u.id_str,
            username=u.username,
            fullname=u.displayname or "",
            bio=u.rawDescription or "",
            location=_location_str(u.location),
            url=u.url or "",
            userPic=u.profileImageUrl or "",
            banner=u.profileBannerUrl or "",
            followers=u.followersCount or 0,
            following=u.friendsCount or 0,
            tweets=u.statusesCount or 0,
            likes=u.favouritesCount or 0,
            media=u.mediaCount or 0,
            listed=u.listedCount or 0,
            verified=bool(u.verified),
            blue=bool(u.blue),
            protected=bool(u.protected),
            joinDate=u.created,
            pinnedTweetIds=[str(i) for i in (u.pinnedIds or [])],
        )


class MediaOut(BaseModel):
    kind: str
    url: str
    thumb: str = ""
    altText: str = ""


class TweetOut(BaseModel):
    id: str
    url: str
    user: UserOut
    text: str = ""
    lang: str = ""
    date: Optional[datetime] = None
    replies: int = 0
    retweets: int = 0
    likes: int = 0
    quotes: int = 0
    views: int = 0
    bookmarks: int = 0
    conversationId: Optional[str] = None
    inReplyToTweetId: Optional[str] = None
    inReplyToUsername: Optional[str] = None
    hashtags: List[str] = []
    cashtags: List[str] = []
    mentions: List[str] = []
    links: List[str] = []
    media: List[MediaOut] = []
    quote: Optional["TweetOut"] = None
    retweet: Optional["TweetOut"] = None

    @classmethod
    def from_twscrape(cls, t) -> "TweetOut":
        media: List[MediaOut] = []
        if t.media:
            for p in t.media.photos or []:
                media.append(MediaOut(kind="photo", url=p.url, altText=getattr(p, "altText", "") or ""))
            for v in t.media.videos or []:
                best = ""
                if getattr(v, "variants", None):
                    best = max(v.variants, key=lambda x: (getattr(x, "bitrate", 0) or 0)).url
                media.append(MediaOut(kind="video", url=best or "", thumb=getattr(v, "thumbnailUrl", "") or ""))
            for g in t.media.animated or []:
                media.append(MediaOut(kind="gif", url=g.videoUrl or "", thumb=getattr(g, "thumbnailUrl", "") or ""))

        return cls(
            id=t.id_str,
            url=t.url,
            user=UserOut.from_twscrape(t.user),
            text=t.rawContent or "",
            lang=t.lang or "",
            date=t.date,
            replies=t.replyCount or 0,
            retweets=t.retweetCount or 0,
            likes=t.likeCount or 0,
            quotes=t.quoteCount or 0,
            views=t.viewCount or 0,
            bookmarks=t.bookmarkedCount or 0,
            conversationId=t.conversationIdStr,
            inReplyToTweetId=t.inReplyToTweetIdStr,
            inReplyToUsername=t.inReplyToScreenName,
            hashtags=[h if isinstance(h, str) else h.text for h in (t.hashtags or [])],
            cashtags=[c if isinstance(c, str) else c.text for c in (t.cashtags or [])],
            mentions=[m.username for m in (t.mentionedUsers or [])],
            links=[l if isinstance(l, str) else l.url for l in (t.links or [])],
            media=media,
            quote=cls.from_twscrape(t.quotedTweet) if t.quotedTweet else None,
            retweet=cls.from_twscrape(t.retweetedTweet) if t.retweetedTweet else None,
        )


TweetOut.model_rebuild()


class TimelinePage(BaseModel):
    user: UserOut
    tweets: List[TweetOut]
    count: int


class SearchResponse(BaseModel):
    kind: str = "tweets"
    query: str
    tweets: List[TweetOut]
    count: int
