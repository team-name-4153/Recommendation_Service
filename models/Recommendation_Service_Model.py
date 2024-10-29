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
    duration: float

