from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class VideoBase(BaseModel):
    """Base video schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class VideoCreate(VideoBase):
    """Schema for creating a video"""
    pass


class VideoUpdate(BaseModel):
    """Schema for updating a video"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class VideoResponse(VideoBase):
    """Schema for video response"""
    id: int
    user_id: int
    file_path: str
    file_size: Optional[int] = None
    thumbnail_path: Optional[str] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    status: str
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VideoListResponse(BaseModel):
    """Schema for video list response with uploader info"""
    id: int
    title: str
    description: Optional[str] = None
    file_size: Optional[int] = None
    thumbnail_path: Optional[str] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: str
    view_count: int
    created_at: datetime
    uploader_username: str

    model_config = ConfigDict(from_attributes=True)
