import { useState, FormEvent, ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/common/Layout';
import apiClient from '../services/api.client';

export default function UploadVideo() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];

      // Check file type
      const validTypes = ['video/mp4', 'video/x-matroska', 'video/avi', 'video/quicktime', 'video/webm'];
      if (!validTypes.includes(selectedFile.type)) {
        setError('지원하지 않는 파일 형식입니다. MP4, MKV, AVI, MOV, WEBM 파일만 업로드 가능합니다.');
        return;
      }

      // Check file size (5GB max)
      const maxSize = 5 * 1024 * 1024 * 1024; // 5GB
      if (selectedFile.size > maxSize) {
        setError('파일 크기가 너무 큽니다. 최대 5GB까지 업로드 가능합니다.');
        return;
      }

      setFile(selectedFile);
      setError('');
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!file) {
      setError('비디오 파일을 선택해주세요');
      return;
    }

    if (!title.trim()) {
      setError('제목을 입력해주세요');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      if (description) {
        formData.append('description', description);
      }

      const response = await apiClient.post('/videos/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        },
      });

      // Redirect to video detail page with thumbnail selection prompt
      const videoId = response.data.id;
      navigate(`/videos/${videoId}?selectThumbnail=true`);
    } catch (err: any) {
      setError(err.response?.data?.detail || '비디오 업로드에 실패했습니다');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-white mb-8">비디오 업로드</h1>

        <form onSubmit={handleSubmit} className="space-y-6 bg-gray-800 rounded-lg p-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-2">
              제목 *
            </label>
            <input
              id="title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={uploading}
              className="w-full px-3 py-2 border border-gray-700 bg-gray-900 text-white rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
              placeholder="비디오 제목을 입력하세요"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-2">
              설명 (선택)
            </label>
            <textarea
              id="description"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={uploading}
              className="w-full px-3 py-2 border border-gray-700 bg-gray-900 text-white rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
              placeholder="비디오에 대한 설명을 입력하세요"
            />
          </div>

          {/* File Upload */}
          <div>
            <label htmlFor="file" className="block text-sm font-medium text-gray-300 mb-2">
              비디오 파일 *
            </label>
            <input
              id="file"
              type="file"
              accept="video/mp4,video/x-matroska,video/avi,video/quicktime,video/webm"
              onChange={handleFileChange}
              disabled={uploading}
              className="w-full px-3 py-2 border border-gray-700 bg-gray-900 text-white rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700"
            />
            {file && (
              <p className="mt-2 text-sm text-gray-400">
                선택된 파일: {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
              </p>
            )}
            <p className="mt-2 text-xs text-gray-500">
              지원 형식: MP4, MKV, AVI, MOV, WEBM (최대 5GB)
            </p>
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div>
              <div className="flex justify-between text-sm text-gray-300 mb-2">
                <span>업로드 중...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={uploading || !file}
              className="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? '업로드 중...' : '업로드'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/videos')}
              disabled={uploading}
              className="px-4 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
            >
              취소
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
