from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingResponse, VideoRatingStats
from app.services.rating_service import rating_service
from app.services.video_service import video_service

router = APIRouter()


@router.post("/{video_id}/rating", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_rating(
    video_id: int,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update a rating for a video (authenticated users only)

    - **video_id**: Video ID
    - **score**: Rating score (1-5)

    If the user has already rated this video, the existing rating will be updated.
    """
    # Check if video exists
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Create or update rating
    rating = await rating_service.create_or_update_rating(
        db=db,
        user_id=current_user.id,
        video_id=video_id,
        rating_data=rating_data
    )

    return rating


@router.get("/{video_id}/rating", response_model=RatingResponse)
async def get_my_rating(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's rating for a video

    - **video_id**: Video ID
    """
    # Check if video exists
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Get user's rating
    rating = await rating_service.get_user_rating(db, current_user.id, video_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't rated this video yet"
        )

    return rating


@router.get("/{video_id}/rating/stats", response_model=VideoRatingStats)
async def get_rating_stats(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get rating statistics for a video (public endpoint)

    - **video_id**: Video ID

    Returns:
    - avg_rating: Average rating score (0.0 if no ratings)
    - rating_count: Total number of ratings
    - user_rating: null (this endpoint doesn't return user-specific rating)
    """
    # Check if video exists
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Get rating stats (no user context for public endpoint)
    stats = await rating_service.get_video_rating_stats(db, video_id, user_id=None)

    return stats


@router.delete("/{video_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_rating(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user's rating for a video

    - **video_id**: Video ID
    """
    # Check if video exists
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Delete rating
    deleted = await rating_service.delete_rating(db, current_user.id, video_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't rated this video yet"
        )

    return None
