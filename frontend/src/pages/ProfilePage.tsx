import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/common/Layout';
import VideoCard from '../components/video/VideoCard';
import apiClient from '../services/api.client';
import { useAuthStore } from '../store/authStore';
import { useToastStore } from '../store/toastStore';

interface UserProfile {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

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

export default function ProfilePage() {
  const { user } = useAuthStore();
  const toast = useToastStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [myVideos, setMyVideos] = useState<Video[]>([]);
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProfile();
    if (user?.role === 'admin') {
      loadMyVideos();
    }
  }, [user]);

  const loadProfile = async () => {
    try {
      const response = await apiClient.get('/auth/me');
      setProfile(response.data);
      setFullName(response.data.full_name || '');
    } catch (err: any) {
      toast.error('프로필을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadMyVideos = async () => {
    try {
      const response = await apiClient.get('/videos/my-videos');
      setMyVideos(response.data);
    } catch (err: any) {
      console.error('Failed to load my videos:', err);
    }
  };

  const handleSaveProfile = async () => {
    if (!profile) return;

    setSaving(true);

    try {
      await apiClient.put(`/users/${profile.id}`, {
        full_name: fullName || null
      });

      setProfile({ ...profile, full_name: fullName || null });
      toast.success('프로필이 업데이트되었습니다');
      setEditing(false);
    } catch (err: any) {
      toast.error('프로필 업데이트에 실패했습니다');
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setFullName(profile?.full_name || '');
    setEditing(false);
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      </Layout>
    );
  }

  if (!profile) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center text-red-500">프로필을 불러올 수 없습니다</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-white mb-8">프로필</h1>

        {/* Profile Card */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">내 정보</h2>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                수정
              </button>
            )}
          </div>

          <div className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                사용자명
              </label>
              <div className="text-white bg-gray-700 px-4 py-2 rounded">
                {profile.username}
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                이메일
              </label>
              <div className="text-white bg-gray-700 px-4 py-2 rounded">
                {profile.email}
              </div>
            </div>

            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                이름
              </label>
              {editing ? (
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="이름을 입력하세요"
                  className="w-full px-4 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              ) : (
                <div className="text-white bg-gray-700 px-4 py-2 rounded">
                  {profile.full_name || '(미설정)'}
                </div>
              )}
            </div>

            {/* Role */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                역할
              </label>
              <div className="text-white bg-gray-700 px-4 py-2 rounded flex items-center">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  profile.role === 'admin' ? 'bg-red-600' : 'bg-gray-600'
                }`}>
                  {profile.role.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Created At */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                가입일
              </label>
              <div className="text-white bg-gray-700 px-4 py-2 rounded">
                {new Date(profile.created_at).toLocaleDateString('ko-KR')}
              </div>
            </div>
          </div>

          {editing && (
            <div className="mt-6 flex gap-3">
              <button
                onClick={handleSaveProfile}
                disabled={saving}
                className={`px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 ${
                  saving ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {saving ? '저장 중...' : '저장'}
              </button>
              <button
                onClick={handleCancelEdit}
                disabled={saving}
                className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500"
              >
                취소
              </button>
            </div>
          )}
        </div>

        {/* My Videos (Admin Only) */}
        {user?.role === 'admin' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">내가 업로드한 비디오</h2>
              <Link
                to="/upload"
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                + 새 비디오 업로드
              </Link>
            </div>

            {myVideos.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 mb-4">아직 업로드한 비디오가 없습니다</p>
                <Link
                  to="/upload"
                  className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  첫 비디오 업로드하기
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {myVideos.map((video) => (
                  <VideoCard key={video.id} video={video} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
