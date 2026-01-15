import os
import uuid
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.video import VideoStatus
from app.schemas.video import VideoCreate, VideoUpdate, VideoResponse, VideoListResponse, VideoListPaginatedResponse
from app.schemas.thumbnail import ThumbnailResponse, ThumbnailSelect
from app.schemas.tag import TagSimple, VideoTagCreate, VideoTagUpdate
from app.services.video_service import video_service
from app.services.thumbnail_service import thumbnail_service
from app.services.tag_service import tag_service
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
    tag_ids: str = Query(None, description="Comma-separated tag IDs to filter by"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all ready videos

    - **skip**: Number of videos to skip (pagination)
    - **limit**: Maximum number of videos to return
    - **tag_ids**: Comma-separated tag IDs (e.g., "1,2,3")
    """
    # Parse tag IDs if provided
    tag_id_list = None
    if tag_ids:
        try:
            tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag_ids format. Use comma-separated integers."
            )

    videos = await video_service.get_all(
        db,
        skip=skip,
        limit=limit,
        status=VideoStatus.READY,
        tag_ids=tag_id_list
    )

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


@router.get("/paginated", response_model=VideoListPaginatedResponse)
async def list_videos_paginated(
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of videos per page"),
    tag_ids: str = Query(None, description="Comma-separated tag IDs to filter by"),
    sort_by: str = Query("created_at", regex="^(created_at|view_count|rating)$", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of all ready videos with total count

    - **page**: Page number (starting from 1)
    - **page_size**: Number of videos per page
    - **tag_ids**: Comma-separated tag IDs (e.g., "1,2,3")
    - **sort_by**: Sort field (created_at, view_count, rating)
    - **order**: Sort order (asc, desc)
    """
    # Parse tag IDs if provided
    tag_id_list = None
    if tag_ids:
        try:
            tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag_ids format. Use comma-separated integers."
            )

    # Calculate skip value
    skip = (page - 1) * page_size

    # Get total count first
    total = await video_service.count_all(
        db,
        status=VideoStatus.READY,
        tag_ids=tag_id_list
    )

    # Then get videos
    videos = await video_service.get_all(
        db,
        skip=skip,
        limit=page_size,
        status=VideoStatus.READY,
        tag_ids=tag_id_list,
        sort_by=sort_by,
        order=order
    )

    # Transform to include uploader username
    items = []
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
        items.append(VideoListResponse(**video_dict))

    # Calculate total pages
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return VideoListPaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/search", response_model=List[VideoListResponse])
async def search_videos(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    sort_by: str = Query("created_at", regex="^(created_at|view_count|title)$", description="Sort field"),
    include_tags: Optional[str] = Query(None, description="Comma-separated tag IDs to include (OR condition)"),
    exclude_tags: Optional[str] = Query(None, description="Comma-separated tag IDs to exclude"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search videos by title, description, or uploader username with advanced tag filtering

    - **q**: Search query (required, min 1 character)
    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum results (default: 20, max: 100)
    - **sort_by**: Sort field - created_at (default), view_count, or title
    - **include_tags**: Tag IDs that must be present (OR condition, e.g., "1,3,5")
    - **exclude_tags**: Tag IDs that must NOT be present (e.g., "2,4")

    Search is case-insensitive and searches in:
    - Video title
    - Video description
    - Uploader username

    Tag Filtering:
    - include_tags: Videos must have AT LEAST ONE of these tags
    - exclude_tags: Videos must NOT have ANY of these tags
    - Both can be used together

    Examples:
    - /api/v1/videos/search?q=dance
    - /api/v1/videos/search?q=k-pop&sort_by=view_count
    - /api/v1/videos/search?q=직캠&include_tags=1,3
    - /api/v1/videos/search?q=music&include_tags=1&exclude_tags=5,6
    """
    # Parse include_tags if provided
    parsed_include_tags = None
    if include_tags:
        try:
            parsed_include_tags = [int(tid) for tid in include_tags.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid include_tags format. Use comma-separated integers."
            )

    # Parse exclude_tags if provided
    parsed_exclude_tags = None
    if exclude_tags:
        try:
            parsed_exclude_tags = [int(tid) for tid in exclude_tags.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid exclude_tags format. Use comma-separated integers."
            )

    # Search videos
    videos = await video_service.search(
        db=db,
        query_text=q,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        include_tags=parsed_include_tags,
        exclude_tags=parsed_exclude_tags
    )

    # Format response
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


@router.post("/{video_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def increment_view(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Increment view count for a video

    - **video_id**: Video ID

    This endpoint should be called once when the video player starts playing.
    """
    video = await video_service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    await video_service.increment_view_count(db, video)
    return None


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream video file with HTTP Range Request support for seeking

    - **video_id**: Video ID

    Supports:
    - Range requests (206 Partial Content)
    - Video seeking/scrubbing
    - Bandwidth optimization
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

    # Get file size
    file_size = os.path.getsize(video.file_path)

    # Parse Range header
    range_header = request.headers.get("range")

    # Increment view count (only on initial request, not on range requests)
    if not range_header:
        await video_service.increment_view_count(db, video)

    # URL encode filename for Content-Disposition header
    encoded_filename = quote(f"{video.title}{Path(video.file_path).suffix}")

    # Handle Range Request
    if range_header:
        # Parse range header (format: "bytes=start-end")
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        end = min(end, file_size - 1)

        # Calculate content length
        content_length = end - start + 1

        # Stream partial content
        def iterfile_range():
            with open(video.file_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                chunk_size = 1024 * 1024  # 1MB chunks

                while remaining > 0:
                    chunk = f.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iterfile_range(),
            status_code=206,  # Partial Content
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
            }
        )

    # No Range header - stream entire file
    def iterfile():
        with open(video.file_path, "rb") as f:
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
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


# Tag endpoints

@router.get("/{video_id}/tags", response_model=List[TagSimple])
async def get_video_tags(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tags for a video

    - **video_id**: Video ID
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.video import Video

    result = await db.execute(
        select(Video).options(selectinload(Video.tags)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return video.tags


@router.post("/{video_id}/tags", response_model=List[TagSimple])
async def add_tags_to_video(
    video_id: int,
    tag_data: VideoTagCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add tags to a video (uploader only)

    - **video_id**: Video ID
    - **tag_ids**: List of tag IDs to add
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.video import Video

    result = await db.execute(
        select(Video).options(selectinload(Video.tags)).where(Video.id == video_id)
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

    tags = await tag_service.add_tags_to_video(db, video, tag_data.tag_ids)
    return tags


@router.put("/{video_id}/tags", response_model=List[TagSimple])
async def update_video_tags(
    video_id: int,
    tag_data: VideoTagUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update video tags (replace all existing tags)

    - **video_id**: Video ID
    - **tag_ids**: List of tag IDs (replaces all existing)
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.video import Video

    result = await db.execute(
        select(Video).options(selectinload(Video.tags)).where(Video.id == video_id)
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

    tags = await tag_service.set_video_tags(db, video, tag_data.tag_ids)
    return tags


@router.delete("/{video_id}/tags/{tag_id}", response_model=List[TagSimple])
async def remove_tag_from_video(
    video_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a tag from a video (uploader only)

    - **video_id**: Video ID
    - **tag_id**: Tag ID to remove
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.video import Video

    result = await db.execute(
        select(Video).options(selectinload(Video.tags)).where(Video.id == video_id)
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

    tags = await tag_service.remove_tags_from_video(db, video, [tag_id])
    return tags
