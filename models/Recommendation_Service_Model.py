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
class StreamTag:
    session_id: int # foreign key
    tag_name: str

@dataclass
class StreamingSession:
    session_id: int
    streamer_id: int
    game: str
    title: str
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None

@dataclass
class ViewingSession:
    session_id: int # foreign key
    user_id: int
    session_id: str
    stop_watching_time: Optional[datetime.datetime] = None
    watch_duration: int
    


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