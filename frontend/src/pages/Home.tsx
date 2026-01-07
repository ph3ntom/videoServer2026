import { useEffect, useState } from 'react';
import Layout from '../components/common/Layout';
import { useAuthStore } from '../store/authStore';
import apiClient from '../services/api.client';

export default function Home() {
  const { user, loadUser } = useAuthStore();
  const [resendingEmail, setResendingEmail] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const handleResendVerification = async () => {
    setResendingEmail(true);
    setResendMessage('');

    try {
      await apiClient.post('/auth/resend-verification');
      setResendMessage('인증 이메일이 전송되었습니다. 이메일을 확인해주세요.');
    } catch (error: any) {
      setResendMessage(
        error.response?.data?.detail || '이메일 전송에 실패했습니다'
      );
    } finally {
      setResendingEmail(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-4">
            StreamFlix에 오신 것을 환영합니다
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            라즈베리파이 기반 경량 스트리밍 플랫폼
          </p>

          {user && (
            <>
              {/* Email verification notice */}
              {!user.is_verified && (
                <div className="bg-yellow-500/10 border border-yellow-500 rounded-lg p-4 mb-6 max-w-md mx-auto">
                  <p className="text-yellow-500 mb-3">
                    ⚠️ 이메일 인증이 필요합니다
                  </p>
                  <p className="text-sm text-gray-300 mb-4">
                    회원가입 시 전송된 인증 이메일을 확인해주세요.
                  </p>
                  <button
                    onClick={handleResendVerification}
                    disabled={resendingEmail}
                    className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {resendingEmail ? '전송 중...' : '인증 이메일 재전송'}
                  </button>
                  {resendMessage && (
                    <p className="mt-3 text-sm text-gray-300">{resendMessage}</p>
                  )}
                </div>
              )}

              <div className="bg-gray-800 rounded-lg p-6 max-w-md mx-auto">
                <h2 className="text-2xl font-semibold text-white mb-4">
                  사용자 정보
                </h2>
                <div className="space-y-2 text-left">
                  <div className="flex justify-between">
                    <span className="text-gray-400">이메일:</span>
                    <span className="text-white">{user.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">사용자명:</span>
                    <span className="text-white">{user.username}</span>
                  </div>
                  {user.full_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">이름:</span>
                      <span className="text-white">{user.full_name}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-400">역할:</span>
                    <span className="text-white capitalize">{user.role}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">계정 상태:</span>
                    <span className="text-white">
                      {user.is_active ? '활성' : '비활성'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">이메일 인증:</span>
                    <span className={user.is_verified ? 'text-green-500' : 'text-yellow-500'}>
                      {user.is_verified ? '✓ 완료' : '✗ 미완료'}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}

          <div className="mt-12">
            <p className="text-gray-500">
              비디오 업로드 및 스트리밍 기능은 곧 추가될 예정입니다.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
