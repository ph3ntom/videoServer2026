from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    """Category model for video organization"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Icon for UI display (emoji or icon name)
    icon = Column(String(50), default="📁", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    videos = relationship("Video", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, slug={self.slug})>"

    @property
    def video_count(self) -> int:
        """Get number of videos in this category"""
        return len(self.videos)
