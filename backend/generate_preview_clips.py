#!/usr/bin/env python3
"""
Generate preview clips for existing videos
"""
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.video import Video
from app.services.thumbnail_service import thumbnail_service
from app.core.config import settings


async def main():
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )

    # Create async session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        # Get all videos
        result = await session.execute(select(Video))
        videos = result.scalars().all()

        print(f"Found {len(videos)} videos")

        for video in videos:
            print(f"\n{'='*60}")
            print(f"Processing video ID {video.id}: {video.title}")
            print(f"File path: {video.file_path}")

            # Check if file exists
            if not Path(video.file_path).exists():
                print(f"  ❌ Video file not found, skipping...")
                continue

            # Check if preview clips already exist
            clips_dir = Path(settings.UPLOAD_DIR) / "thumbnails" / str(video.id)
            existing_clips = []
            if clips_dir.exists():
                for i in range(1, 8):
                    clip_path = clips_dir / f"preview_{i}.mp4"
                    if clip_path.exists():
                        existing_clips.append(i)

            if len(existing_clips) == 7:
                print(f"  ✅ All 7 preview clips already exist, skipping...")
                continue

            if existing_clips:
                print(f"  ⚠️  Found {len(existing_clips)} existing clips, regenerating all...")

            # Generate preview clips
            try:
                print(f"  🎬 Generating 7 preview clips (3 seconds each)...")
                clip_paths = thumbnail_service.generate_preview_clips(
                    video.file_path,
                    video.id,
                    num_clips=7,
                    clip_duration=3
                )

                if clip_paths:
                    print(f"  ✅ Successfully generated {len(clip_paths)} preview clips!")
                    for i, path in enumerate(clip_paths, 1):
                        size_kb = Path(path).stat().st_size / 1024
                        print(f"     - Clip {i}: {size_kb:.1f} KB")
                else:
                    print(f"  ❌ No preview clips generated")

            except Exception as e:
                print(f"  ❌ Error generating preview clips: {e}")

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
