from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class VideoThumbnail(Base):
    """Video thumbnail model"""
    __tablename__ = "video_thumbnails"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    is_auto_generated = Column(Boolean, default=True, nullable=False)
    is_selected = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)

    # Relationship
    video = relationship("Video", back_populates="thumbnails")

    def __repr__(self):
        return f"<VideoThumbnail(id={self.id}, video_id={self.video_id}, is_selected={self.is_selected})>"
