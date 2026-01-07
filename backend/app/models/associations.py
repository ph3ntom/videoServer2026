from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

# Association table for Video-Tag many-to-many relationship
video_tags = Table(
    "video_tags",
    Base.metadata,
    Column("video_id", Integer, ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)
