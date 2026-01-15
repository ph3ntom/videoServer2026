import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/common/Layout';
import VideoCard from '../components/video/VideoCard';
import apiClient from '../services/api.client';
import { useAuthStore } from '../store/authStore';

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
  watch_progress?: number;
}

interface ContinueWatchingItem {
  video_id: number;
  video_title: string;
  video_description: string | null;
  video_duration: number | null;
  video_thumbnail_path: string | null;
  uploader_username: string;
  watch_position: number;
  progress_percentage: number;
  last_watched_at: string;
}

interface TopRatedVideo {
  video: Video;
  avg_rating: number;
  rating_count: number;
}

interface Tag {
  id: number;
  name: string;
  slug: string;
  color: string;
  video_count: number;
}

export default function Videos() {
  const { user } = useAuthStore();
  const [videos, setVideos] = useState<Video[]>([]);
  const [continueWatching, setContinueWatching] = useState<ContinueWatchingItem[]>([]);
  const [popularVideos, setPopularVideos] = useState<Video[]>([]);
  const [topRatedVideos, setTopRatedVideos] = useState<TopRatedVideo[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedTag, setSelectedTag] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadVideos();
    loadPopularTags();
    loadPopularVideos();
    loadTopRatedVideos();
    if (user) {
      loadContinueWatching();
    }
  }, [user]);

  useEffect(() => {
    loadVideos();
  }, [selectedTag]);

  const loadVideos = async () => {
    setLoading(true);
    setError('');

    try {
      const params = selectedTag ? `?tag_ids=${selectedTag}&limit=4` : '?limit=4';
      const response = await apiClient.get(`/videos/${params}`);
      setVideos(response.data);
    } catch (err: any) {
      setError('비디오 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadPopularTags = async () => {
    try {
      const response = await apiClient.get('/tags/popular?limit=10');
      setTags(response.data);
    } catch (err: any) {
      console.error('Failed to load tags:', err);
    }
  };

  const loadContinueWatching = async () => {
    try {
      const response = await apiClient.get('/videos/continue-watching?limit=6');
      setContinueWatching(response.data);
    } catch (err: any) {
      console.error('Failed to load continue watching:', err);
    }
  };

  const loadPopularVideos = async () => {
    try {
      const response = await apiClient.get('/statistics/popular?limit=4');
      setPopularVideos(response.data);
    } catch (err: any) {
      console.error('Failed to load popular videos:', err);
    }
  };

  const loadTopRatedVideos = async () => {
    try {
      const response = await apiClient.get('/statistics/top-rated?limit=4&min_ratings=1');
      setTopRatedVideos(response.data);
    } catch (err: any) {
      console.error('Failed to load top rated videos:', err);
    }
  };

  const handleTagClick = (tagId: number) => {
    setSelectedTag(selectedTag === tagId ? null : tagId);
  };

  // Transform continue watching to Video format
  const continueWatchingVideos: Video[] = continueWatching.map(item => ({
    id: item.video_id,
    title: item.video_title,
    description: item.video_description,
    file_size: null,
    thumbnail_path: item.video_thumbnail_path,
    duration: item.video_duration,
    width: null,
    height: null,
    status: 'ready',
    view_count: 0,
    created_at: item.last_watched_at,
    uploader_username: item.uploader_username,
    watch_progress: item.progress_percentage
  }));


  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">비디오</h1>
          <Link
            to="/upload"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            + 비디오 업로드
          </Link>
        </div>

        {/* Tag Filter */}
        {tags.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-medium text-gray-400 mb-3">인기 태그</h2>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedTag(null)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedTag === null
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                전체
              </button>
              {tags.map(tag => (
                <button
                  key={tag.id}
                  onClick={() => handleTagClick(tag.id)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    selectedTag === tag.id
                      ? 'ring-2 ring-offset-2 ring-offset-gray-900'
                      : 'hover:opacity-80'
                  }`}
                  style={{
                    backgroundColor: selectedTag === tag.id ? tag.color : tag.color + '40',
                    color: selectedTag === tag.id ? '#fff' : tag.color,
                    border: `1px solid ${tag.color}`
                  }}
                >
                  {tag.name} ({tag.video_count})
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Popular Videos Section */}
        {popularVideos.length > 0 && (
          <div className="mb-12">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-bold text-white">인기 비디오</h2>
                <span className="text-sm text-gray-400">조회수 기준</span>
              </div>
              <Link
                to="/videos/popular"
                className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center gap-1"
              >
                더보기 →
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {popularVideos.map((video) => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>
          </div>
        )}

        {/* Top Rated Videos Section */}
        {topRatedVideos.length > 0 && (
          <div className="mb-12">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-bold text-white">높은 평점</h2>
                <span className="text-sm text-gray-400">평균 평점 기준</span>
              </div>
              <Link
                to="/videos/top-rated"
                className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center gap-1"
              >
                더보기 →
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {topRatedVideos.map((item) => (
                <div key={item.video.id} className="relative">
                  <VideoCard video={item.video} />
                  <div className="absolute top-2 right-2 bg-yellow-500 text-gray-900 px-2 py-1 rounded-md text-xs font-bold flex items-center gap-1">
                    <span>★</span>
                    <span>{item.avg_rating.toFixed(1)}</span>
                    <span className="text-gray-700">({item.rating_count})</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Continue Watching Section */}
        {user && continueWatchingVideos.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-white mb-4">이어보기</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {continueWatchingVideos.map((video) => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* All Videos Section */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">
            {selectedTag ? '필터링된 비디오' : '모든 비디오'}
          </h2>
          {!selectedTag && (
            <Link
              to="/videos/all"
              className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center gap-1"
            >
              더보기 →
            </Link>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-400 text-lg mb-4">아직 업로드된 비디오가 없습니다</p>
            <Link
              to="/upload"
              className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              첫 비디오 업로드하기
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {videos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
