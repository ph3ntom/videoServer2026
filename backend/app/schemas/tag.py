from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class TagBase(BaseModel):
    """Base schema for Tag"""
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")
    color: str = Field("#3B82F6", pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")

    @validator('name')
    def validate_name(cls, v):
        """Validate tag name - alphanumeric, spaces, hyphens only"""
        if not re.match(r'^[\w\s\-가-힣]+$', v):
            raise ValueError('Tag name can only contain letters, numbers, spaces, hyphens, and Korean characters')
        return v.strip()


class TagCreate(TagBase):
    """Schema for creating a new tag"""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not re.match(r'^[\w\s\-가-힣]+$', v):
                raise ValueError('Tag name can only contain letters, numbers, spaces, hyphens, and Korean characters')
            return v.strip()
        return v


class TagResponse(TagBase):
    """Schema for tag response"""
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    video_count: int = Field(0, description="Number of videos with this tag")

    class Config:
        from_attributes = True


class TagSimple(BaseModel):
    """Simplified tag schema for embedding in other responses"""
    id: int
    name: str
    slug: str
    color: str

    class Config:
        from_attributes = True


class VideoTagCreate(BaseModel):
    """Schema for adding tags to a video"""
    tag_ids: list[int] = Field(..., min_items=1, max_items=10, description="List of tag IDs to add")


class VideoTagUpdate(BaseModel):
    """Schema for updating video tags (replace all)"""
    tag_ids: list[int] = Field(..., max_items=10, description="List of tag IDs (replaces existing)")
