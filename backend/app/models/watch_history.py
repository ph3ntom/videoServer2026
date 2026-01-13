from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class WatchHistory(Base):
    """Watch history model for tracking video playback progress"""
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)

    # Playback position (in seconds)
    watch_position = Column(Integer, nullable=False, default=0)

    # Total watch duration (in seconds)
    watch_duration = Column(Integer, nullable=False, default=0)

    # Completion status (true if watched >= 90%)
    completed = Column(Boolean, default=False, nullable=False)

    # Timestamps
    last_watched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="watch_history")
    video = relationship("Video", backref="watch_history")

    # Constraints
    __table_args__ = (
        # 한 사용자는 한 비디오에 하나의 시청 기록만 유지
        UniqueConstraint('user_id', 'video_id', name='uq_user_video_watch_history'),
    )

    def __repr__(self):
        return f"<WatchHistory(id={self.id}, user_id={self.user_id}, video_id={self.video_id}, position={self.watch_position})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate watch progress percentage"""
        if not self.video or not self.video.duration or self.video.duration == 0:
            return 0.0
        return min(100.0, (self.watch_position / self.video.duration) * 100.0)
