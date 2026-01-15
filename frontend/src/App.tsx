import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import VerifyEmail from './pages/VerifyEmail'
import PrivateRoute from './components/common/PrivateRoute'
import ErrorBoundary from './components/common/ErrorBoundary'
import { useAuthStore } from './store/authStore'

// Lazy load protected pages for better initial load performance
const Home = lazy(() => import('./pages/Home'))
const Videos = lazy(() => import('./pages/Videos'))
const VideoPlayer = lazy(() => import('./pages/VideoPlayer'))
const UploadVideo = lazy(() => import('./pages/UploadVideo'))
const SearchPage = lazy(() => import('./pages/SearchPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const PopularVideos = lazy(() => import('./pages/PopularVideos'))
const TopRatedVideos = lazy(() => import('./pages/TopRatedVideos'))
const AllVideos = lazy(() => import('./pages/AllVideos'))

// Loading component for Suspense fallback
const PageLoader = () => (
  <div className="min-h-screen bg-gray-900 flex items-center justify-center">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
  </div>
)

function App() {
  const loadUser = useAuthStore((state) => state.loadUser)

  // Load user on app mount (page refresh)
  useEffect(() => {
    loadUser()
  }, [loadUser])

  return (
    <ErrorBoundary>
      <Router>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify-email" element={<VerifyEmail />} />

            {/* Protected routes - lazy loaded */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              }
            />
          <Route
            path="/videos"
            element={
              <PrivateRoute>
                <Videos />
              </PrivateRoute>
            }
          />
          <Route
            path="/videos/popular"
            element={
              <PrivateRoute>
                <PopularVideos />
              </PrivateRoute>
            }
          />
          <Route
            path="/videos/top-rated"
            element={
              <PrivateRoute>
                <TopRatedVideos />
              </PrivateRoute>
            }
          />
          <Route
            path="/videos/all"
            element={
              <PrivateRoute>
                <AllVideos />
              </PrivateRoute>
            }
          />
          <Route
            path="/videos/:id"
            element={
              <PrivateRoute>
                <VideoPlayer />
              </PrivateRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <PrivateRoute>
                <UploadVideo />
              </PrivateRoute>
            }
          />
          <Route
            path="/search"
            element={
              <PrivateRoute>
                <SearchPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <ProfilePage />
              </PrivateRoute>
            }
          />

            {/* Catch all - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Router>
    </ErrorBoundary>
  )
}

export default App
