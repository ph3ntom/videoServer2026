from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
from sqlalchemy.orm import selectinload
import re

from app.models.tag import Tag
from app.models.video import Video
from app.models.associations import video_tags
from app.schemas.tag import TagCreate, TagUpdate


class TagService:
    """Service for tag management"""

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-friendly slug from tag name"""
        # Convert to lowercase
        slug = name.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug

    async def create(self, db: AsyncSession, tag_data: TagCreate) -> Tag:
        """Create a new tag"""
        # Generate slug
        slug = self.generate_slug(tag_data.name)

        # Check if tag with same name or slug exists
        result = await db.execute(
            select(Tag).where(
                or_(Tag.name == tag_data.name, Tag.slug == slug)
            )
        )
        existing_tag = result.scalar_one_or_none()

        if existing_tag:
            # Return existing tag instead of creating duplicate
            return existing_tag

        # Create new tag
        tag = Tag(
            name=tag_data.name,
            slug=slug,
            description=tag_data.description,
            color=tag_data.color
        )

        db.add(tag)
        await db.commit()
        await db.refresh(tag)

        return tag

    async def get_by_id(self, db: AsyncSession, tag_id: int) -> Optional[Tag]:
        """Get tag by ID"""
        result = await db.execute(
            select(Tag).options(selectinload(Tag.videos)).where(Tag.id == tag_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Tag]:
        """Get tag by slug"""
        result = await db.execute(
            select(Tag).options(selectinload(Tag.videos)).where(Tag.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Tag]:
        """Get all tags with optional search"""
        query = select(Tag).options(selectinload(Tag.videos))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Tag.name.ilike(search_pattern),
                    Tag.description.ilike(search_pattern)
                )
            )

        query = query.order_by(Tag.name).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_popular(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[tuple[Tag, int]]:
        """Get most popular tags (by video count)"""
        # Count videos per tag
        query = (
            select(Tag, func.count(video_tags.c.video_id).label('video_count'))
            .outerjoin(video_tags, Tag.id == video_tags.c.tag_id)
            .group_by(Tag.id)
            .order_by(func.count(video_tags.c.video_id).desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def update(
        self,
        db: AsyncSession,
        tag: Tag,
        tag_data: TagUpdate
    ) -> Tag:
        """Update tag"""
        update_data = tag_data.model_dump(exclude_unset=True)

        # Update slug if name changes
        if 'name' in update_data:
            update_data['slug'] = self.generate_slug(update_data['name'])

        for field, value in update_data.items():
            setattr(tag, field, value)

        await db.commit()
        await db.refresh(tag)

        return tag

    async def delete(self, db: AsyncSession, tag: Tag) -> None:
        """Delete tag"""
        await db.delete(tag)
        await db.commit()

    async def add_tags_to_video(
        self,
        db: AsyncSession,
        video: Video,
        tag_ids: List[int]
    ) -> List[Tag]:
        """Add tags to a video"""
        # Get existing tags for this video
        existing_tag_ids = {tag.id for tag in video.tags}

        # Get tags to add (only new ones)
        new_tag_ids = set(tag_ids) - existing_tag_ids

        if new_tag_ids:
            # Get tag objects
            result = await db.execute(
                select(Tag).where(Tag.id.in_(new_tag_ids))
            )
            tags_to_add = result.scalars().all()

            # Add tags to video
            video.tags.extend(tags_to_add)
            await db.commit()
            await db.refresh(video, ['tags'])

        return video.tags

    async def remove_tags_from_video(
        self,
        db: AsyncSession,
        video: Video,
        tag_ids: List[int]
    ) -> List[Tag]:
        """Remove tags from a video"""
        # Remove specified tags
        video.tags = [tag for tag in video.tags if tag.id not in tag_ids]
        await db.commit()
        await db.refresh(video, ['tags'])

        return video.tags

    async def set_video_tags(
        self,
        db: AsyncSession,
        video: Video,
        tag_ids: List[int]
    ) -> List[Tag]:
        """Set video tags (replace all existing tags)"""
        # Get tags
        result = await db.execute(
            select(Tag).where(Tag.id.in_(tag_ids))
        )
        tags = list(result.scalars().all())

        # Replace all tags
        video.tags = tags
        await db.commit()
        await db.refresh(video, ['tags'])

        return video.tags

    async def get_videos_by_tag(
        self,
        db: AsyncSession,
        tag_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Video]:
        """Get all videos with a specific tag"""
        query = (
            select(Video)
            .join(video_tags, Video.id == video_tags.c.video_id)
            .where(video_tags.c.tag_id == tag_id)
            .order_by(Video.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def search_tags(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10
    ) -> List[Tag]:
        """Search tags for autocomplete"""
        search_pattern = f"%{query}%"

        result = await db.execute(
            select(Tag)
            .where(Tag.name.ilike(search_pattern))
            .order_by(Tag.name)
            .limit(limit)
        )

        return list(result.scalars().all())


tag_service = TagService()
