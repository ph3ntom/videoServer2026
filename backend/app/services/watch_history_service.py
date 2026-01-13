from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.models.watch_history import WatchHistory
from app.models.video import Video
from app.schemas.watch_history import WatchHistoryCreate, WatchHistoryUpdate, ContinueWatchingItem


class WatchHistoryService:
    """Service for watch history operations"""

    @staticmethod
    async def save_or_update_watch_history(
        db: AsyncSession,
        user_id: int,
        video_id: int,
        watch_data: WatchHistoryUpdate
    ) -> WatchHistory:
        """
        Save or update watch history (upsert logic)

        Args:
            db: Database session
            user_id: User ID
            video_id: Video ID
            watch_data: Watch position and duration

        Returns:
            Updated or created WatchHistory
        """
        # Get video to calculate completion
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError("Video not found")

        # Check if watch history exists
        result = await db.execute(
            select(WatchHistory).where(
                and_(
                    WatchHistory.user_id == user_id,
                    WatchHistory.video_id == video_id
                )
            )
        )
        existing = result.scalar_one_or_none()

        # Calculate completion (>= 90% watched)
        completed = False
        if video.duration and video.duration > 0:
            progress = (watch_data.watch_position / video.duration) * 100
            completed = progress >= 90.0

        if existing:
            # Update existing record
            existing.watch_position = watch_data.watch_position
            existing.watch_duration = max(existing.watch_duration, watch_data.watch_duration)
            existing.completed = completed
            existing.last_watched_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new record
            new_history = WatchHistory(
                user_id=user_id,
                video_id=video_id,
                watch_position=watch_data.watch_position,
                watch_duration=watch_data.watch_duration,
                completed=completed,
                last_watched_at=datetime.utcnow()
            )
            db.add(new_history)

            try:
                await db.commit()
                await db.refresh(new_history)
                return new_history
            except IntegrityError:
                await db.rollback()
                # Handle race condition
                result = await db.execute(
                    select(WatchHistory).where(
                        and_(
                            WatchHistory.user_id == user_id,
                            WatchHistory.video_id == video_id
                        )
                    )
                )
                existing = result.scalar_one_or_none()
                if existing:
                    existing.watch_position = watch_data.watch_position
                    existing.watch_duration = max(existing.watch_duration, watch_data.watch_duration)
                    existing.completed = completed
                    existing.last_watched_at = datetime.utcnow()
                    await db.commit()
                    await db.refresh(existing)
                    return existing
                raise

    @staticmethod
    async def get_watch_history(
        db: AsyncSession,
        user_id: int,
        video_id: int
    ) -> Optional[WatchHistory]:
        """Get watch history for a specific video"""
        result = await db.execute(
            select(WatchHistory).where(
                and_(
                    WatchHistory.user_id == user_id,
                    WatchHistory.video_id == video_id
                )
            ).options(selectinload(WatchHistory.video))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_continue_watching_list(
        db: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[ContinueWatchingItem]:
        """
        Get continue watching list for user

        Returns videos that are:
        - Not completed (< 90% watched)
        - Ordered by last_watched_at DESC
        """
        result = await db.execute(
            select(WatchHistory)
            .where(
                and_(
                    WatchHistory.user_id == user_id,
                    WatchHistory.completed == False,
                    WatchHistory.watch_position > 0  # At least started watching
                )
            )
            .options(
                selectinload(WatchHistory.video).selectinload(Video.uploader)
            )
            .order_by(desc(WatchHistory.last_watched_at))
            .limit(limit)
        )
        histories = result.scalars().all()

        # Transform to ContinueWatchingItem
        items = []
        for history in histories:
            if history.video:  # Safety check
                items.append(ContinueWatchingItem(
                    video_id=history.video.id,
                    video_title=history.video.title,
                    video_description=history.video.description,
                    video_duration=history.video.duration,
                    video_thumbnail_path=history.video.thumbnail_path,
                    uploader_username=history.video.uploader.username,
                    watch_position=history.watch_position,
                    progress_percentage=history.progress_percentage,
                    last_watched_at=history.last_watched_at
                ))

        return items

    @staticmethod
    async def delete_watch_history(
        db: AsyncSession,
        user_id: int,
        video_id: int
    ) -> bool:
        """
        Delete watch history

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(WatchHistory).where(
                and_(
                    WatchHistory.user_id == user_id,
                    WatchHistory.video_id == video_id
                )
            )
        )
        history = result.scalar_one_or_none()

        if history:
            await db.delete(history)
            await db.commit()
            return True
        return False


watch_history_service = WatchHistoryService()
