import os
import subprocess
from pathlib import Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.models.video_thumbnail import VideoThumbnail
from app.core.config import settings


class ThumbnailService:
    """Service for thumbnail generation and management"""

    @staticmethod
    def generate_thumbnails(video_path: str, video_id: int, max_thumbnails: int = 12) -> List[str]:
        """
        Generate thumbnails from video using FFmpeg scene detection or interval-based method

        Args:
            video_path: Path to video file
            video_id: Video ID for creating thumbnail directory
            max_thumbnails: Maximum number of thumbnails to generate

        Returns:
            List of generated thumbnail file paths
        """
        # Create thumbnails directory
        thumbnails_dir = Path(settings.UPLOAD_DIR) / "thumbnails" / str(video_id)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Get video resolution to determine if we should use scene detection
            # Scene detection is very slow for high-resolution videos (4K, etc.)
            probe_cmd = [
                settings.FFPROBE_PATH,
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                video_path
            ]

            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            width, height = map(int, probe_result.stdout.strip().split(','))

            # For high-resolution videos (> 1080p), use interval-based method
            # Scene detection is too slow for 4K+ videos
            if width > 1920 or height > 1080:
                print(f"High resolution video ({width}x{height}), using interval-based thumbnails")
                return ThumbnailService._generate_interval_thumbnails(
                    video_path, video_id, max_thumbnails
                )

        except Exception as e:
            print(f"Could not determine video resolution: {e}, using scene detection")

        # Output pattern for thumbnails
        output_pattern = str(thumbnails_dir / "thumb_%03d.webp")

        try:
            # FFmpeg command for scene detection and thumbnail generation
            # select='gt(scene,0.3)' detects scene changes with threshold 0.3
            # scale=1280:720 resizes to 720p for better quality
            # -c:v libwebp forces single-image WebP encoder (not animation)
            cmd = [
                settings.FFMPEG_PATH,
                '-i', video_path,
                '-vf', f"select='gt(scene,0.3)',scale=1280:720,setpts=N/FRAME_RATE/TB",
                '-frames:v', str(max_thumbnails),
                '-c:v', 'libwebp',  # Force single-image WebP encoder
                '-q:v', '2',  # Quality (1-31, lower is better) - using 2 for high quality
                '-f', 'image2',
                output_pattern
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes timeout
            )

            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                # Fallback: generate thumbnails at fixed intervals
                return ThumbnailService._generate_interval_thumbnails(
                    video_path, video_id, max_thumbnails
                )

            # Collect generated thumbnail paths
            thumbnail_files = sorted(thumbnails_dir.glob("thumb_*.webp"))
            return [str(f) for f in thumbnail_files]

        except subprocess.TimeoutExpired:
            print(f"Thumbnail generation timeout for video {video_id}")
            return ThumbnailService._generate_interval_thumbnails(
                video_path, video_id, max_thumbnails
            )
        except Exception as e:
            print(f"Error generating thumbnails: {e}")
            return []

    @staticmethod
    def _generate_interval_thumbnails(
        video_path: str, 
        video_id: int, 
        count: int = 12
    ) -> List[str]:
        """
        Fallback: Generate thumbnails at regular intervals
        
        Args:
            video_path: Path to video file
            video_id: Video ID
            count: Number of thumbnails to generate
            
        Returns:
            List of generated thumbnail file paths
        """
        thumbnails_dir = Path(settings.UPLOAD_DIR) / "thumbnails" / str(video_id)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        thumbnail_paths = []
        
        try:
            # Get video duration first
            duration_cmd = [
                settings.FFPROBE_PATH,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            
            # Generate thumbnails at regular intervals
            interval = duration / (count + 1)
            
            for i in range(1, count + 1):
                timestamp = interval * i
                output_file = thumbnails_dir / f"thumb_{i:03d}.webp"
                
                cmd = [
                    settings.FFMPEG_PATH,
                    '-ss', str(timestamp),
                    '-i', video_path,
                    '-vframes', '1',
                    '-vf', 'scale=1280:720',
                    '-c:v', 'libwebp',  # Force single-image WebP encoder
                    '-q:v', '2',
                    str(output_file)
                ]
                
                subprocess.run(cmd, capture_output=True, timeout=10)
                
                if output_file.exists():
                    thumbnail_paths.append(str(output_file))
                    
        except Exception as e:
            print(f"Error generating interval thumbnails: {e}")
            
        return thumbnail_paths

    @staticmethod
    async def save_thumbnails_to_db(
        db: AsyncSession,
        video: Video,
        thumbnail_paths: List[str]
    ) -> None:
        """
        Save generated thumbnails to database
        
        Args:
            db: Database session
            video: Video object
            thumbnail_paths: List of thumbnail file paths
        """
        if not thumbnail_paths:
            return
        
        # Create thumbnail records
        for idx, path in enumerate(thumbnail_paths):
            thumbnail = VideoThumbnail(
                video_id=video.id,
                file_path=path,
                is_auto_generated=True,
                is_selected=(idx == 0)  # Select first thumbnail by default
            )
            db.add(thumbnail)
        
        # Set first thumbnail as video's thumbnail_path
        if thumbnail_paths:
            video.thumbnail_path = thumbnail_paths[0]
        
        await db.commit()

    @staticmethod
    async def select_thumbnail(
        db: AsyncSession,
        video: Video,
        thumbnail_id: int
    ) -> VideoThumbnail:
        """
        Select a thumbnail as the video's main thumbnail

        Args:
            db: Database session
            video: Video object
            thumbnail_id: ID of thumbnail to select

        Returns:
            Selected thumbnail object
        """
        # Deselect all thumbnails for this video
        for thumbnail in video.thumbnails:
            thumbnail.is_selected = False

        # Find and select the specified thumbnail
        selected_thumbnail = None
        for thumbnail in video.thumbnails:
            if thumbnail.id == thumbnail_id:
                thumbnail.is_selected = True
                selected_thumbnail = thumbnail
                video.thumbnail_path = thumbnail.file_path
                break

        if not selected_thumbnail:
            raise ValueError(f"Thumbnail {thumbnail_id} not found for video {video.id}")

        await db.commit()
        await db.refresh(selected_thumbnail)

        return selected_thumbnail

    @staticmethod
    def generate_preview_clips(
        video_path: str,
        video_id: int,
        num_clips: int = 7,
        clip_duration: int = 3
    ) -> List[str]:
        """
        Generate preview video clips from the video for hover preview

        Args:
            video_path: Path to video file
            video_id: Video ID for creating clips directory
            num_clips: Number of preview clips to generate (default: 7)
            clip_duration: Duration of each clip in seconds (default: 5)

        Returns:
            List of generated clip file paths
        """
        # Create clips directory (same as thumbnails directory)
        clips_dir = Path(settings.UPLOAD_DIR) / "thumbnails" / str(video_id)
        clips_dir.mkdir(parents=True, exist_ok=True)

        clip_paths = []

        try:
            # Get video duration using FFprobe
            duration_cmd = [
                settings.FFPROBE_PATH,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]

            result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=10)
            duration = float(result.stdout.strip())

            # Calculate segment size
            segment_size = duration / num_clips

            # Generate clips from each segment
            for i in range(num_clips):
                # Calculate start time for this segment
                # Start from the middle of each segment, offset by half clip duration
                segment_middle = (i + 0.5) * segment_size
                start_time = max(0, segment_middle - (clip_duration / 2))

                # Ensure we don't go past the end of the video
                if start_time + clip_duration > duration:
                    start_time = max(0, duration - clip_duration)

                output_file = clips_dir / f"preview_{i + 1}.mp4"

                # FFmpeg command for clip extraction
                # -ss: start time
                # -t: duration
                # scale=320:-1: resize to 320p width, maintain aspect ratio
                # -c:v libx264: H.264 codec
                # -preset veryfast: fast encoding
                # -crf 28: quality (18-28, higher = lower quality/smaller file)
                # -an: remove audio
                # -movflags +faststart: optimize for streaming
                cmd = [
                    settings.FFMPEG_PATH,
                    '-ss', str(start_time),
                    '-t', str(clip_duration),
                    '-i', video_path,
                    '-vf', 'scale=320:-1',
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-crf', '28',
                    '-an',
                    '-movflags', '+faststart',
                    str(output_file)
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 seconds timeout per clip
                )

                if result.returncode == 0 and output_file.exists():
                    clip_paths.append(str(output_file))
                    print(f"Generated preview clip {i + 1}/{num_clips} at {start_time:.2f}s")
                else:
                    print(f"Failed to generate preview clip {i + 1}: {result.stderr}")

        except Exception as e:
            print(f"Error generating preview clips: {e}")

        return clip_paths


thumbnail_service = ThumbnailService()
