import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import Layout from '../components/common/Layout';
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

export default function VideoPlayer() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const [video, setVideo] = useState<Video | null>(null);
  const [thumbnails, setThumbnails] = useState<Thumbnail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [uploadingThumbnail, setUploadingThumbnail] = useState(false);
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

  // Initialize Video.js player
  useEffect(() => {
    if (!video || !videoRef.current) return;

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
      player.ready(() => {
        console.log('Video.js player is ready');
      });
    }

    // Cleanup
    return () => {
      if (playerRef.current) {
        playerRef.current.dispose();
        playerRef.current = null;
      }
    };
  }, [video]);

  const loadVideo = async (videoId: number) => {
    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get(`/videos/${videoId}`);
      setVideo(response.data);
      loadThumbnails(videoId);
    } catch (err: any) {
      setError('비디오를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
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
        <div className="bg-black rounded-lg overflow-hidden mb-6">
          <div ref={videoRef} />
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
      </div>
    </Layout>
  );
}
