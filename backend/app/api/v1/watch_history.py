from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.watch_history import (
    WatchHistoryUpdate,
    WatchHistoryResponse,
    ContinueWatchingItem
)
from app.services.watch_history_service import watch_history_service
from app.services.video_service import video_service

router = APIRouter()


@router.post("/{video_id}/watch-history", response_model=WatchHistoryResponse)
async def save_watch_progress(
    video_id: int,
    watch_data: WatchHistoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save or update watch progress for a video

    - **video_id**: Video ID
    - **watch_position**: Current playback position in seconds
    - **watch_duration**: Total watch duration in seconds

    This endpoint saves the user's current playback position.
    Call this periodically (e.g., every 10 seconds) while the video is playing.
    """
    # Check if video exists
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    try:
        history = await watch_history_service.save_or_update_watch_history(
            db=db,
            user_id=current_user.id,
            video_id=video_id,
            watch_data=watch_data
        )

        return history
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{video_id}/watch-history", response_model=WatchHistoryResponse)
async def get_watch_progress(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get watch progress for a specific video

    - **video_id**: Video ID

    Returns the user's watch progress for this video.
    Use this when loading a video to resume from the last position.
    """
    # Check if video exists
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    history = await watch_history_service.get_watch_history(
        db=db,
        user_id=current_user.id,
        video_id=video_id
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No watch history found for this video"
        )

    return history


@router.get("/continue-watching", response_model=List[ContinueWatchingItem])
async def get_continue_watching(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get continue watching list for the current user

    - **limit**: Maximum number of videos to return (default: 10)

    Returns a list of videos that the user has started watching but not completed.
    Ordered by last watched date (most recent first).
    """
    items = await watch_history_service.get_continue_watching_list(
        db=db,
        user_id=current_user.id,
        limit=limit
    )

    return items


@router.delete("/{video_id}/watch-history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watch_progress(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete watch history for a video

    - **video_id**: Video ID

    Removes the watch progress for this video.
    """
    deleted = await watch_history_service.delete_watch_history(
        db=db,
        user_id=current_user.id,
        video_id=video_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No watch history found for this video"
        )

    return None
