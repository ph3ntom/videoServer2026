"""
Video transcoding service for on-demand quality conversion
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Literal
import logging
import time

logger = logging.getLogger(__name__)

# Cache for validated files: {file_path: (is_valid, timestamp)}
_validation_cache: dict[str, tuple[bool, float]] = {}
VALIDATION_CACHE_TTL = 300  # 5 minutes

# Quality presets
QualityType = Literal["480p", "720p", "1080p", "4k", "original"]

QUALITY_SETTINGS = {
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


def get_transcoded_path(original_path: str, quality: QualityType) -> str:
    """
    Get the path for a transcoded video file.

    Structure:
    /storage/videos/UUID.mp4 (original)
    /storage/videos/UUID_480p.mp4 (transcoded)
    /storage/videos/UUID_720p.mp4 (transcoded)
    /storage/videos/UUID_1080p.mp4 (transcoded)
    /storage/videos/UUID_4k.mp4 (transcoded)

    Args:
        original_path: Path to original video file (e.g., /storage/videos/UUID.mp4)
        quality: Quality preset (480p, 720p, 1080p, 4k, original)

    Returns:
        Path to transcoded file
    """
    if quality == "original":
        return original_path

    path = Path(original_path)

    # Get filename without extension (e.g., "UUID" from "UUID.mp4")
    stem = path.stem

    # Get parent directory
    video_dir = path.parent

    # Transcoded file: {video_dir}/{stem}_{quality}.mp4
    transcoded_file = video_dir / f"{stem}_{quality}.mp4"
    return str(transcoded_file)


def is_valid_video_file(video_path: str, use_cache: bool = True) -> bool:
    """
    Verify that a video file is valid and playable using FFprobe.
    Uses caching to avoid repeated ffprobe calls.

    Args:
        video_path: Path to video file
        use_cache: Whether to use validation cache (default: True)

    Returns:
        True if file is valid
    """
    if not os.path.exists(video_path):
        return False

    # Check cache first
    if use_cache and video_path in _validation_cache:
        is_valid, timestamp = _validation_cache[video_path]
        # If cache is still fresh, return cached result
        if time.time() - timestamp < VALIDATION_CACHE_TTL:
            return is_valid

    # Validate with ffprobe
    try:
        import subprocess
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        is_valid = result.returncode == 0 and "video" in result.stdout

        # Cache the result
        if use_cache:
            _validation_cache[video_path] = (is_valid, time.time())

        return is_valid
    except Exception as e:
        logger.error(f"Failed to validate video file {video_path}: {e}")
        return False


def is_transcoded_available(original_path: str, quality: QualityType) -> bool:
    """
    Check if a transcoded version already exists and is valid.

    Args:
        original_path: Path to original video
        quality: Quality preset

    Returns:
        True if transcoded file exists and is valid
    """
    if quality == "original":
        return True

    transcoded_path = get_transcoded_path(original_path, quality)

    # Check if file exists
    if not os.path.exists(transcoded_path):
        return False

    # Check if file is valid (not corrupted or incomplete)
    if not is_valid_video_file(transcoded_path):
        logger.warning(f"Transcoded file exists but is invalid, removing: {transcoded_path}")
        try:
            os.remove(transcoded_path)
        except Exception as e:
            logger.error(f"Failed to remove invalid file: {e}")
        return False

    return True


async def transcode_video(
    input_path: str,
    output_path: str,
    quality: QualityType
) -> bool:
    """
    Transcode video to specified quality using FFmpeg.

    Args:
        input_path: Path to source video
        output_path: Path to save transcoded video
        quality: Quality preset (480p, 720p, 1080p, 4k)

    Returns:
        True if successful, False otherwise
    """
    if quality == "original":
        return True  # No transcoding needed

    if quality not in QUALITY_SETTINGS:
        logger.error(f"Invalid quality preset: {quality}")
        return False

    settings = QUALITY_SETTINGS[quality]

    # Ensure output directory exists
    os.makedirs(Path(output_path).parent, exist_ok=True)

    # FFmpeg command
    # -i: input file
    # -vf scale: resize video
    # -c:v libx264: H.264 codec
    # -preset medium: encoding speed/quality balance
    # -crf 23: quality (lower = better, 23 is good default)
    # -b:v: video bitrate
    # -c:a aac: audio codec
    # -b:a: audio bitrate
    # -movflags +faststart: optimize for streaming
    # -y: overwrite output file

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
        "-movflags", "+faststart",
        "-y",  # Overwrite output
        output_path
    ]

    try:
        logger.info(f"Starting transcoding: {input_path} -> {output_path} ({quality})")

        # Run FFmpeg asynchronously
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            print(f"[TRANSCODING] ✅ SUCCESS: {output_path}")
            logger.info(f"Transcoding completed: {output_path}")

            # Verify the file is valid
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"[TRANSCODING] File size: {file_size} bytes")
                if file_size < 1000:  # Less than 1KB is suspicious
                    print(f"[TRANSCODING] ⚠️ WARNING: File size too small, might be corrupted")

            return True
        else:
            error_message = stderr.decode() if stderr else "No error message"
            print(f"[TRANSCODING] ❌ FAILED with return code {process.returncode}")
            print(f"[TRANSCODING] Error: {error_message[:500]}")  # First 500 chars
            logger.error(f"Transcoding failed (code {process.returncode}): {error_message}")

            # Clean up partial file
            if os.path.exists(output_path):
                os.remove(output_path)
                print(f"[TRANSCODING] Cleaned up partial file: {output_path}")
            return False

    except Exception as e:
        logger.error(f"Transcoding error: {str(e)}")
        # Clean up partial file
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


def get_video_resolution(video_path: str) -> tuple[int, int]:
    """
    Get video resolution using FFprobe.

    Args:
        video_path: Path to video file

    Returns:
        Tuple of (width, height), or (0, 0) if failed
    """
    try:
        import subprocess
        import json

        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-select_streams", "v:0",
            video_path
        ]

        result = subprocess.run(command, capture_output=True, text=True)
        data = json.loads(result.stdout)

        if "streams" in data and len(data["streams"]) > 0:
            stream = data["streams"][0]
            width = stream.get("width", 0)
            height = stream.get("height", 0)
            return (width, height)

    except Exception as e:
        logger.error(f"Failed to get video resolution: {e}")

    return (0, 0)


def should_use_original(original_path: str, quality: QualityType) -> bool:
    """
    Check if we should use original file instead of transcoding.
    Returns True if requested quality is >= original resolution.

    Args:
        original_path: Path to original video
        quality: Requested quality

    Returns:
        True if original should be used
    """
    if quality == "original":
        return True

    # Get original resolution
    orig_width, orig_height = get_video_resolution(original_path)

    if orig_width == 0 or orig_height == 0:
        # Can't determine resolution, default to transcoding
        return False

    # Get target resolution
    target_settings = QUALITY_SETTINGS.get(quality)
    if not target_settings:
        return False

    target_height = target_settings["height"]

    # If original is lower or equal to target, use original
    # e.g., original is 1080p, user wants 4K -> use original (no upscaling)
    if orig_height <= target_height:
        logger.info(f"Original resolution ({orig_width}x{orig_height}) is <= target ({quality}), using original")
        return True

    return False


async def get_video_for_quality(
    original_path: str,
    quality: QualityType,
    transcode_in_background: bool = False
) -> Optional[str]:
    """
    Get video file path for requested quality.
    If transcoded version doesn't exist:
    - If transcode_in_background=True: start transcoding and return original
    - If transcode_in_background=False: transcode synchronously and return transcoded

    Args:
        original_path: Path to original video
        quality: Requested quality
        transcode_in_background: Whether to transcode in background

    Returns:
        Path to video file (original or transcoded)
    """
    if quality == "original":
        return original_path

    # Check if original file exists
    if not os.path.exists(original_path):
        logger.error(f"Original video not found: {original_path}")
        return None

    # Check if we should just use original (e.g., original is 1080p, user wants 4K)
    if should_use_original(original_path, quality):
        print(f"[TRANSCODING] Using original file for {quality} request (no upscaling)")
        logger.info(f"Using original file for {quality} request (no upscaling)")
        return original_path

    # Get transcoded path
    transcoded_path = get_transcoded_path(original_path, quality)
    print(f"[TRANSCODING] Transcoded path: {transcoded_path}")

    # If already transcoded, validate and return cached version
    if os.path.exists(transcoded_path):
        print(f"[TRANSCODING] Found cached file, validating: {transcoded_path}")
        if is_valid_video_file(transcoded_path):
            print(f"[TRANSCODING] ✓ Using valid cached file: {transcoded_path}")
            logger.info(f"Using cached transcoded file: {transcoded_path}")
            return transcoded_path
        else:
            print(f"[TRANSCODING] ✗ Cached file is invalid/incomplete, removing: {transcoded_path}")
            logger.warning(f"Cached file is invalid, removing: {transcoded_path}")
            try:
                os.remove(transcoded_path)
            except Exception as e:
                logger.error(f"Failed to remove invalid cached file: {e}")

    # Need to transcode
    print(f"[TRANSCODING] Need to transcode. Cache not found: {transcoded_path}")
    logger.info(f"Transcoded file not found: {transcoded_path}")

    if transcode_in_background:
        # Start transcoding in background, return original for now
        print(f"[TRANSCODING] Starting background transcoding for {quality}")
        logger.info(f"Starting background transcoding for {quality}")
        asyncio.create_task(transcode_video(original_path, transcoded_path, quality))
        return original_path
    else:
        # Transcode synchronously (user waits)
        print(f"[TRANSCODING] Starting SYNCHRONOUS transcoding for {quality}")
        print(f"[TRANSCODING] This may take several minutes...")
        logger.info(f"Starting synchronous transcoding for {quality}")
        success = await transcode_video(original_path, transcoded_path, quality)

        if success:
            print(f"[TRANSCODING] Transcoding completed successfully: {transcoded_path}")
            return transcoded_path
        else:
            # Fallback to original if transcoding failed
            print(f"[TRANSCODING] Transcoding FAILED, falling back to original")
            logger.warning(f"Transcoding failed, falling back to original")
            return original_path


def get_available_qualities(original_path: str) -> list[str]:
    """
    Get list of available qualities for a video.

    Args:
        original_path: Path to original video

    Returns:
        List of available quality strings (e.g., ["original", "720p", "1080p"])
    """
    qualities = ["original"]

    for quality in ["480p", "720p", "1080p", "4k"]:
        if is_transcoded_available(original_path, quality):
            qualities.append(quality)

    return qualities


def delete_transcoded_files(original_path: str):
    """
    Delete all transcoded versions of a video.
    Used when deleting a video or regenerating transcodes.

    Args:
        original_path: Path to original video
    """
    video_dir = Path(original_path).parent

    for quality in ["480p", "720p", "1080p", "4k"]:
        transcoded_file = video_dir / f"{quality}.mp4"
        if transcoded_file.exists():
            try:
                transcoded_file.unlink()
                logger.info(f"Deleted transcoded file: {transcoded_file}")
            except Exception as e:
                logger.error(f"Failed to delete {transcoded_file}: {e}")
