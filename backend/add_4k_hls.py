"""
Add 4K quality to existing HLS conversion for video 13
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services import hls_service
from app.core.database import AsyncSessionLocal
from app.services.video_service import video_service


async def add_4k_to_video(video_id: int):
    """Add 4K HLS quality to an existing video"""
    async with AsyncSessionLocal() as db:
        # Get video
        video = await video_service.get_by_id(db, video_id)
        if not video:
            print(f"❌ Video {video_id} not found")
            return

        print(f"Video: {video.title}")
        print(f"File: {video.file_path}")

        # Check if HLS directory exists
        hls_dir = hls_service.get_hls_directory(video.file_path)
        if not hls_dir.exists():
            print(f"❌ HLS directory not found: {hls_dir}")
            return

        print(f"\n🎬 Adding 4K quality to existing HLS...")

        # Convert only 4K quality
        success = await hls_service.convert_to_hls_quality(
            video.file_path,
            hls_dir,
            "4k"
        )

        if success:
            print("\n✅ 4K quality added successfully")

            # Regenerate master playlist with all qualities
            existing_qualities = []
            for quality in ["480p", "720p", "1080p", "4k"]:
                quality_playlist = hls_dir / quality / "playlist.m3u8"
                if quality_playlist.exists():
                    existing_qualities.append(quality)

            print(f"Existing qualities: {', '.join(existing_qualities)}")
            hls_service.create_master_playlist(hls_dir, existing_qualities)
            print("✅ Master playlist updated")
        else:
            print("\n❌ Failed to add 4K quality")


if __name__ == "__main__":
    print("=" * 60)
    print("Adding 4K HLS quality to video 13")
    print("=" * 60)

    asyncio.run(add_4k_to_video(13))

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
