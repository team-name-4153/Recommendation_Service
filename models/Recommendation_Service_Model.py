from dataclasses import dataclass
import datetime
from typing import Optional, List
import json


@dataclass
class StreamTag:
    tag_id: int
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
    stop_watching_time: Optional[datetime.datetime] = None
    watch_duration: int
    


# DB schema 
'''
CREATE TABLE streaming_session (
    session_id INT PRIMARY KEY,
    streamer_id INT NOT NULL,
    game VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    start_time DATETIME NOT NULL,
    end_time DATETIME
);

CREATE TABLE stream_tag (
    tag_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    tag_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (session_id) REFERENCES streaming_session(session_id)
);

CREATE TABLE viewing_session (
    viewing_session_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    user_id INT NOT NULL,
    stop_watching_time DATETIME,
    watch_duration INT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES streaming_session(session_id)
);
'''