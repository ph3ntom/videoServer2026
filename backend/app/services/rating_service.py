from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError

from app.models.rating import Rating
from app.models.video import Video
from app.schemas.rating import RatingCreate, VideoRatingStats


class RatingService:
    """Service for rating CRUD operations"""

    @staticmethod
    async def create_or_update_rating(
        db: AsyncSession,
        user_id: int,
        video_id: int,
        rating_data: RatingCreate
    ) -> Rating:
        """
        Create or update a user's rating for a video

        Uses upsert logic: if rating exists, update it; otherwise create new one
        """
        # Check if rating already exists
        result = await db.execute(
            select(Rating).where(
                and_(
                    Rating.user_id == user_id,
                    Rating.video_id == video_id
                )
            )
        )
        existing_rating = result.scalar_one_or_none()

        if existing_rating:
            # Update existing rating
            existing_rating.score = rating_data.score
            await db.commit()
            await db.refresh(existing_rating)
            return existing_rating
        else:
            # Create new rating
            new_rating = Rating(
                user_id=user_id,
                video_id=video_id,
                score=rating_data.score
            )
            db.add(new_rating)

            try:
                await db.commit()
                await db.refresh(new_rating)
                return new_rating
            except IntegrityError:
                await db.rollback()
                # Handle race condition: if rating was created concurrently, try to update
                result = await db.execute(
                    select(Rating).where(
                        and_(
                            Rating.user_id == user_id,
                            Rating.video_id == video_id
                        )
                    )
                )
                existing_rating = result.scalar_one_or_none()
                if existing_rating:
                    existing_rating.score = rating_data.score
                    await db.commit()
                    await db.refresh(existing_rating)
                    return existing_rating
                raise

    @staticmethod
    async def get_user_rating(
        db: AsyncSession,
        user_id: int,
        video_id: int
    ) -> Optional[Rating]:
        """Get a specific user's rating for a video"""
        result = await db.execute(
            select(Rating).where(
                and_(
                    Rating.user_id == user_id,
                    Rating.video_id == video_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_video_rating_stats(
        db: AsyncSession,
        video_id: int,
        user_id: Optional[int] = None
    ) -> VideoRatingStats:
        """
        Get rating statistics for a video

        Returns:
            - avg_rating: Average rating score (0.0 if no ratings)
            - rating_count: Total number of ratings
            - user_rating: Current user's rating (if user_id provided)
        """
        # Get average rating and count
        result = await db.execute(
            select(
                func.coalesce(func.avg(Rating.score), 0.0).label('avg_rating'),
                func.count(Rating.id).label('rating_count')
            ).where(Rating.video_id == video_id)
        )
        stats = result.one()

        # Get user's rating if user_id provided
        user_rating = None
        if user_id:
            user_rating_obj = await RatingService.get_user_rating(db, user_id, video_id)
            if user_rating_obj:
                user_rating = user_rating_obj.score

        return VideoRatingStats(
            avg_rating=float(stats.avg_rating),
            rating_count=stats.rating_count,
            user_rating=user_rating
        )

    @staticmethod
    async def delete_rating(
        db: AsyncSession,
        user_id: int,
        video_id: int
    ) -> bool:
        """
        Delete a user's rating for a video

        Returns:
            True if rating was deleted, False if rating didn't exist
        """
        result = await db.execute(
            select(Rating).where(
                and_(
                    Rating.user_id == user_id,
                    Rating.video_id == video_id
                )
            )
        )
        rating = result.scalar_one_or_none()

        if rating:
            await db.delete(rating)
            await db.commit()
            return True
        return False


rating_service = RatingService()
