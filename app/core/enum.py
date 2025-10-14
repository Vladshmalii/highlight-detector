from enum import Enum

class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GameType(str, Enum):
    CS2 = "cs2"
    DOTA2 = "dota2"


class EventType(str, Enum):
    KILL = "kill"
    MULTI_KILL = "multi_kill"
    CLUTCH = "clutch"
    ACE = "ace"
    TEAMFIGHT = "teamfight"
    RAMPAGE = "rampage"
    OBJECTIVE = "objective"