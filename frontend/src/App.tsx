import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import Home from './pages/Home'
import VerifyEmail from './pages/VerifyEmail'
import Videos from './pages/Videos'
import VideoPlayer from './pages/VideoPlayer'
import UploadVideo from './pages/UploadVideo'
import SearchPage from './pages/SearchPage'
import ProfilePage from './pages/ProfilePage'
import PopularVideos from './pages/PopularVideos'
import TopRatedVideos from './pages/TopRatedVideos'
import AllVideos from './pages/AllVideos'
import PrivateRoute from './components/common/PrivateRoute'
import ErrorBoundary from './components/common/ErrorBoundary'
import { useAuthStore } from './store/authStore'

function App() {
  const loadUser = useAuthStore((state) => state.loadUser)

  // Load user on app mount (page refresh)
  useEffect(() => {
    loadUser()
  }, [loadUser])

  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />

          {/* Protected routes */}
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
      </Router>
    </ErrorBoundary>
  )
}

export default App
