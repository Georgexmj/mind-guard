import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import EldersPage from './pages/EldersPage'
import ElderDetailPage from './pages/ElderDetailPage'
import AssessmentsPage from './pages/AssessmentsPage'
import AssessmentDetailPage from './pages/AssessmentDetailPage'
import InterventionsPage from './pages/InterventionsPage'
import QuestionsPage from './pages/QuestionsPage'
import NotificationsPage from './pages/NotificationsPage'
import ElderDashboardPage from './pages/ElderDashboardPage'
import Layout from './components/Layout'

// 页面加载时尝试修复可能损坏的 localStorage 数据
function fixLocalStorage() {
  try {
    // 检查并修复可能损坏的用户数据
    const userStr = localStorage.getItem('mindguard-user')
    if (userStr) {
      try {
        JSON.parse(userStr)
      } catch {
        // 如果解析失败，删除损坏的数据
        console.log('发现损坏的 mindguard-user，已删除')
        localStorage.removeItem('mindguard-user')
      }
    }
    
    // 检查 token 是否存在
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.log('access_token 不存在')
    }
  } catch (e) {
    console.error('修复 localStorage 失败:', e)
  }
}

// 在应用启动时运行修复
fixLocalStorage()

// 简单的认证检查 - 直接检查 localStorage
const isLoggedIn = () => {
  const token = localStorage.getItem('access_token')
  const user = localStorage.getItem('mindguard-user')
  return token !== null && token.length > 0 && user !== null && user.length > 0
}

// 获取用户角色
const getUserRole = (): string | null => {
  try {
    const userStr = localStorage.getItem('mindguard-user')
    if (userStr) {
      const user = JSON.parse(userStr)
      return user.role || null
    }
  } catch (e) {
    console.error('getUserRole() error:', e)
  }
  return null
}

// 根据角色获取默认路由
const getDefaultRouteByRole = (role?: string | null) => {
  switch (role) {
    case 'admin':
    case 'doctor':
      return '/dashboard'
    case 'elder':
    case 'family':
      return '/elder-home'
    default:
      return '/dashboard'
  }
}

// 简单的认证路由
function AuthRoute({ children }: { children: React.ReactNode }) {
  const loggedIn = isLoggedIn()
  
  if (loggedIn) {
    return <>{children}</>
  }
  return <Navigate to="/login" replace />
}

// 简单的角色路由
function RoleRoute({
  allowedRoles,
  children,
}: {
  allowedRoles: string[]
  children: React.ReactNode
}) {
  const role = getUserRole()
  const loggedIn = isLoggedIn()
  
  // 如果有 token 但角色不匹配，允许访问（避免被踢出去）
  if (loggedIn) {
    // 如果角色在允许列表中，直接访问
    if (role && allowedRoles.includes(role)) {
      return <>{children}</>
    }
    // 如果角色不在允许列表中，跳转到默认页面
    const redirectTo = getDefaultRouteByRole(role)
    return <Navigate to={redirectTo} replace />
  }
  
  return <Navigate to="/login" replace />
}

// 默认重定向
function DefaultRedirect() {
  const role = getUserRole()
  const redirectTo = getDefaultRouteByRole(role)
  return <Navigate to={redirectTo} replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        {/* 所有需要认证的路由 */}
        <Route
          path="/"
          element={
            <AuthRoute>
              <Layout />
            </AuthRoute>
          }
        >
          <Route index element={<DefaultRedirect />} />
          
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
            path="elder-home"
            element={
              <RoleRoute allowedRoles={['elder', 'family']}>
                <ElderDashboardPage />
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
        
        {/* 404 重定向 */}
        <Route path="*" element={<DefaultRedirect />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
