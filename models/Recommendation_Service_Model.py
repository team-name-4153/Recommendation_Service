from dataclasses import dataclass
import datetime
from typing import Optional, List
import json


@dataclass
class StreamTag:
    session_id: int # foreign key
    tag_name: str
    # (session_id, tag_name) is the primary key

@dataclass
class StreamSession:
    session_id: int
    streamer_id: int
    game: str
    title: str
    start_time: datetime.datetime
    hls_folder: str
    end_time: Optional[datetime.datetime] = None

@dataclass
class ViewSession:
    viewing_session_id: int # primary key
    user_id: int
    session_id: int # foreign key
    watch_duration: int
    stop_watching_time: Optional[int] = None # in second
    


# DB schema 
'''
CREATE TABLE stream_session (
    session_id INT AUTO_INCREMENT,
    streamer_id INT NOT NULL,
    game VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    hls_folder VARCHAR(255) NOT NULL,
    PRIMARY KEY (session_id, streamer_id)
);

CREATE TABLE stream_tag (
    session_id INT NOT NULL,
    tag_name VARCHAR(255) NOT NULL,
    PRIMARY KEY (session_id, tag_name),
    FOREIGN KEY (session_id) REFERENCES stream_session(session_id)
);

CREATE TABLE view_session (
    viewing_session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    stop_watching_time INT,
    watch_duration INT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES stream_session(session_id)
);

'''