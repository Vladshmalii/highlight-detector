from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.core.enum import VideoStatus, GameType

Base = declarative_base()


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    game_type = Column(Enum(GameType), nullable=False)
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False)
    highlights = Column(JSON, default=list)
    video_metadata = Column(JSON, default=dict)
    total_events = Column(Integer, default=0)
    processing_time = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)