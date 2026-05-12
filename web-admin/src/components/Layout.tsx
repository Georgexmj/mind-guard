import { useMemo } from 'react'
import type { ReactNode } from 'react'
import { Layout as AntLayout, Menu, Avatar, Dropdown, Space, Typography } from 'antd'
import type { MenuProps } from 'antd'
import {
  DashboardOutlined,
  UserOutlined,
  FileTextOutlined,
  LogoutOutlined,
  MedicineBoxOutlined,
  BookOutlined,
  BellOutlined,
  TeamOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import type { User } from '../types'
import '../styles/layout.css'

const { Header, Content } = AntLayout
const { Text } = Typography

type UserRole = User['role']

type AppMenuItem = {
  key: string
  icon: ReactNode
  label: string
  roles: UserRole[]
}

const menuItems: AppMenuItem[] = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '数据总览', roles: ['admin', 'doctor'] },
  { key: '/elders', icon: <TeamOutlined />, label: '老人管理', roles: ['admin', 'doctor'] },
  { key: '/assessments', icon: <FileTextOutlined />, label: '评估管理', roles: ['admin', 'doctor'] },
  { key: '/interventions', icon: <LineChartOutlined />, label: '训练管理', roles: ['admin', 'doctor'] },
  { key: '/questions', icon: <BookOutlined />, label: '题库管理', roles: ['admin', 'doctor'] },
  { key: '/notifications', icon: <BellOutlined />, label: '预警中心', roles: ['admin', 'doctor'] },
  { key: '/elder-home', icon: <UserOutlined />, label: '老人端首页', roles: ['elder', 'family'] },
]

const roleLabelMap: Record<UserRole, string> = {
  admin: '系统管理员',
  doctor: '社区医生',
  elder: '老人用户',
  family: '家属用户',
}

// 直接从 localStorage 获取用户信息
const getUserFromStorage = (): User | null => {
  try {
    const stored = localStorage.getItem('mindguard-user')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

// 直接清除认证信息
const logoutFromStorage = (): void => {
  localStorage.removeItem('mindguard-user')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  
  // 直接从 localStorage 获取用户信息
  const user = getUserFromStorage()
  const role = user?.role

  const visibleMenuItems = useMemo(
    () => (role ? menuItems.filter((item) => item.roles.includes(role)) : []),
    [role]
  )

  const selectedKey = useMemo(
    () =>
      visibleMenuItems.find((item) => location.pathname.startsWith(item.key))?.key ??
      visibleMenuItems[0]?.key,
    [location.pathname, visibleMenuItems]
  )

  const userMenu: MenuProps = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        danger: true,
      },
    ],
    onClick: ({ key }) => {
      if (key === 'logout') {
        logoutFromStorage()
        navigate('/login')
      }
    },
  }

  return (
    <AntLayout className="mg-shell">
      <Header className="mg-header">
        <div className="mg-brand" onClick={() => navigate(selectedKey || '/dashboard')}>
          <span className="mg-brand-icon">智</span>
          <div className="mg-brand-copy">
            <Text className="mg-brand-title">MindGuard Admin</Text>
            <Text className="mg-brand-subtitle">认知守护 · 社区筛查管理平台</Text>
          </div>
        </div>

        <Menu
          className="mg-top-menu"
          mode="horizontal"
          selectedKeys={selectedKey ? [selectedKey] : []}
          items={visibleMenuItems}
          onClick={({ key }) => navigate(key)}
        />

        <div className="mg-header-right">
          <Space className="mg-role-pill">
            <UserOutlined />
            <Text>{user?.role ? roleLabelMap[user.role] : '未登录'}</Text>
          </Space>
          <Dropdown menu={userMenu} placement="bottomRight" trigger={['click']}>
            <Avatar className="mg-user-avatar" icon={<MedicineBoxOutlined />} />
          </Dropdown>
        </div>
      </Header>

      <Content className="mg-content">
        <Outlet />
      </Content>
    </AntLayout>
  )
}
