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
import NotificationsPage from './pages/NotificationsPage'
import Layout from './components/Layout'
import type { User } from './types'

type UserRole = User['role']

const getDefaultRouteByRole = (role?: UserRole) => {
  switch (role) {
    case 'admin':
    case 'doctor':
      return '/dashboard'
    case 'elder':
    case 'family':
      return '/assessments'
    default:
      return '/login'
  }
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function RoleRoute({
  allowedRoles,
  children,
}: {
  allowedRoles: UserRole[]
  children: React.ReactNode
}) {
  const user = useAuthStore((state) => state.user)
  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={getDefaultRouteByRole(user.role)} replace />
  }
  return <>{children}</>
}

function DefaultIndexRedirect() {
  const user = useAuthStore((state) => state.user)
  return <Navigate to={getDefaultRouteByRole(user?.role)} replace />
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
          <Route index element={<DefaultIndexRedirect />} />
          <Route
            path="dashboard"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor']}>
                <DashboardPage />
              </RoleRoute>
            }
          />
          <Route
            path="elders"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor']}>
                <EldersPage />
              </RoleRoute>
            }
          />
          <Route
            path="elders/:id"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor']}>
                <ElderDetailPage />
              </RoleRoute>
            }
          />
          <Route
            path="assessments"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor', 'elder', 'family']}>
                <AssessmentsPage />
              </RoleRoute>
            }
          />
          <Route
            path="assessments/:sessionId"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor', 'elder', 'family']}>
                <AssessmentDetailPage />
              </RoleRoute>
            }
          />
          <Route
            path="interventions"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor', 'elder', 'family']}>
                <InterventionsPage />
              </RoleRoute>
            }
          />
          <Route
            path="questions"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor']}>
                <QuestionsPage />
              </RoleRoute>
            }
          />
          <Route
            path="notifications"
            element={
              <RoleRoute allowedRoles={['admin', 'doctor', 'elder', 'family']}>
                <NotificationsPage />
              </RoleRoute>
            }
          />
        </Route>
        <Route path="*" element={<DefaultIndexRedirect />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
