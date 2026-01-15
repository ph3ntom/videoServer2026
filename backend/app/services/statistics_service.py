from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
from typing import List
from app.models.video import Video
from app.models.rating import Rating


async def get_popular_videos(
    db: AsyncSession,
    limit: int = 10,
    skip: int = 0
) -> List[Video]:
    """
    Get most popular videos by view count.

    Args:
        db: Database session
        limit: Maximum number of videos to return (default: 10)
        skip: Number of videos to skip for pagination (default: 0)

    Returns:
        List of Video objects ordered by view count (descending)
    """
    query = (
        select(Video)
        .options(joinedload(Video.uploader))
        .where(Video.status == "ready")
        .order_by(desc(Video.view_count))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    videos = result.scalars().unique().all()
    return list(videos)


async def get_top_rated_videos(
    db: AsyncSession,
    limit: int = 10,
    skip: int = 0,
    min_ratings: int = 5
) -> List[dict]:
    """
    Get top rated videos with minimum rating threshold.

    Args:
        db: Database session
        limit: Maximum number of videos to return (default: 10)
        skip: Number of videos to skip for pagination (default: 0)
        min_ratings: Minimum number of ratings required (default: 5)

    Returns:
        List of dicts containing video info and rating statistics
    """
    # Subquery to calculate average rating and rating count per video
    rating_stats = (
        select(
            Rating.video_id,
            func.avg(Rating.score).label('avg_rating'),
            func.count(Rating.id).label('rating_count')
        )
        .group_by(Rating.video_id)
        .having(func.count(Rating.id) >= min_ratings)
        .subquery()
    )

    # Main query to get videos with their rating stats
    query = (
        select(
            Video,
            rating_stats.c.avg_rating,
            rating_stats.c.rating_count
        )
        .join(rating_stats, Video.id == rating_stats.c.video_id)
        .options(joinedload(Video.uploader))
        .where(Video.status == "ready")
        .order_by(desc(rating_stats.c.avg_rating))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    # Format the results
    top_rated = []
    for row in rows:
        video = row[0]
        avg_rating = float(row[1])
        rating_count = int(row[2])

        top_rated.append({
            "video": video,
            "avg_rating": round(avg_rating, 2),
            "rating_count": rating_count
        })

    return top_rated


async def get_video_statistics_summary(
    db: AsyncSession
) -> dict:
    """
    Get overall video statistics summary.

    Args:
        db: Database session

    Returns:
        Dictionary containing platform statistics
    """
    # Total videos
    total_videos_query = select(func.count(Video.id)).where(Video.status == "ready")
    total_videos_result = await db.execute(total_videos_query)
    total_videos = total_videos_result.scalar()

    # Total views
    total_views_query = select(func.sum(Video.view_count))
    total_views_result = await db.execute(total_views_query)
    total_views = total_views_result.scalar() or 0

    # Total ratings
    total_ratings_query = select(func.count(Rating.id))
    total_ratings_result = await db.execute(total_ratings_query)
    total_ratings = total_ratings_result.scalar()

    # Average rating across platform
    avg_rating_query = select(func.avg(Rating.score))
    avg_rating_result = await db.execute(avg_rating_query)
    avg_rating = avg_rating_result.scalar()

    return {
        "total_videos": total_videos,
        "total_views": total_views,
        "total_ratings": total_ratings,
        "average_rating": round(float(avg_rating), 2) if avg_rating else 0.0
    }
