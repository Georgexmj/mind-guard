import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import EldersPage from './pages/EldersPage'
import ElderDetailPage from './pages/ElderDetailPage'
import AssessmentsPage from './pages/AssessmentsPage'
import AssessmentDetailPage from './pages/AssessmentDetailPage'
import InterventionsPage from './pages/InterventionsPage'
import QuestionsPage from './pages/QuestionsPage'
import Layout from './components/Layout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="elders" element={<EldersPage />} />
          <Route path="elders/:id" element={<ElderDetailPage />} />
          <Route path="assessments" element={<AssessmentsPage />} />
          <Route path="assessments/:sessionId" element={<AssessmentDetailPage />} />
          <Route path="interventions" element={<InterventionsPage />} />
          <Route path="questions" element={<QuestionsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
