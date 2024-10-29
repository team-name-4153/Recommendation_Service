from dataclasses import dataclass
import datetime

@dataclass
class Label:
    resource_id: int
    label: str


@dataclass
class WatchSession:
    user_id: int
    stream_id: int
    watch_start_time: datetime
    watch_end_time: datetime
    duration: float

