import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import SearchBar from '../search/SearchBar';
import Toast from './Toast';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <Toast />
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16 gap-4">
            {/* Logo */}
            <Link to="/" className="flex items-center flex-shrink-0">
              <span className="text-2xl font-bold text-white">StreamFlix</span>
            </Link>

            {/* Search Bar */}
            {user && <SearchBar className="flex-1 max-w-2xl" />}

            {/* Navigation */}
            <nav className="flex items-center space-x-4 flex-shrink-0">
              {user && (
                <>
                  <Link
                    to="/videos"
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    비디오
                  </Link>
                  <Link
                    to="/upload"
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    업로드
                  </Link>
                  <Link
                    to="/profile"
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    프로필
                  </Link>
                  <div className="flex items-center space-x-4 text-gray-300">
                    <span className="text-sm">
                      {user.full_name || user.username}
                    </span>
                    <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                      {user.role}
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                  >
                    로그아웃
                  </button>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">{children}</main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
