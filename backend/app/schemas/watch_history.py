from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class WatchHistoryBase(BaseModel):
    """Base watch history schema"""
    watch_position: int = Field(..., ge=0, description="Current playback position in seconds")


class WatchHistoryCreate(WatchHistoryBase):
    """Schema for creating/updating watch history"""
    watch_duration: int = Field(0, ge=0, description="Total watch duration in seconds")


class WatchHistoryUpdate(BaseModel):
    """Schema for updating watch history"""
    watch_position: int = Field(..., ge=0, description="Current playback position in seconds")
    watch_duration: int = Field(0, ge=0, description="Total watch duration in seconds")


class WatchHistoryResponse(WatchHistoryBase):
    """Schema for watch history response"""
    id: int
    user_id: int
    video_id: int
    watch_duration: int
    completed: bool
    progress_percentage: float = Field(description="Watch progress percentage (0-100)")
    last_watched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContinueWatchingItem(BaseModel):
    """Schema for continue watching list item"""
    video_id: int
    video_title: str
    video_description: str | None
    video_duration: int | None
    video_thumbnail_path: str | None
    uploader_username: str
    watch_position: int
    progress_percentage: float
    last_watched_at: datetime

    model_config = ConfigDict(from_attributes=True)
