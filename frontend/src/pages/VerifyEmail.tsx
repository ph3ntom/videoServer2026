import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import apiClient from '../services/api.client';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');

      if (!token) {
        setStatus('error');
        setMessage('인증 토큰이 없습니다');
        return;
      }

      try {
        const response = await apiClient.post('/auth/verify-email', null, {
          params: { token }
        });
        setStatus('success');
        setMessage(response.data.message || '이메일이 성공적으로 인증되었습니다');
      } catch (error: any) {
        setStatus('error');
        setMessage(
          error.response?.data?.detail || '이메일 인증에 실패했습니다'
        );
      }
    };

    verifyEmail();
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-white mb-6">
            이메일 인증
          </h2>

          {status === 'loading' && (
            <div className="bg-gray-800 rounded-lg p-8">
              <div className="flex justify-center mb-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
              </div>
              <p className="text-gray-300">이메일을 인증하는 중...</p>
            </div>
          )}

          {status === 'success' && (
            <div className="bg-green-500/10 border border-green-500 rounded-lg p-8">
              <div className="text-green-500 text-5xl mb-4">✓</div>
              <p className="text-green-500 text-lg mb-6">{message}</p>
              <Link
                to="/login"
                className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                로그인하기
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="bg-red-500/10 border border-red-500 rounded-lg p-8">
              <div className="text-red-500 text-5xl mb-4">✗</div>
              <p className="text-red-500 text-lg mb-6">{message}</p>
              <div className="space-x-4">
                <Link
                  to="/login"
                  className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  로그인
                </Link>
                <Link
                  to="/register"
                  className="inline-block px-6 py-3 bg-gray-700 text-white rounded-md hover:bg-gray-600"
                >
                  회원가입
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
