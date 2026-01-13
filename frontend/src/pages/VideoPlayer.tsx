import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import Layout from '../components/common/Layout';
import TagSelector from '../components/tag/TagSelector';
import VideoCard from '../components/video/VideoCard';
import StarRating from '../components/rating/StarRating';
import apiClient from '../services/api.client';
import { useAuthStore } from '../store/authStore';

import type Player from 'video.js/dist/types/player';

interface Video {
  id: number;
  user_id: number;
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
}

interface Thumbnail {
  id: number;
  video_id: number;
  file_path: string;
  is_auto_generated: boolean;
  is_selected: boolean;
  created_at: string;
}

interface Tag {
  id: number;
  name: string;
  slug: string;
  color: string;
}

interface RelatedVideo {
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
}

interface RatingStats {
  avg_rating: number;
  rating_count: number;
  user_rating: number | null;
}

export default function VideoPlayer() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const [video, setVideo] = useState<Video | null>(null);
  const [thumbnails, setThumbnails] = useState<Thumbnail[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [relatedVideos, setRelatedVideos] = useState<RelatedVideo[]>([]);
  const [ratingStats, setRatingStats] = useState<RatingStats>({
    avg_rating: 0,
    rating_count: 0,
    user_rating: null
  });
  const [editingTags, setEditingTags] = useState(false);
  const [tempTags, setTempTags] = useState<Tag[]>([]);
  const [savingTags, setSavingTags] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [uploadingThumbnail, setUploadingThumbnail] = useState(false);
  const [showResumePrompt, setShowResumePrompt] = useState(false);
  const [resumePosition, setResumePosition] = useState(0);
  const navigate = useNavigate();
  const { user} = useAuthStore();
  const videoRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<Player | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (id) {
      loadVideo(parseInt(id));
    }
  }, [id]);

  // Reload rating stats when user changes (login/logout)
  useEffect(() => {
    if (video) {
      loadRatingStats(video.id);
    }
  }, [user, video?.id]);

  // Initialize Video.js player
  useEffect(() => {
    if (!video || !videoRef.current) return;

    let saveProgressInterval: NodeJS.Timeout;

    // Make sure Video.js player is only initialized once
    if (!playerRef.current) {
      const videoElement = document.createElement('video-js');
      videoElement.classList.add('vjs-big-play-centered');
      videoRef.current.appendChild(videoElement);

      const videoUrl = `${import.meta.env.VITE_API_BASE_URL}/api/v1/videos/${video.id}/stream`;

      const player = (playerRef.current = videojs(videoElement, {
        autoplay: false,
        controls: true,
        responsive: true,
        fluid: true,
        preload: 'auto',
        sources: [
          {
            src: videoUrl,
            type: 'video/mp4'
          }
        ]
      }));

      // Player ready event
      player.ready(async () => {
        console.log('Video.js player is ready');

        // Load watch history and show resume prompt if available
        if (user) {
          try {
            const historyResponse = await apiClient.get(`/videos/${video.id}/watch-history`);
            const watchHistory = historyResponse.data;

            // Show resume prompt if watch position is significant
            if (watchHistory.watch_position > 5 && watchHistory.progress_percentage < 95) {
              setResumePosition(watchHistory.watch_position);
              setShowResumePrompt(true);
            }
          } catch (err: any) {
            // No watch history (404 is expected)
            if (err.response?.status !== 404) {
              console.error('Failed to load watch history:', err);
            }
          }
        }
      });

      // Save progress every 10 seconds while playing
      player.on('play', () => {
        if (user) {
          saveProgressInterval = setInterval(() => {
            saveWatchProgress();
          }, 10000);
        }
      });

      // Stop saving when paused
      player.on('pause', () => {
        if (saveProgressInterval) {
          clearInterval(saveProgressInterval);
        }
        // Save one last time when paused
        if (user) {
          saveWatchProgress();
        }
      });

      // Save when video ends
      player.on('ended', () => {
        if (saveProgressInterval) {
          clearInterval(saveProgressInterval);
        }
        if (user) {
          saveWatchProgress();
        }
      });
    }

    // Cleanup
    return () => {
      if (saveProgressInterval) {
        clearInterval(saveProgressInterval);
      }
      if (playerRef.current) {
        playerRef.current.dispose();
        playerRef.current = null;
      }
    };
  }, [video, user]);

  const saveWatchProgress = async () => {
    if (!playerRef.current || !video || !user) return;

    try {
      const currentTime = Math.floor(playerRef.current.currentTime());
      const duration = Math.floor(playerRef.current.duration());

      await apiClient.post(`/videos/${video.id}/watch-history`, {
        watch_position: currentTime,
        watch_duration: duration
      });
    } catch (err) {
      console.error('Failed to save watch progress:', err);
    }
  };

  const handleResumeVideo = () => {
    if (playerRef.current && resumePosition > 0) {
      playerRef.current.currentTime(resumePosition);
      setShowResumePrompt(false);
    }
  };

  const handleStartFromBeginning = () => {
    if (playerRef.current) {
      playerRef.current.currentTime(0);
      setShowResumePrompt(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const loadVideo = async (videoId: number) => {
    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get(`/videos/${videoId}`);
      setVideo(response.data);
      loadThumbnails(videoId);
      loadTags(videoId);
      loadRatingStats(videoId);
    } catch (err: any) {
      setError('비디오를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadRatingStats = async (videoId: number) => {
    try {
      const response = await apiClient.get(`/videos/${videoId}/rating/stats`);
      setRatingStats(response.data);

      // If user is logged in, get their specific rating
      if (user) {
        try {
          const userRatingResponse = await apiClient.get(`/videos/${videoId}/rating`);
          setRatingStats(prev => ({
            ...prev,
            user_rating: userRatingResponse.data.score
          }));
        } catch (err: any) {
          // User hasn't rated yet (404 is expected)
          if (err.response?.status !== 404) {
            console.error('Failed to load user rating:', err);
          }
        }
      }
    } catch (err: any) {
      console.error('Failed to load rating stats:', err);
    }
  };

  const handleRate = async (score: number) => {
    if (!video || !user) {
      alert('로그인이 필요합니다');
      return;
    }

    try {
      await apiClient.post(`/videos/${video.id}/rating`, { score });

      // Reload rating stats to reflect the new rating
      await loadRatingStats(video.id);
    } catch (err: any) {
      alert('평가 등록에 실패했습니다');
      throw err;
    }
  };

  const loadTags = async (videoId: number) => {
    try {
      const response = await apiClient.get(`/videos/${videoId}/tags`);
      setTags(response.data);
      // Load related videos after tags are loaded
      if (response.data.length > 0) {
        loadRelatedVideos(response.data.map((tag: Tag) => tag.id));
      }
    } catch (err: any) {
      console.error('Failed to load tags:', err);
    }
  };

  const loadRelatedVideos = async (tagIds: number[]) => {
    try {
      if (tagIds.length === 0) return;

      // Get videos with same tags, excluding current video
      const response = await apiClient.get(`/videos`, {
        params: {
          tag_ids: tagIds.join(','),
          limit: 6
        }
      });

      // Filter out current video
      const filtered = response.data.filter((v: RelatedVideo) => v.id !== parseInt(id || '0'));
      setRelatedVideos(filtered.slice(0, 4)); // Show max 4 related videos
    } catch (err: any) {
      console.error('Failed to load related videos:', err);
    }
  };

  const loadThumbnails = async (videoId: number) => {
    try {
      const response = await apiClient.get(`/videos/${videoId}/thumbnails`);
      setThumbnails(response.data);

      // Check if we should auto-show thumbnails
      const shouldSelectThumbnail = searchParams.get('selectThumbnail') === 'true';
      if (shouldSelectThumbnail && response.data.length > 0) {
        setShowThumbnails(true);
      }
    } catch (err: any) {
      console.error('Failed to load thumbnails:', err);
    }
  };

  const handleSelectThumbnail = async (thumbnailId: number) => {
    if (!video) return;

    try {
      await apiClient.post(`/videos/${video.id}/thumbnails/select`, {
        thumbnail_id: thumbnailId
      });

      // Reload video and thumbnails
      await loadVideo(video.id);
      alert('썸네일이 선택되었습니다');
    } catch (err: any) {
      alert('썸네일 선택에 실패했습니다');
    }
  };

  const handleUploadThumbnail = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !video) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert('이미지 파일만 업로드 가능합니다 (JPG, PNG, WebP)');
      return;
    }

    // Validate file size (max 20MB)
    if (file.size > 20 * 1024 * 1024) {
      alert('파일 크기는 20MB 이하여야 합니다');
      return;
    }

    setUploadingThumbnail(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      await apiClient.post(`/videos/${video.id}/thumbnails/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Reload thumbnails
      await loadThumbnails(video.id);
      alert('커스텀 썸네일이 업로드되었습니다');

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      alert('썸네일 업로드에 실패했습니다');
    } finally {
      setUploadingThumbnail(false);
    }
  };

  const handleDelete = async () => {
    if (!video || !window.confirm('정말로 이 비디오를 삭제하시겠습니까?')) {
      return;
    }

    setDeleting(true);
    try {
      await apiClient.delete(`/videos/${video.id}`);
      navigate('/videos');
    } catch (err: any) {
      alert('비디오 삭제에 실패했습니다');
      setDeleting(false);
    }
  };

  const handleEditTags = () => {
    setTempTags([...tags]);
    setEditingTags(true);
  };

  const handleCancelEditTags = () => {
    setTempTags([]);
    setEditingTags(false);
  };

  const handleSaveTags = async () => {
    if (!video) return;

    setSavingTags(true);
    try {
      await apiClient.put(`/videos/${video.id}/tags`, {
        tag_ids: tempTags.map(tag => tag.id)
      });
      setTags(tempTags);
      setEditingTags(false);
      alert('태그가 저장되었습니다');
    } catch (err: any) {
      alert('태그 저장에 실패했습니다');
    } finally {
      setSavingTags(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR');
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      </Layout>
    );
  }

  if (error || !video) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded">
            {error || '비디오를 찾을 수 없습니다'}
          </div>
        </div>
      </Layout>
    );
  }

  const isOwner = user?.id === video.user_id;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Video Player */}
        <div className="bg-black rounded-lg overflow-hidden mb-6 relative">
          <div ref={videoRef} />

          {/* Resume Watching Prompt */}
          {showResumePrompt && (
            <div className="absolute inset-0 bg-black/80 flex items-center justify-center z-50">
              <div className="bg-gray-800 rounded-lg p-6 max-w-md mx-4 border border-gray-700">
                <h3 className="text-white text-xl font-bold mb-3">
                  이어보기
                </h3>
                <p className="text-gray-300 mb-6">
                  이전에 <span className="text-indigo-400 font-semibold">{formatTime(resumePosition)}</span>까지 시청하셨습니다.
                  <br />
                  이어서 보시겠습니까?
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={handleResumeVideo}
                    className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-medium transition-colors"
                  >
                    이어보기
                  </button>
                  <button
                    onClick={handleStartFromBeginning}
                    className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-md hover:bg-gray-600 font-medium transition-colors"
                  >
                    처음부터 보기
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Video Info */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white mb-2">{video.title}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-400">
                <span>{video.view_count} 조회</span>
                <span>{formatDate(video.created_at)}</span>
              </div>
            </div>

            {isOwner && (
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? '삭제 중...' : '삭제'}
              </button>
            )}
          </div>

          {video.description && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <h3 className="text-white font-semibold mb-2">설명</h3>
              <p className="text-gray-300 whitespace-pre-wrap">{video.description}</p>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-gray-700 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {video.duration && (
              <div>
                <span className="text-gray-500">재생 시간</span>
                <p className="text-white">
                  {Math.floor(video.duration / 60)}분 {video.duration % 60}초
                </p>
              </div>
            )}
            {video.width && video.height && (
              <div>
                <span className="text-gray-500">해상도</span>
                <p className="text-white">
                  {video.width} x {video.height}
                </p>
              </div>
            )}
            {video.file_size && (
              <div>
                <span className="text-gray-500">파일 크기</span>
                <p className="text-white">
                  {(video.file_size / (1024 * 1024)).toFixed(1)} MB
                </p>
              </div>
            )}
            <div>
              <span className="text-gray-500">상태</span>
              <p className="text-white capitalize">{video.status}</p>
            </div>
          </div>

          {/* Tags Section */}
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-white font-semibold">태그</h3>
              {isOwner && !editingTags && (
                <button
                  onClick={handleEditTags}
                  className="text-sm text-indigo-400 hover:text-indigo-300"
                >
                  편집
                </button>
              )}
            </div>

            {editingTags ? (
              <div className="space-y-4">
                <TagSelector
                  selectedTags={tempTags}
                  onTagsChange={setTempTags}
                  maxTags={10}
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveTags}
                    disabled={savingTags}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {savingTags ? '저장 중...' : '저장'}
                  </button>
                  <button
                    onClick={handleCancelEditTags}
                    disabled={savingTags}
                    className="px-4 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 disabled:opacity-50"
                  >
                    취소
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tags.length > 0 ? (
                  tags.map(tag => (
                    <span
                      key={tag.id}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                      style={{
                        backgroundColor: tag.color + '20',
                        color: tag.color,
                        border: `1px solid ${tag.color}`
                      }}
                    >
                      {tag.name}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-500 text-sm">태그가 없습니다</span>
                )}
              </div>
            )}
          </div>

          {/* Rating Section */}
          <div className="mt-4 pt-4 border-t border-gray-700">
            <h3 className="text-white font-semibold mb-3">평점</h3>
            <StarRating
              rating={ratingStats.avg_rating}
              count={ratingStats.rating_count}
              userRating={ratingStats.user_rating}
              onRate={user ? handleRate : undefined}
              readOnly={!user}
            />
          </div>
        </div>

        {/* Thumbnails Section */}
        {isOwner && thumbnails.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mt-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">썸네일 관리</h2>
              <button
                onClick={() => setShowThumbnails(!showThumbnails)}
                className="text-indigo-400 hover:text-indigo-300"
              >
                {showThumbnails ? '숨기기' : '보기'}
              </button>
            </div>

            {showThumbnails && (
              <>
                {/* Upload notification */}
                {searchParams.get('selectThumbnail') === 'true' && (
                  <div className="bg-indigo-500/10 border border-indigo-500 text-indigo-300 px-4 py-3 rounded mb-4">
                    <p className="font-medium">비디오가 성공적으로 업로드되었습니다!</p>
                    <p className="text-sm mt-1">아래에서 원하는 썸네일을 클릭하여 선택하거나, 커스텀 썸네일을 업로드하세요.</p>
                  </div>
                )}

                {/* Custom thumbnail upload */}
                <div className="mb-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/jpg,image/png,image/webp"
                    onChange={handleUploadThumbnail}
                    disabled={uploadingThumbnail}
                    className="hidden"
                    id="thumbnail-upload"
                  />
                  <label
                    htmlFor="thumbnail-upload"
                    className={`inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors cursor-pointer ${
                      uploadingThumbnail ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {uploadingThumbnail ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        업로드 중...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        커스텀 썸네일 업로드
                      </>
                    )}
                  </label>
                  <p className="text-gray-400 text-sm mt-2">
                    JPG, PNG, WebP 형식 지원 (최대 20MB)
                  </p>
                </div>

                {/* Thumbnails grid */}
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {thumbnails.map((thumbnail) => (
                    <div
                      key={thumbnail.id}
                      className={`relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                        thumbnail.is_selected
                          ? 'border-indigo-500 ring-2 ring-indigo-500'
                          : 'border-gray-700 hover:border-gray-500'
                      }`}
                      onClick={() => handleSelectThumbnail(thumbnail.id)}
                    >
                      <img
                        src={`${import.meta.env.VITE_API_BASE_URL}/api/v1/videos/${video.id}/thumbnails/${thumbnail.id}/image`}
                        alt={`Thumbnail ${thumbnail.id}`}
                        className="w-full aspect-video object-cover"
                      />
                      {thumbnail.is_selected && (
                        <div className="absolute top-1 right-1 bg-indigo-500 text-white text-xs px-2 py-1 rounded">
                          선택됨
                        </div>
                      )}
                      {!thumbnail.is_auto_generated && (
                        <div className="absolute top-1 left-1 bg-green-500 text-white text-xs px-2 py-1 rounded">
                          커스텀
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Related Videos Section */}
        {relatedVideos.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-white mb-6">관련 비디오</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {relatedVideos.map((relatedVideo) => (
                <VideoCard key={relatedVideo.id} video={relatedVideo} />
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
