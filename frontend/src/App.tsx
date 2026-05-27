import { Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider, useAuth } from './AuthContext'
import { Layout } from './components/Layout'
import { JobDetailPage } from './pages/JobDetailPage'
import { JobsPage } from './pages/JobsPage'
import { LoginPage } from './pages/LoginPage'
import { UploadPage } from './pages/UploadPage'

function PrivateRoutes() {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/jobs" replace />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/jobs/:jobId" element={<JobDetailPage />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<PrivateRoutes />} />
      </Routes>
    </AuthProvider>
  )
}
