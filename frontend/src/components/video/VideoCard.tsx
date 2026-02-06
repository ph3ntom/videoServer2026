import { useState, useEffect, useRef, useCallback, useMemo, memo } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../../services/api.client';

interface Video {
  id: number;
  title: string;
  description: string | null;
  file_size: number | null;
  thumbnail_path: string | null;
  duration: number | null;
  width: number | null;
  height: number | null;
  status: string;
  view_count: number;
  created_at: string;
  uploader_username: string;
  watch_progress?: number; // Progress percentage (0-100)
}

interface Thumbnail {
  id: number;
  video_id: number;
  file_path: string;
  is_auto_generated: boolean;
  is_selected: boolean;
  created_at: string;
}

interface VideoCardProps {
  video: Video;
}

function VideoCard({ video }: VideoCardProps) {
  const [thumbnails, setThumbnails] = useState<Thumbnail[]>([]);
  const [currentThumbnailIndex, setCurrentThumbnailIndex] = useState(0);
  const [isHovering, setIsHovering] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [previewClipsAvailable, setPreviewClipsAvailable] = useState(false);
  const [currentClipIndex, setCurrentClipIndex] = useState(0);
  const [isPlayingPreview, setIsPlayingPreview] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Intersection Observer for lazy loading thumbnails
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
          }
        });
      },
      { threshold: 0.1 }
    );

    if (cardRef.current) {
      observer.observe(cardRef.current);
    }

    return () => {
      if (cardRef.current) {
        observer.unobserve(cardRef.current);
      }
    };
  }, []);

  // Load thumbnails when card comes into view
  useEffect(() => {
    if (isInView && thumbnails.length === 0) {
      loadThumbnails();
      checkPreviewClips();
    }
  }, [isInView]);

  const loadThumbnails = async () => {
    try {
      const response = await apiClient.get(`/videos/${video.id}/thumbnails`);
      setThumbnails(response.data);

      // Preload thumbnail images
      response.data.forEach((thumbnail: Thumbnail) => {
        const img = new Image();
        img.src = `${import.meta.env.VITE_API_BASE_URL}/api/v1/videos/${video.id}/thumbnails/${thumbnail.id}/image`;
      });
    } catch (err) {
      console.error('Failed to load thumbnails:', err);
    }
  };

  const checkPreviewClips = async () => {
    try {
      const response = await apiClient.get(`/videos/${video.id}/preview-clips`);
      setPreviewClipsAvailable(response.data.available);
    } catch (err) {
      console.error('Failed to check preview clips:', err);
      setPreviewClipsAvailable(false);
    }
  };

  // Handle mouse enter with debounce
  const handleMouseEnter = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    // Debounce: wait 300ms before starting animation
    hoverTimeoutRef.current = setTimeout(() => {
      if (previewClipsAvailable) {
        // Play preview clips
        setIsPlayingPreview(true);
        setCurrentClipIndex(0);
      } else {
        // Fall back to thumbnail cycling
        setIsHovering(true);
        if (thumbnails.length > 1) {
          // Start cycling thumbnails every 1 second
          intervalRef.current = setInterval(() => {
            setCurrentThumbnailIndex((prev) => (prev + 1) % thumbnails.length);
          }, 1000);
        }
      }
    }, 300);
  }, [previewClipsAvailable, thumbnails.length]);

  // Handle mouse leave
  const handleMouseLeave = useCallback(() => {
    // Clear debounce timeout
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }

    // Clear interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    setIsHovering(false);
    setIsPlayingPreview(false);
    setCurrentThumbnailIndex(0);
    setCurrentClipIndex(0);
  }, []);

  // Update video src when clip index changes
  useEffect(() => {
    if (isPlayingPreview && videoRef.current) {
      // Add cache buster to force reload of new 3-second clips
      const cacheBuster = Date.now();
      const newSrc = `${import.meta.env.VITE_API_BASE_URL}/api/v1/videos/${video.id}/preview-clips/${currentClipIndex + 1}?v=${cacheBuster}`;
      console.log(`[VideoCard ${video.id}] Loading clip ${currentClipIndex + 1}/7: ${newSrc}`);
      videoRef.current.src = newSrc;
      videoRef.current.load();
      videoRef.current.play().catch(err => {
        console.error(`[VideoCard ${video.id}] Failed to play clip ${currentClipIndex + 1}:`, err);
      });
    }
  }, [currentClipIndex, isPlayingPreview, video.id]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  const formatDuration = useCallback((seconds: number | null) => {
    if (!seconds) return '알 수 없음';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }, []);

  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }, []);

  const getThumbnailUrl = useMemo(() => {
    // Use thumbnail_path as cache buster to force reload when thumbnail changes
    const cacheBuster = video.thumbnail_path
      ? encodeURIComponent(video.thumbnail_path.split('/').pop() || '')
      : Date.now();

    if (isHovering && thumbnails.length > 0) {
      const thumbnail = thumbnails[currentThumbnailIndex];
      return `${import.meta.env.VITE_API_BASE_URL}/api/v1/videos/${video.id}/thumbnails/${thumbnail.id}/image?v=${cacheBuster}`;
    }
    return `${import.meta.env.VITE_API_BASE_URL}/api/v1/videos/${video.id}/thumbnail?v=${cacheBuster}`;
  }, [isHovering, thumbnails, currentThumbnailIndex, video.id, video.thumbnail_path]);

  return (
    <Link
      to={`/videos/${video.id}`}
      ref={cardRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="bg-gray-800 rounded-lg overflow-hidden hover:ring-2 hover:ring-indigo-500 transition-all"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-gray-700 flex items-center justify-center relative overflow-hidden">
        {isPlayingPreview ? (
          <>
            {/* Preview video clip */}
            <video
              ref={videoRef}
              muted
              playsInline
              className="w-full h-full object-cover"
              onError={() => {
                // Fallback to thumbnail on error
                console.error(`[VideoCard ${video.id}] Video error`);
                setIsPlayingPreview(false);
                setPreviewClipsAvailable(false);
              }}
              onEnded={() => {
                // Move to next clip when current clip ends
                console.log(`[VideoCard ${video.id}] Clip ${currentClipIndex + 1} ended, moving to next clip`);
                setCurrentClipIndex((prev) => (prev + 1) % 7);
              }}
            />
            {/* Clip progress indicator */}
            <div className="absolute top-2 right-2 flex gap-1">
              {[...Array(7)].map((_, index) => (
                <div
                  key={index}
                  className={`h-1 rounded-full transition-all ${
                    index === currentClipIndex
                      ? 'w-4 bg-white'
                      : 'w-1 bg-white/50'
                  }`}
                />
              ))}
            </div>
          </>
        ) : video.thumbnail_path ? (
          <>
            {/* Static or cycling thumbnail images */}
            <img
              src={getThumbnailUrl}
              alt={video.title}
              className="w-full h-full object-cover transition-opacity duration-300"
              style={{ opacity: 1 }}
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
            {/* Hover indicator for thumbnail cycling */}
            {isHovering && thumbnails.length > 1 && (
              <div className="absolute top-2 right-2 flex gap-1">
                {thumbnails.map((_, index) => (
                  <div
                    key={index}
                    className={`h-1 rounded-full transition-all ${
                      index === currentThumbnailIndex
                        ? 'w-4 bg-white'
                        : 'w-1 bg-white/50'
                    }`}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <svg
            className="w-16 h-16 text-gray-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
          </svg>
        )}
        {video.duration && (
          <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
            {formatDuration(video.duration)}
          </div>
        )}
        {/* Watch progress bar */}
        {video.watch_progress && video.watch_progress > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
            <div
              className="h-full bg-red-600 transition-all"
              style={{ width: `${video.watch_progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Video info */}
      <div className="p-4">
        <h3 className="text-white font-semibold text-lg mb-2 truncate">
          {video.title}
        </h3>
        {video.description && (
          <p className="text-gray-400 text-sm mb-3 line-clamp-2">
            {video.description}
          </p>
        )}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>{video.uploader_username}</span>
          <span>{video.view_count} 조회</span>
        </div>
        <div className="flex items-center justify-between text-xs text-gray-600 mt-2">
          <span>{formatDuration(video.duration)}</span>
          <span>{formatDate(video.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

// Memoize the component to prevent unnecessary re-renders
export default memo(VideoCard);
