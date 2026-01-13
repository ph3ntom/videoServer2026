from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RatingBase(BaseModel):
    """Base rating schema"""
    score: int = Field(..., ge=1, le=5, description="Rating score from 1 to 5")


class RatingCreate(RatingBase):
    """Schema for creating a rating"""
    pass


class RatingUpdate(RatingBase):
    """Schema for updating a rating"""
    pass


class RatingResponse(RatingBase):
    """Schema for rating response"""
    id: int
    user_id: int
    video_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoRatingStats(BaseModel):
    """Schema for video rating statistics"""
    avg_rating: float = Field(0.0, description="Average rating score")
    rating_count: int = Field(0, description="Total number of ratings")
    user_rating: int | None = Field(None, description="Current user's rating (if logged in)")

    model_config = ConfigDict(from_attributes=True)
