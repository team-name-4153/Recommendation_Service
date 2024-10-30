from dataclasses import dataclass
import datetime
from typing import Optional, List
import json

# @dataclass
# class Label:
#     resource_id: int
#     label: str


# @dataclass
# class WatchSession:
#     user_id: int
#     stream_id: int
#     duration: float


@dataclass
class StreamingSession:
    session_id: str
    streamer_id: str
    game: str
    game_tags: List[str]  # Will be stored as JSON in DB
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    duration: Optional[int] = None  # in seconds

@dataclass
class ViewingSession:
    viewing_id: str
    user_id: str
    session_id: str
    start_watching_time: datetime.datetime
    end_watching_time: Optional[datetime.datetime] = None
    watch_duration: Optional[int] = None  # in seconds
    

@dataclass
class UserViewingPreference:
    user_id: str
    game: str
    streamer_id: str
    game_tags: List[str]  # Will be stored as JSON in DB
    total_watch_time: int = 0  # in seconds
    last_watched: Optional[datetime.datetime] = None
    watch_count: int = 0


# DB schema 
'''

CREATE TABLE streaming_sessions (
    session_id VARCHAR(36) PRIMARY KEY, -- streaming_id
    streamer_id VARCHAR(36) NOT NULL,
    game VARCHAR(100) NOT NULL,
    game_tags JSON,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    duration INT NULL
)

CREATE TABLE viewing_sessions (
    viewing_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    start_watching_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_watching_time TIMESTAMP NULL,
    watch_duration INT NULL,
    FOREIGN KEY (session_id) REFERENCES streaming_sessions(session_id)
)

CREATE TABLE user_viewing_preferences (
    user_id VARCHAR(36),
    game VARCHAR(100),
    streamer_id VARCHAR(36),
    game_tags JSON,
    total_watch_time INT DEFAULT 0,
    last_watched TIMESTAMP,
    watch_count INT DEFAULT 0,
    PRIMARY KEY (user_id, game, streamer_id)
)


'''