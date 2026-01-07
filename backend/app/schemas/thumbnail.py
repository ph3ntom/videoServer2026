from pydantic import BaseModel
from datetime import datetime


class ThumbnailBase(BaseModel):
    """Base thumbnail schema"""
    pass


class ThumbnailResponse(ThumbnailBase):
    """Thumbnail response schema"""
    id: int
    video_id: int
    file_path: str
    is_auto_generated: bool
    is_selected: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ThumbnailSelect(BaseModel):
    """Schema for selecting a thumbnail"""
    thumbnail_id: int
