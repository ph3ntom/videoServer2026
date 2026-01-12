import { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/api.client';

interface Tag {
  id: number;
  name: string;
  slug: string;
  color: string;
}

interface TagSelectorProps {
  selectedTags: Tag[];
  onTagsChange: (tags: Tag[]) => void;
  maxTags?: number;
}

export default function TagSelector({ selectedTags, onTagsChange, maxTags = 10 }: TagSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Tag[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [isCreatingTag, setIsCreatingTag] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3B82F6');
  const [newTagDescription, setNewTagDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load all tags on mount
  useEffect(() => {
    loadAllTags();
  }, []);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Search tags when query changes
  useEffect(() => {
    if (searchQuery.trim().length > 0) {
      searchTags(searchQuery);
    } else {
      setSearchResults(allTags);
    }
  }, [searchQuery, allTags]);

  const loadAllTags = async () => {
    try {
      const response = await apiClient.get('/tags/');
      setAllTags(response.data);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  const searchTags = async (query: string) => {
    try {
      const response = await apiClient.get(`/tags/search?q=${encodeURIComponent(query)}`);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Failed to search tags:', error);
    }
  };

  const addTag = (tag: Tag) => {
    if (selectedTags.length >= maxTags) {
      alert(`최대 ${maxTags}개의 태그만 추가할 수 있습니다.`);
      return;
    }

    if (!selectedTags.find(t => t.id === tag.id)) {
      onTagsChange([...selectedTags, tag]);
    }
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  const removeTag = (tagId: number) => {
    onTagsChange(selectedTags.filter(t => t.id !== tagId));
  };

  const handleInputFocus = () => {
    setIsDropdownOpen(true);
  };

  const handleCreateNewTag = () => {
    setNewTagName(searchQuery);
    setNewTagColor('#3B82F6');
    setNewTagDescription('');
    setIsCreatingTag(true);
    setIsDropdownOpen(false);
  };

  const handleCancelCreate = () => {
    setIsCreatingTag(false);
    setNewTagName('');
    setNewTagColor('#3B82F6');
    setNewTagDescription('');
  };

  const handleSubmitNewTag = async () => {
    if (!newTagName.trim()) {
      alert('태그 이름을 입력해주세요');
      return;
    }

    if (selectedTags.length >= maxTags) {
      alert(`최대 ${maxTags}개의 태그만 추가할 수 있습니다.`);
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await apiClient.post('/tags/', {
        name: newTagName.trim(),
        description: newTagDescription.trim() || undefined,
        color: newTagColor
      });

      const newTag = response.data;

      // Add to selected tags
      onTagsChange([...selectedTags, newTag]);

      // Update all tags list
      setAllTags([...allTags, newTag]);

      // Reset form
      setIsCreatingTag(false);
      setNewTagName('');
      setNewTagColor('#3B82F6');
      setNewTagDescription('');
      setSearchQuery('');
    } catch (err: any) {
      if (err.response?.data?.detail) {
        alert(`태그 생성 실패: ${err.response.data.detail}`);
      } else {
        alert('태그 생성에 실패했습니다');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-300">
        태그 ({selectedTags.length}/{maxTags})
      </label>

      {/* Selected tags */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedTags.map(tag => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium"
              style={{
                backgroundColor: tag.color + '20',
                color: tag.color,
                border: `1px solid ${tag.color}`
              }}
            >
              {tag.name}
              <button
                type="button"
                onClick={() => removeTag(tag.id)}
                className="hover:opacity-70"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search input */}
      <div className="relative" ref={dropdownRef}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={handleInputFocus}
          placeholder="태그 검색 또는 선택..."
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          disabled={selectedTags.length >= maxTags}
        />

        {/* Dropdown */}
        {isDropdownOpen && searchResults.length > 0 && selectedTags.length < maxTags && (
          <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-600 rounded-md shadow-lg max-h-60 overflow-y-auto">
            {searchResults
              .filter(tag => !selectedTags.find(t => t.id === tag.id))
              .map(tag => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => addTag(tag)}
                  className="w-full px-4 py-2 text-left hover:bg-gray-700 flex items-center gap-2"
                >
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: tag.color }}
                  />
                  <span className="text-white">{tag.name}</span>
                </button>
              ))}
          </div>
        )}

        {/* No results - show create new tag option */}
        {isDropdownOpen && searchQuery && searchResults.length === 0 && selectedTags.length < maxTags && (
          <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-600 rounded-md shadow-lg p-3">
            <p className="text-sm text-gray-400 mb-2">"{searchQuery}" 태그를 찾을 수 없습니다</p>
            <button
              type="button"
              onClick={handleCreateNewTag}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              새 태그 만들기
            </button>
          </div>
        )}
      </div>

      {/* Create New Tag Modal */}
      {isCreatingTag && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-600">
            <h3 className="text-xl font-bold text-white mb-4">새 태그 만들기</h3>

            <div className="space-y-4">
              {/* Tag Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  태그 이름 *
                </label>
                <input
                  type="text"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  placeholder="예: f-nine, bird, 댄스"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  autoFocus
                />
              </div>

              {/* Tag Color */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  색상
                </label>
                <div className="flex gap-2 items-center">
                  <input
                    type="color"
                    value={newTagColor}
                    onChange={(e) => setNewTagColor(e.target.value)}
                    className="w-12 h-10 bg-gray-700 border border-gray-600 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={newTagColor}
                    onChange={(e) => setNewTagColor(e.target.value)}
                    placeholder="#3B82F6"
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                {/* Preset colors */}
                <div className="flex gap-2 mt-2">
                  {['#FF6B6B', '#4ECDC4', '#95E1D3', '#F7DC6F', '#3B82F6', '#8B5CF6', '#EC4899', '#10B981'].map(color => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setNewTagColor(color)}
                      className="w-8 h-8 rounded-full border-2 border-gray-600 hover:border-white transition-colors"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
              </div>

              {/* Tag Description (Optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  설명 (선택사항)
                </label>
                <textarea
                  value={newTagDescription}
                  onChange={(e) => setNewTagDescription(e.target.value)}
                  placeholder="태그에 대한 설명..."
                  rows={2}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Preview */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  미리보기
                </label>
                <span
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                  style={{
                    backgroundColor: newTagColor + '20',
                    color: newTagColor,
                    border: `1px solid ${newTagColor}`
                  }}
                >
                  {newTagName || '태그 이름'}
                </span>
              </div>

              {/* Buttons */}
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleSubmitNewTag}
                  disabled={isSubmitting || !newTagName.trim()}
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? '생성 중...' : '생성'}
                </button>
                <button
                  type="button"
                  onClick={handleCancelCreate}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 disabled:opacity-50"
                >
                  취소
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
