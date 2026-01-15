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

interface PaginatedResponse {
  items: Video[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const ITEMS_PER_PAGE = 20;

export default function AllVideos() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [sortBy, setSortBy] = useState<'created_at' | 'view_count' | 'rating'>('created_at');

  useEffect(() => {
    loadVideos();
  }, [currentPage, sortBy]);

  const loadVideos = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await apiClient.get<PaginatedResponse>(
        `/videos/paginated?page=${currentPage}&page_size=${ITEMS_PER_PAGE}&sort_by=${sortBy}&order=desc`
      );
      setVideos(response.data.items);
      setTotal(response.data.total);
      setTotalPages(response.data.total_pages);
    } catch (err: any) {
      setError('비디오 목록을 불러오는데 실패했습니다');
      console.error('Failed to load videos:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 7; // Show max 7 page buttons

    if (totalPages <= maxVisible) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (currentPage > 3) {
        pages.push('...');
      }

      // Show pages around current
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('...');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
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
          <div className="flex items-center justify-between mt-4">
            <div>
              <h1 className="text-3xl font-bold text-white">모든 비디오</h1>
              <p className="text-gray-400 mt-2">
                전체 {total.toLocaleString()}개의 비디오
              </p>
            </div>
            {/* Sort Dropdown */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">정렬:</label>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value as 'created_at' | 'view_count' | 'rating');
                  setCurrentPage(1); // Reset to first page when sorting changes
                }}
                className="bg-gray-800 text-white px-4 py-2 rounded-md border border-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="created_at">최신순</option>
                <option value="view_count">조회수순</option>
                <option value="rating">평점순</option>
              </select>
            </div>
          </div>
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
            <p className="text-gray-400 text-lg">아직 업로드된 비디오가 없습니다</p>
            <Link
              to="/upload"
              className="inline-block mt-4 px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              첫 비디오 업로드하기
            </Link>
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
            {totalPages > 1 && (
              <div className="flex flex-col items-center gap-4 mt-12">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-gray-800 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
                  >
                    이전
                  </button>

                  <div className="flex gap-2">
                    {getPageNumbers().map((page, index) => {
                      if (page === '...') {
                        return (
                          <span key={`ellipsis-${index}`} className="px-3 py-2 text-gray-400">
                            ...
                          </span>
                        );
                      }
                      return (
                        <button
                          key={page}
                          onClick={() => handlePageChange(page as number)}
                          className={`px-4 py-2 rounded-md transition-colors ${
                            currentPage === page
                              ? 'bg-indigo-600 text-white'
                              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                          }`}
                        >
                          {page}
                        </button>
                      );
                    })}
                  </div>

                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 bg-gray-800 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
                  >
                    다음
                  </button>
                </div>

                {/* Page Info */}
                <div className="text-center text-gray-400 text-sm">
                  페이지 {currentPage} / {totalPages} ({total.toLocaleString()}개 비디오)
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
