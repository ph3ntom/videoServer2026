import os
import uuid
from pathlib import Path
from typing import List
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.video import VideoStatus
from app.schemas.video import VideoCreate, VideoUpdate, VideoResponse, VideoListResponse
from app.schemas.thumbnail import ThumbnailResponse, ThumbnailSelect
from app.services.video_service import video_service
from app.services.thumbnail_service import thumbnail_service
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a video file

    - **file**: Video file (mp4, mkv, avi, mov, webm)
    - **title**: Video title
    - **description**: Video description (optional)
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_video_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.allowed_video_extensions_list)}"
        )

    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename

    # Save file
    try:
        contents = await file.read()
        file_size = len(contents)

        # Check file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024**3):.1f}GB"
            )

        with open(file_path, "wb") as f:
            f.write(contents)

    except Exception as e:
        # Clean up file if error occurs
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Create video record
    video_data = VideoCreate(title=title, description=description)
    video = await video_service.create(
        db=db,
        video_data=video_data,
        user_id=current_user.id,
        file_path=str(file_path),
        file_size=file_size
    )

    # Extract metadata in background (for now, doing it synchronously)
    try:
        video = await video_service.update_video_metadata(db, video)
    except Exception as e:
        print(f"Failed to extract metadata: {e}")
        # Video will remain in PROCESSING status

    # Generate thumbnails
    try:
        thumbnail_paths = thumbnail_service.generate_thumbnails(
            str(file_path),
            video.id,
            max_thumbnails=12
        )

        if thumbnail_paths:
            await thumbnail_service.save_thumbnails_to_db(db, video, thumbnail_paths)
            await db.refresh(video)
        else:
            print(f"No thumbnails generated for video {video.id}")
    except Exception as e:
        print(f"Failed to generate thumbnails: {e}")
        # Continue without thumbnails

    return video


@router.get("/", response_model=List[VideoListResponse])
async def list_videos(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all ready videos

    - **skip**: Number of videos to skip (pagination)
    - **limit**: Maximum number of videos to return
    """
    videos = await video_service.get_all(db, skip=skip, limit=limit, status=VideoStatus.READY)

    # Transform to include uploader username
    result = []
    for video in videos:
        video_dict = {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "file_size": video.file_size,
            "thumbnail_path": video.thumbnail_path,
            "duration": video.duration,
            "width": video.width,
            "height": video.height,
            "status": video.status.value,
            "view_count": video.view_count,
            "created_at": video.created_at,
            "uploader_username": video.uploader.username
        }
        result.append(VideoListResponse(**video_dict))

    return result


@router.get("/my-videos", response_model=List[VideoResponse])
async def get_my_videos(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's uploaded videos

    - **skip**: Number of videos to skip (pagination)
    - **limit**: Maximum number of videos to return
    """
    videos = await video_service.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return videos


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get video by ID

    - **video_id**: Video ID
    """
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    return video


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream video file

    - **video_id**: Video ID
    """
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    if video.status != VideoStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video is not ready for streaming"
        )

    if not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    # Increment view count
    await video_service.increment_view_count(db, video)

    # Stream video file
    def iterfile():
        with open(video.file_path, "rb") as f:
            yield from f

    # URL encode filename for Content-Disposition header (supports UTF-8 characters)
    encoded_filename = quote(f"{video.title}{Path(video.file_path).suffix}")

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video_data: VideoUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update video metadata

    - **video_id**: Video ID
    - **title**: New video title (optional)
    - **description**: New video description (optional)
    """
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Check ownership
    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this video"
        )

    video = await video_service.update(db, video, video_data)
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete video

    - **video_id**: Video ID
    """
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Check ownership
    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this video"
        )

    await video_service.delete(db, video)
    return None


# Thumbnail endpoints

@router.get("/{video_id}/thumbnails", response_model=List[ThumbnailResponse])
async def get_video_thumbnails(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all thumbnails for a video

    - **video_id**: Video ID
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.video import Video

    result = await db.execute(
        select(Video).options(selectinload(Video.thumbnails)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return video.thumbnails


@router.post("/{video_id}/thumbnails/select", response_model=ThumbnailResponse)
async def select_thumbnail(
    video_id: int,
    data: ThumbnailSelect,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Select a thumbnail as the video's main thumbnail (Admin only)

    - **video_id**: Video ID
    - **thumbnail_id**: ID of thumbnail to select
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.video import Video

    result = await db.execute(
        select(Video).options(selectinload(Video.thumbnails)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Check ownership
    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this video"
        )

    try:
        selected_thumbnail = await thumbnail_service.select_thumbnail(
            db, video, data.thumbnail_id
        )
        return selected_thumbnail
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{video_id}/thumbnails/upload", response_model=ThumbnailResponse)
async def upload_custom_thumbnail(
    video_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a custom thumbnail image (Admin only)

    - **video_id**: Video ID
    - **file**: Image file (jpg, jpeg, png, webp)
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.video import Video
    from app.models.video_thumbnail import VideoThumbnail

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Read file and validate size (max 20MB)
    contents = await file.read()
    max_size = 20 * 1024 * 1024  # 20MB
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: 20MB"
        )

    result = await db.execute(
        select(Video).options(selectinload(Video.thumbnails)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Check ownership
    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this video"
        )

    # Create thumbnails directory
    thumbnails_dir = Path(settings.UPLOAD_DIR) / "thumbnails" / str(video_id)
    thumbnails_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    unique_filename = f"custom_{uuid.uuid4()}{file_ext}"
    file_path = thumbnails_dir / unique_filename

    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Create thumbnail record
    thumbnail = VideoThumbnail(
        video_id=video.id,
        file_path=str(file_path),
        is_auto_generated=False,
        is_selected=False
    )
    db.add(thumbnail)
    await db.commit()
    await db.refresh(thumbnail)

    return thumbnail


@router.get("/{video_id}/thumbnails/{thumbnail_id}/image")
async def get_thumbnail_image(
    video_id: int,
    thumbnail_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get thumbnail image file

    - **video_id**: Video ID
    - **thumbnail_id**: Thumbnail ID
    """
    from sqlalchemy import select
    from app.models.video_thumbnail import VideoThumbnail
    from fastapi.responses import FileResponse

    result = await db.execute(
        select(VideoThumbnail).where(
            VideoThumbnail.id == thumbnail_id,
            VideoThumbnail.video_id == video_id
        )
    )
    thumbnail = result.scalar_one_or_none()

    if not thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found"
        )

    if not os.path.exists(thumbnail.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail file not found"
        )

    # Determine media type
    file_ext = Path(thumbnail.file_path).suffix.lower()
    media_types = {
        '.webp': 'image/webp',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    media_type = media_types.get(file_ext, 'image/webp')

    return FileResponse(thumbnail.file_path, media_type=media_type)


@router.get("/{video_id}/thumbnail")
async def get_selected_thumbnail(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get selected thumbnail image for a video

    - **video_id**: Video ID
    """
    from sqlalchemy import select
    from app.models.video import Video
    from fastapi.responses import FileResponse

    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    if not video.thumbnail_path or not os.path.exists(video.thumbnail_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found"
        )

    # Determine media type
    file_ext = Path(video.thumbnail_path).suffix.lower()
    media_types = {
        '.webp': 'image/webp',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    media_type = media_types.get(file_ext, 'image/webp')

    return FileResponse(video.thumbnail_path, media_type=media_type)
