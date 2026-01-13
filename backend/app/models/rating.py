from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Rating(Base):
    """Rating model for video ratings (1-5 stars)"""
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)

    # Rating score (1-5)
    score = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="ratings")
    video = relationship("Video", backref="ratings")

    # Constraints
    __table_args__ = (
        # 한 사용자는 한 비디오에 하나의 평점만 등록 가능
        UniqueConstraint('user_id', 'video_id', name='uq_user_video_rating'),
        # 평점은 1-5 사이만 허용
        CheckConstraint('score >= 1 AND score <= 5', name='check_rating_score'),
    )

    def __repr__(self):
        return f"<Rating(id={self.id}, user_id={self.user_id}, video_id={self.video_id}, score={self.score})>"
