import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, BigInteger, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class VideoStatus(str, enum.Enum):
    """Video processing status"""
    PROCESSING = "processing"  # Uploading or processing thumbnails
    READY = "ready"  # Ready to stream
    FAILED = "failed"  # Processing failed
    DELETED = "deleted"  # Soft deleted


class Video(Base):
    """Video model for storing video metadata"""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Video metadata
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)  # Path to video file
    file_size = Column(BigInteger, nullable=True)  # File size in bytes
    thumbnail_path = Column(String(500), nullable=True)  # Path to selected thumbnail

    # Video properties
    duration = Column(Integer, nullable=True)  # Duration in seconds
    width = Column(Integer, nullable=True)  # Video width in pixels
    height = Column(Integer, nullable=True)  # Video height in pixels
    fps = Column(Float, nullable=True)  # Frames per second
    codec = Column(String(50), nullable=True)  # Video codec
    bitrate = Column(Integer, nullable=True)  # Bitrate in kbps

    # Processing status
    status = Column(Enum(VideoStatus), default=VideoStatus.PROCESSING, nullable=False, index=True)

    # View count
    view_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    uploader = relationship("User", back_populates="videos")
    thumbnails = relationship("VideoThumbnail", back_populates="video", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="video_tags", back_populates="videos")
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    category = relationship("Category", back_populates="videos")

    def __repr__(self):
        return f"<Video(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def is_ready(self) -> bool:
        """Check if video is ready to stream"""
        return self.status == VideoStatus.READY

    @property
    def is_processing(self) -> bool:
        """Check if video is being processed"""
        return self.status == VideoStatus.PROCESSING
