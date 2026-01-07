import os
import subprocess
import json
from typing import List, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import UploadFile

from app.models.video import Video, VideoStatus
from app.models.user import User
from app.schemas.video import VideoCreate, VideoUpdate
from app.core.config import settings


class VideoService:
    """Service for video CRUD operations"""

    @staticmethod
    async def get_by_id(db: AsyncSession, video_id: int) -> Optional[Video]:
        """Get video by ID"""
        result = await db.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[VideoStatus] = VideoStatus.READY
    ) -> List[Video]:
        """Get all videos"""
        from sqlalchemy.orm import selectinload

        query = select(Video).options(selectinload(Video.uploader))

        if status:
            query = query.where(Video.status == status)

        query = query.order_by(desc(Video.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Video]:
        """Get videos by user"""
        query = (
            select(Video)
            .where(Video.user_id == user_id)
            .order_by(desc(Video.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        video_data: VideoCreate,
        user_id: int,
        file_path: str,
        file_size: int
    ) -> Video:
        """Create a new video"""
        video = Video(
            user_id=user_id,
            title=video_data.title,
            description=video_data.description,
            file_path=file_path,
            file_size=file_size,
            status=VideoStatus.PROCESSING
        )

        db.add(video)
        await db.commit()
        await db.refresh(video)
        return video

    @staticmethod
    async def update(
        db: AsyncSession,
        video: Video,
        video_data: VideoUpdate
    ) -> Video:
        """Update video metadata"""
        if video_data.title is not None:
            video.title = video_data.title
        if video_data.description is not None:
            video.description = video_data.description

        await db.commit()
        await db.refresh(video)
        return video

    @staticmethod
    async def delete(db: AsyncSession, video: Video) -> None:
        """Delete video"""
        # Delete file
        if os.path.exists(video.file_path):
            os.remove(video.file_path)

        # Delete from database
        await db.delete(video)
        await db.commit()

    @staticmethod
    async def increment_view_count(db: AsyncSession, video: Video) -> None:
        """Increment video view count"""
        video.view_count += 1
        await db.commit()

    @staticmethod
    def extract_video_metadata(file_path: str) -> dict:
        """Extract video metadata using ffprobe"""
        try:
            cmd = [
                settings.FFPROBE_PATH,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {}

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break

            if not video_stream:
                return {}

            format_data = data.get('format', {})

            return {
                'duration': int(float(format_data.get('duration', 0))),
                'width': video_stream.get('width'),
                'height': video_stream.get('height'),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name'),
                'bitrate': int(format_data.get('bit_rate', 0)) // 1000  # Convert to kbps
            }
        except Exception as e:
            print(f"Error extracting video metadata: {e}")
            return {}

    @staticmethod
    async def update_video_metadata(db: AsyncSession, video: Video) -> Video:
        """Update video with extracted metadata"""
        metadata = VideoService.extract_video_metadata(video.file_path)

        video.duration = metadata.get('duration')
        video.width = metadata.get('width')
        video.height = metadata.get('height')
        video.fps = metadata.get('fps')
        video.codec = metadata.get('codec')
        video.bitrate = metadata.get('bitrate')
        video.status = VideoStatus.READY

        await db.commit()
        await db.refresh(video)
        return video


video_service = VideoService()
