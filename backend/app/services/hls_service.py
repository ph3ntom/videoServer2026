"""
HLS (HTTP Live Streaming) conversion service
Converts videos to HLS format with multiple quality levels
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Literal
import logging

logger = logging.getLogger(__name__)

QualityType = Literal["480p", "720p", "1080p", "4k"]

# Quality settings for HLS
HLS_QUALITY_SETTINGS = {
    "480p": {
        "width": 854,
        "height": 480,
        "bitrate": "1000k",
        "audio_bitrate": "128k"
    },
    "720p": {
        "width": 1280,
        "height": 720,
        "bitrate": "2500k",
        "audio_bitrate": "192k"
    },
    "1080p": {
        "width": 1920,
        "height": 1080,
        "bitrate": "5000k",
        "audio_bitrate": "192k"
    },
    "4k": {
        "width": 3840,
        "height": 2160,
        "bitrate": "20000k",
        "audio_bitrate": "256k"
    }
}


def get_hls_directory(original_path: str) -> Path:
    """
    Get the HLS directory path for a video.

    Structure:
    /storage/videos/UUID.mp4 (original)
    /storage/videos/UUID_hls/ (HLS directory)

    Args:
        original_path: Path to original video file

    Returns:
        Path to HLS directory
    """
    path = Path(original_path)
    stem = path.stem
    parent = path.parent
    return parent / f"{stem}_hls"


def get_master_playlist_path(original_path: str) -> str:
    """Get path to master playlist (master.m3u8)"""
    hls_dir = get_hls_directory(original_path)
    return str(hls_dir / "master.m3u8")


def get_quality_playlist_path(original_path: str, quality: QualityType) -> str:
    """Get path to quality-specific playlist"""
    hls_dir = get_hls_directory(original_path)
    return str(hls_dir / quality / "playlist.m3u8")


def is_hls_available(original_path: str) -> bool:
    """
    Check if HLS conversion is complete.

    Returns:
        True if master.m3u8 exists
    """
    master_path = get_master_playlist_path(original_path)
    return os.path.exists(master_path)


def get_available_hls_qualities(original_path: str) -> list[str]:
    """
    Get list of available HLS quality levels.

    Returns:
        List of available qualities (e.g., ["480p", "720p", "1080p"])
    """
    hls_dir = get_hls_directory(original_path)
    if not hls_dir.exists():
        return []

    qualities = []
    for quality in ["480p", "720p", "1080p", "4k"]:
        playlist = hls_dir / quality / "playlist.m3u8"
        if playlist.exists():
            qualities.append(quality)

    return qualities


async def convert_to_hls_quality(
    input_path: str,
    hls_dir: Path,
    quality: QualityType
) -> bool:
    """
    Convert video to HLS format for a specific quality.

    Args:
        input_path: Path to source video
        hls_dir: HLS output directory
        quality: Quality preset

    Returns:
        True if successful
    """
    settings = HLS_QUALITY_SETTINGS[quality]
    quality_dir = hls_dir / quality
    quality_dir.mkdir(parents=True, exist_ok=True)

    playlist_path = quality_dir / "playlist.m3u8"
    segment_pattern = quality_dir / "segment%d.ts"

    # FFmpeg HLS conversion command
    # -hls_time 6: 6 second segments
    # -hls_playlist_type vod: Video on demand (not live)
    # -hls_segment_filename: segment file pattern
    # -hls_flags independent_segments: Each segment is independent
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"scale={settings['width']}:{settings['height']}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-b:v", settings["bitrate"],
        "-c:a", "aac",
        "-b:a", settings["audio_bitrate"],
        "-hls_time", "6",
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(segment_pattern),
        "-hls_flags", "independent_segments",
        str(playlist_path)
    ]

    try:
        logger.info(f"Starting HLS conversion: {quality}")
        print(f"[HLS] Starting conversion for {quality}")

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            print(f"[HLS] ✅ {quality} conversion completed")
            logger.info(f"HLS conversion completed: {quality}")
            return True
        else:
            error_message = stderr.decode() if stderr else "No error message"
            print(f"[HLS] ❌ {quality} conversion failed")
            print(f"[HLS] Error: {error_message[:500]}")
            logger.error(f"HLS conversion failed for {quality}: {error_message}")
            return False

    except Exception as e:
        logger.error(f"HLS conversion error for {quality}: {str(e)}")
        print(f"[HLS] ❌ Exception during {quality} conversion: {str(e)}")
        return False


def create_master_playlist(hls_dir: Path, qualities: list[QualityType]):
    """
    Create master playlist (master.m3u8) that references all quality levels.

    Args:
        hls_dir: HLS directory
        qualities: List of available qualities
    """
    master_path = hls_dir / "master.m3u8"

    lines = ["#EXTM3U", "#EXT-X-VERSION:3"]

    for quality in qualities:
        settings = HLS_QUALITY_SETTINGS[quality]
        bandwidth = int(settings["bitrate"].replace("k", "000"))
        resolution = f"{settings['width']}x{settings['height']}"

        lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={resolution}")
        lines.append(f"{quality}/playlist.m3u8")

    master_content = "\n".join(lines) + "\n"
    master_path.write_text(master_content)
    logger.info(f"Created master playlist: {master_path}")
    print(f"[HLS] ✅ Master playlist created")


async def convert_video_to_hls(
    original_path: str,
    qualities: Optional[list[QualityType]] = None
) -> bool:
    """
    Convert video to HLS format with multiple quality levels.

    Args:
        original_path: Path to original video
        qualities: List of qualities to generate (default: all)

    Returns:
        True if successful
    """
    if qualities is None:
        qualities = ["480p", "720p", "1080p"]  # Default qualities

    hls_dir = get_hls_directory(original_path)
    hls_dir.mkdir(parents=True, exist_ok=True)

    print(f"[HLS] Converting video to HLS format")
    print(f"[HLS] Qualities: {', '.join(qualities)}")
    logger.info(f"Starting HLS conversion for {original_path}")

    # Convert each quality
    successful_qualities = []
    for quality in qualities:
        success = await convert_to_hls_quality(original_path, hls_dir, quality)
        if success:
            successful_qualities.append(quality)

    if not successful_qualities:
        logger.error("No qualities were successfully converted")
        print("[HLS] ❌ No qualities were successfully converted")
        return False

    # Create master playlist
    create_master_playlist(hls_dir, successful_qualities)

    print(f"[HLS] ✅ Conversion complete. Available qualities: {', '.join(successful_qualities)}")
    logger.info(f"HLS conversion complete: {successful_qualities}")

    return True


def delete_hls_files(original_path: str):
    """
    Delete all HLS files for a video.

    Args:
        original_path: Path to original video
    """
    hls_dir = get_hls_directory(original_path)

    if hls_dir.exists():
        try:
            import shutil
            shutil.rmtree(hls_dir)
            logger.info(f"Deleted HLS directory: {hls_dir}")
            print(f"[HLS] Deleted HLS files: {hls_dir}")
        except Exception as e:
            logger.error(f"Failed to delete HLS directory: {e}")
            print(f"[HLS] ❌ Failed to delete HLS directory: {e}")
