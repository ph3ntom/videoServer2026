import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/common/Layout';
import VideoCard from '../components/video/VideoCard';
import apiClient from '../services/api.client';

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
}

interface TopRatedVideo {
  video: Video;
  avg_rating: number;
  rating_count: number;
}

const ITEMS_PER_PAGE = 20;
const TOTAL_PAGES = 5;

export default function TopRatedVideos() {
  const [topRatedVideos, setTopRatedVideos] = useState<TopRatedVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadTopRatedVideos();
  }, [currentPage]);

  const loadTopRatedVideos = async () => {
    setLoading(true);
    setError('');

    try {
      const skip = (currentPage - 1) * ITEMS_PER_PAGE;
      const response = await apiClient.get(
        `/statistics/top-rated?limit=${ITEMS_PER_PAGE}&skip=${skip}&min_ratings=1`
      );
      setTopRatedVideos(response.data);
    } catch (err: any) {
      setError('높은 평점 동영상을 불러오는데 실패했습니다');
      console.error('Failed to load top rated videos:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/videos"
            className="text-indigo-400 hover:text-indigo-300 mb-4 inline-flex items-center"
          >
            ← 뒤로 가기
          </Link>
          <div className="flex items-center gap-3 mt-4">
            <h1 className="text-3xl font-bold text-white">높은 평점</h1>
            <span className="text-sm text-gray-400 bg-gray-800 px-3 py-1 rounded-full">
              평균 평점 기준
            </span>
          </div>
          <p className="text-gray-400 mt-2">
            가장 높은 평점을 받은 동영상을 확인하세요
          </p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
          </div>
        ) : topRatedVideos.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-400 text-lg">아직 평점이 등록된 동영상이 없습니다</p>
          </div>
        ) : (
          <>
            {/* Video Grid - 4 columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {topRatedVideos.map((item) => (
                <div key={item.video.id} className="relative">
                  <VideoCard video={item.video} />
                  {/* Rating Badge */}
                  <div className="absolute top-2 right-2 bg-yellow-500 text-gray-900 px-2 py-1 rounded-md text-xs font-bold flex items-center gap-1 shadow-lg">
                    <span>★</span>
                    <span>{item.avg_rating.toFixed(1)}</span>
                    <span className="text-gray-700">({item.rating_count})</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex justify-center items-center gap-2 mt-12">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-gray-800 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
              >
                이전
              </button>

              <div className="flex gap-2">
                {Array.from({ length: TOTAL_PAGES }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-4 py-2 rounded-md transition-colors ${
                      currentPage === page
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === TOTAL_PAGES}
                className="px-4 py-2 bg-gray-800 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
              >
                다음
              </button>
            </div>

            {/* Page Info */}
            <div className="text-center mt-4 text-gray-400 text-sm">
              페이지 {currentPage} / {TOTAL_PAGES}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
