from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tag(Base):
    """Tag model for video categorization and search"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Color for UI display (hex color)
    color = Column(String(7), default="#3B82F6", nullable=False)  # Default: blue-500

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    videos = relationship("Video", secondary="video_tags", back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name}, slug={self.slug})>"

    @property
    def video_count(self) -> int:
        """Get number of videos with this tag"""
        return len(self.videos)
