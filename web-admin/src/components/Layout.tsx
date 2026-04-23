import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Layout as AntLayout, Menu, Button, Avatar, Dropdown, Space, Typography } from 'antd'
import type { MenuProps } from 'antd'
import {
  DashboardOutlined,
  UserOutlined,
  FileTextOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MedicineBoxOutlined,
  HeartOutlined,
  BookOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import type { User } from '../types'
import '../styles/layout.css'

const { Sider, Header, Content } = AntLayout
const { Text } = Typography

type UserRole = User['role']

type AppMenuItem = {
  key: string
  icon: ReactNode
  label: string
  roles: UserRole[]
}

const menuItems: AppMenuItem[] = [
  { key: '/elder-home', icon: <DashboardOutlined />, label: '我的看板', roles: ['elder', 'family'] },
  { key: '/dashboard', icon: <DashboardOutlined />, label: '运营看板', roles: ['admin', 'doctor'] },
  { key: '/elders', icon: <UserOutlined />, label: '老人管理', roles: ['admin', 'doctor'] },
  { key: '/assessments', icon: <FileTextOutlined />, label: '评估管理', roles: ['admin', 'doctor', 'elder', 'family'] },
  { key: '/interventions', icon: <HeartOutlined />, label: '干预管理', roles: ['admin', 'doctor', 'elder', 'family'] },
  { key: '/questions', icon: <BookOutlined />, label: '题库管理', roles: ['admin', 'doctor'] },
  { key: '/notifications', icon: <BellOutlined />, label: '通知中心', roles: ['admin', 'doctor', 'elder', 'family'] },
]

const pageTitleMap: Record<string, string> = {
  '/elder-home': '我的看板',
  '/dashboard': '运营看板',
  '/elders': '老人管理',
  '/assessments': '评估管理',
  '/interventions': '干预管理',
  '/questions': '题库管理',
  '/notifications': '通知中心',
}

const roleLabelMap: Record<UserRole, string> = {
  admin: '系统管理员',
  doctor: '医生',
  elder: '老人用户',
  family: '家属用户',
}

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
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

  const currentTitle = pageTitleMap[selectedKey ?? ''] ?? '管理工作台'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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
      if (key === 'logout') handleLogout()
    },
  }

  return (
    <AntLayout className="mg-shell">
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={248}
        className="mg-sider"
      >
        <div className="mg-logo" onClick={() => navigate('/dashboard')}>
          <div className="mg-logo-icon">
            <MedicineBoxOutlined />
          </div>
          {!collapsed && (
            <div className="mg-logo-text">
              <Text className="mg-logo-title">MindGuard</Text>
              <Text className="mg-logo-subtitle">认知早筛管理台</Text>
            </div>
          )}
        </div>

        <Menu
          className="mg-menu"
          mode="inline"
          selectedKeys={selectedKey ? [selectedKey] : []}
          items={visibleMenuItems}
          onClick={({ key }) => navigate(key)}
        />

        {!collapsed && (
          <div className="mg-sider-footer">
            <Text className="mg-sider-footer-title">今日提醒</Text>
            <Text className="mg-sider-footer-desc">重点关注高风险老人复评与干预跟踪闭环。</Text>
          </div>
        )}
      </Sider>

      <AntLayout className="mg-main">
        <Header className="mg-header">
          <div className="mg-header-left">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed((prev) => !prev)}
              className="mg-collapse-btn"
            />
            <div>
              <Text className="mg-header-title">{currentTitle}</Text>
              <Text className="mg-header-subtitle">社区老年认知障碍早期筛查与干预系统</Text>
            </div>
          </div>

          <Dropdown menu={userMenu} placement="bottomRight" trigger={['click']}>
            <Space className="mg-user-chip">
              <Avatar className="mg-user-avatar" icon={<UserOutlined />} />
              <div className="mg-user-meta">
                <Text className="mg-user-name">{user?.name || '未登录用户'}</Text>
                <Text className="mg-user-role">{user?.role ? roleLabelMap[user.role] : ''}</Text>
              </div>
            </Space>
          </Dropdown>
        </Header>

        <Content className="mg-content">
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
