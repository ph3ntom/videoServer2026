from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagSimple
)
from app.services.tag_service import tag_service

router = APIRouter()


@router.post("/", response_model=TagSimple, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tag (authenticated users only)

    - **name**: Tag name (unique)
    - **description**: Optional description
    - **color**: Hex color code (default: #3B82F6)

    Returns TagSimple (without video_count) to avoid relationship loading issues
    """
    tag = await tag_service.create(db, tag_data)
    return tag


@router.get("/", response_model=List[TagResponse])
async def list_tags(
    skip: int = Query(0, ge=0, description="Number of tags to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of tags to return"),
    search: str = Query(None, description="Search query for tag name or description"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all tags

    - **skip**: Pagination offset
    - **limit**: Maximum number of results
    - **search**: Optional search query
    """
    tags = await tag_service.get_all(db, skip=skip, limit=limit, search=search)
    return tags


@router.get("/popular", response_model=List[TagResponse])
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=50, description="Number of popular tags to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get most popular tags (by video count)

    - **limit**: Number of tags to return
    """
    popular_tags = await tag_service.get_popular(db, limit=limit)

    # Convert to response format
    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            slug=tag.slug,
            description=tag.description,
            color=tag.color,
            created_at=tag.created_at,
            updated_at=tag.updated_at,
            video_count=count
        )
        for tag, count in popular_tags
    ]


@router.get("/search", response_model=List[TagSimple])
async def search_tags(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search tags for autocomplete

    - **q**: Search query
    - **limit**: Maximum number of results
    """
    tags = await tag_service.search_tags(db, q, limit=limit)
    return tags


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get tag by ID

    - **tag_id**: Tag ID
    """
    tag = await tag_service.get_by_id(db, tag_id)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    return tag


@router.get("/slug/{slug}", response_model=TagResponse)
async def get_tag_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get tag by slug

    - **slug**: Tag slug (URL-friendly identifier)
    """
    tag = await tag_service.get_by_slug(db, slug)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    return tag


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update tag (authenticated users only)

    - **tag_id**: Tag ID
    - **name**: New tag name (optional)
    - **description**: New description (optional)
    - **color**: New color (optional)
    """
    tag = await tag_service.get_by_id(db, tag_id)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    tag = await tag_service.update(db, tag, tag_data)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete tag (authenticated users only)

    - **tag_id**: Tag ID
    """
    tag = await tag_service.get_by_id(db, tag_id)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    await tag_service.delete(db, tag)
    return None
