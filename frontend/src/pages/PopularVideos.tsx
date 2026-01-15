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

const ITEMS_PER_PAGE = 20;
const TOTAL_PAGES = 5;

export default function PopularVideos() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadPopularVideos();
  }, [currentPage]);

  const loadPopularVideos = async () => {
    setLoading(true);
    setError('');

    try {
      const skip = (currentPage - 1) * ITEMS_PER_PAGE;
      const response = await apiClient.get(`/statistics/popular?limit=${ITEMS_PER_PAGE}&skip=${skip}`);
      setVideos(response.data);
    } catch (err: any) {
      setError('인기 동영상을 불러오는데 실패했습니다');
      console.error('Failed to load popular videos:', err);
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
            <h1 className="text-3xl font-bold text-white">인기 동영상</h1>
            <span className="text-sm text-gray-400 bg-gray-800 px-3 py-1 rounded-full">
              조회수 기준
            </span>
          </div>
          <p className="text-gray-400 mt-2">
            가장 많이 조회된 동영상을 확인하세요
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
        ) : videos.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-400 text-lg">아직 인기 동영상이 없습니다</p>
          </div>
        ) : (
          <>
            {/* Video Grid - 4 columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {videos.map((video) => (
                <VideoCard key={video.id} video={video} />
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
