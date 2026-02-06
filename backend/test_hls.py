"""
Test HLS conversion
"""
import asyncio
import sys
sys.path.insert(0, '/Users/ihoyeon/Desktop/python Projects/videos_web_server/backend')

from app.services import hls_service

async def test_hls_conversion():
    # Test video path
    video_path = "/Users/ihoyeon/Desktop/python Projects/videos_web_server/storage/videos/2a4df361-2e77-4833-abf1-fc4e0e9dc7dc.mp4"

    print("=" * 60)
    print("Starting HLS conversion test")
    print("=" * 60)

    # Convert to HLS with default qualities (480p, 720p, 1080p)
    success = await hls_service.convert_video_to_hls(
        original_path=video_path,
        qualities=["480p", "720p", "1080p"]
    )

    if success:
        print("\n" + "=" * 60)
        print("HLS conversion completed successfully!")
        print("=" * 60)

        # Check status
        is_available = hls_service.is_hls_available(video_path)
        available_qualities = hls_service.get_available_hls_qualities(video_path)

        print(f"\nHLS Available: {is_available}")
        print(f"Available Qualities: {available_qualities}")

        master_path = hls_service.get_master_playlist_path(video_path)
        print(f"\nMaster playlist: {master_path}")

    else:
        print("\n" + "=" * 60)
        print("HLS conversion failed!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_hls_conversion())
