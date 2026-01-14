from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import statistics_service
from app.schemas.video import VideoListResponse
from pydantic import BaseModel


router = APIRouter()


class TopRatedVideoResponse(BaseModel):
    """Response schema for top rated video with statistics"""
    video: VideoListResponse
    avg_rating: float
    rating_count: int

    class Config:
        from_attributes = True


class StatisticsSummaryResponse(BaseModel):
    """Response schema for platform statistics summary"""
    total_videos: int
    total_views: int
    total_ratings: int
    average_rating: float

    class Config:
        from_attributes = True


@router.get("/popular", response_model=List[VideoListResponse])
async def get_popular_videos(
    limit: int = Query(default=10, ge=1, le=50, description="Number of videos to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get most popular videos by view count.

    Args:
        limit: Maximum number of videos to return (1-50, default: 10)
        db: Database session

    Returns:
        List of popular videos ordered by view count
    """
    videos = await statistics_service.get_popular_videos(db, limit=limit)

    # Convert to response format
    return [
        VideoListResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            file_size=video.file_size,
            thumbnail_path=video.thumbnail_path,
            duration=video.duration,
            width=video.width,
            height=video.height,
            status=video.status,
            view_count=video.view_count,
            created_at=video.created_at,
            uploader_username=video.uploader.username if video.uploader else None
        )
        for video in videos
    ]


@router.get("/top-rated", response_model=List[TopRatedVideoResponse])
async def get_top_rated_videos(
    limit: int = Query(default=10, ge=1, le=50, description="Number of videos to return"),
    min_ratings: int = Query(default=5, ge=1, le=100, description="Minimum number of ratings required"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top rated videos with minimum rating threshold.

    Args:
        limit: Maximum number of videos to return (1-50, default: 10)
        min_ratings: Minimum number of ratings required (1-100, default: 5)
        db: Database session

    Returns:
        List of top rated videos with rating statistics
    """
    top_rated = await statistics_service.get_top_rated_videos(
        db,
        limit=limit,
        min_ratings=min_ratings
    )

    # Convert to response format
    return [
        TopRatedVideoResponse(
            video=VideoListResponse(
                id=item["video"].id,
                title=item["video"].title,
                description=item["video"].description,
                file_size=item["video"].file_size,
                thumbnail_path=item["video"].thumbnail_path,
                duration=item["video"].duration,
                width=item["video"].width,
                height=item["video"].height,
                status=item["video"].status,
                view_count=item["video"].view_count,
                created_at=item["video"].created_at,
                uploader_username=item["video"].uploader.username if item["video"].uploader else None
            ),
            avg_rating=item["avg_rating"],
            rating_count=item["rating_count"]
        )
        for item in top_rated
    ]


@router.get("/summary", response_model=StatisticsSummaryResponse)
async def get_statistics_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall platform statistics summary.

    Args:
        db: Database session

    Returns:
        Platform statistics including total videos, views, and ratings
    """
    summary = await statistics_service.get_video_statistics_summary(db)
    return StatisticsSummaryResponse(**summary)
