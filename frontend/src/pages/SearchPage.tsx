import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
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

interface Tag {
  id: number;
  name: string;
  slug: string;
  color: string;
  type: string;
}

type SortOption = 'created_at' | 'view_count' | 'title';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [videos, setVideos] = useState<Video[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [includeTags, setIncludeTags] = useState<number[]>([]);
  const [excludeTags, setExcludeTags] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const query = searchParams.get('q') || '';
  const sortBy = (searchParams.get('sort_by') as SortOption) || 'created_at';

  useEffect(() => {
    loadTags();
  }, []);

  useEffect(() => {
    if (query) {
      searchVideos();
    }
  }, [query, sortBy, includeTags, excludeTags]);

  const loadTags = async () => {
    try {
      const response = await apiClient.get('/tags/popular?limit=20');
      setTags(response.data);
    } catch (err: any) {
      console.error('Failed to load tags:', err);
    }
  };

  const searchVideos = async () => {
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams({
        q: query,
        sort_by: sortBy,
      });

      if (includeTags.length > 0) {
        params.append('include_tags', includeTags.join(','));
      }

      if (excludeTags.length > 0) {
        params.append('exclude_tags', excludeTags.join(','));
      }

      const response = await apiClient.get(`/videos/search?${params.toString()}`);
      setVideos(response.data);
    } catch (err: any) {
      setError('검색에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleSortChange = (newSort: SortOption) => {
    setSearchParams({ q: query, sort_by: newSort });
  };

  const handleTagInclude = (tagId: number) => {
    if (includeTags.includes(tagId)) {
      setIncludeTags(includeTags.filter(id => id !== tagId));
    } else {
      setIncludeTags([...includeTags, tagId]);
      // Remove from exclude if it was there
      setExcludeTags(excludeTags.filter(id => id !== tagId));
    }
  };

  const handleTagExclude = (tagId: number) => {
    if (excludeTags.includes(tagId)) {
      setExcludeTags(excludeTags.filter(id => id !== tagId));
    } else {
      setExcludeTags([...excludeTags, tagId]);
      // Remove from include if it was there
      setIncludeTags(includeTags.filter(id => id !== tagId));
    }
  };

  const clearFilters = () => {
    setIncludeTags([]);
    setExcludeTags([]);
  };

  const getTagState = (tagId: number): 'include' | 'exclude' | 'none' => {
    if (includeTags.includes(tagId)) return 'include';
    if (excludeTags.includes(tagId)) return 'exclude';
    return 'none';
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Search Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            검색 결과: "{query}"
          </h1>
          <p className="text-gray-400">
            {loading ? '검색 중...' : `${videos.length}개의 비디오`}
          </p>
        </div>

        <div className="flex gap-6">
          {/* Sidebar Filters */}
          <aside className="w-64 flex-shrink-0">
            {/* Sort Options */}
            <div className="bg-gray-800 rounded-lg p-4 mb-4">
              <h2 className="text-sm font-medium text-gray-300 mb-3">정렬</h2>
              <div className="space-y-2">
                <button
                  onClick={() => handleSortChange('created_at')}
                  className={`w-full text-left px-3 py-2 rounded ${
                    sortBy === 'created_at'
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  최신순
                </button>
                <button
                  onClick={() => handleSortChange('view_count')}
                  className={`w-full text-left px-3 py-2 rounded ${
                    sortBy === 'view_count'
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  인기순
                </button>
                <button
                  onClick={() => handleSortChange('title')}
                  className={`w-full text-left px-3 py-2 rounded ${
                    sortBy === 'title'
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  제목순
                </button>
              </div>
            </div>

            {/* Tag Filters */}
            {tags.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <h2 className="text-sm font-medium text-gray-300">태그 필터</h2>
                  {(includeTags.length > 0 || excludeTags.length > 0) && (
                    <button
                      onClick={clearFilters}
                      className="text-xs text-indigo-400 hover:text-indigo-300"
                    >
                      초기화
                    </button>
                  )}
                </div>

                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {tags.map(tag => {
                    const state = getTagState(tag.id);
                    return (
                      <div
                        key={tag.id}
                        className="flex items-center gap-2 p-2 rounded hover:bg-gray-700"
                      >
                        <button
                          onClick={() => handleTagInclude(tag.id)}
                          className={`flex-1 text-left px-2 py-1 rounded text-sm ${
                            state === 'include'
                              ? 'ring-2 ring-green-500'
                              : state === 'exclude'
                              ? 'opacity-50'
                              : ''
                          }`}
                          style={{
                            backgroundColor: state === 'include' ? tag.color : tag.color + '20',
                            color: state === 'include' ? '#fff' : tag.color,
                          }}
                        >
                          {tag.name}
                        </button>
                        <button
                          onClick={() => handleTagExclude(tag.id)}
                          className={`px-2 py-1 rounded text-xs ${
                            state === 'exclude'
                              ? 'bg-red-600 text-white'
                              : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                          }`}
                          title="제외"
                        >
                          {state === 'exclude' ? '✕' : '−'}
                        </button>
                      </div>
                    );
                  })}
                </div>

                {/* Active Filters Summary */}
                {(includeTags.length > 0 || excludeTags.length > 0) && (
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <p className="text-xs text-gray-400 mb-2">적용된 필터:</p>
                    {includeTags.length > 0 && (
                      <div className="mb-2">
                        <span className="text-xs text-green-400">포함: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {includeTags.map(tagId => {
                            const tag = tags.find(t => t.id === tagId);
                            return tag ? (
                              <span
                                key={tagId}
                                className="text-xs px-2 py-0.5 rounded"
                                style={{ backgroundColor: tag.color, color: '#fff' }}
                              >
                                {tag.name}
                              </span>
                            ) : null;
                          })}
                        </div>
                      </div>
                    )}
                    {excludeTags.length > 0 && (
                      <div>
                        <span className="text-xs text-red-400">제외: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {excludeTags.map(tagId => {
                            const tag = tags.find(t => t.id === tagId);
                            return tag ? (
                              <span
                                key={tagId}
                                className="text-xs px-2 py-0.5 rounded bg-red-600 text-white"
                              >
                                {tag.name}
                              </span>
                            ) : null;
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </aside>

          {/* Main Content */}
          <main className="flex-1">
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
                <p className="text-gray-400 text-lg mb-4">
                  검색 결과가 없습니다
                </p>
                <p className="text-gray-500 text-sm">
                  다른 검색어를 시도하거나 필터를 변경해보세요
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {videos.map((video) => (
                  <VideoCard key={video.id} video={video} />
                ))}
              </div>
            )}
          </main>
        </div>
      </div>
    </Layout>
  );
}
