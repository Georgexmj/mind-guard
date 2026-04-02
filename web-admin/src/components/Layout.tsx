import { useState } from 'react'
import { Layout as AntLayout, Menu, Button, Avatar, Dropdown, Space, Typography } from 'antd'
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

const { Sider, Header, Content } = AntLayout
const { Text } = Typography

type UserRole = User['role']

type MenuItem = {
  key: string
  icon: React.ReactNode
  label: string
  roles: UserRole[]
}

const menuItems: MenuItem[] = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表盘',
    roles: ['admin', 'doctor'],
  },
  {
    key: '/elders',
    icon: <UserOutlined />,
    label: '老人管理',
    roles: ['admin', 'doctor'],
  },
  {
    key: '/assessments',
    icon: <FileTextOutlined />,
    label: '评估管理',
    roles: ['admin', 'doctor', 'elder', 'family'],
  },
  {
    key: '/interventions',
    icon: <HeartOutlined />,
    label: '干预管理',
    roles: ['admin', 'doctor', 'elder', 'family'],
  },
  {
    key: '/questions',
    icon: <BookOutlined />,
    label: '题库管理',
    roles: ['admin', 'doctor'],
  },
  {
    key: '/notifications',
    icon: <BellOutlined />,
    label: '通知中心',
    roles: ['admin', 'doctor', 'elder', 'family'],
  },
]

const roleLabelMap: Record<UserRole, string> = {
  admin: '管理员',
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

  const visibleMenuItems = role
    ? menuItems.filter((item) => item.roles.includes(role))
    : []

  const selectedKey =
    visibleMenuItems.find((item) => location.pathname.startsWith(item.key))?.key || visibleMenuItems[0]?.key

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={220}
        style={{
          background: 'linear-gradient(180deg, #001529 0%, #002140 100%)',
          boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? '0' : '0 20px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <MedicineBoxOutlined style={{ color: '#1677ff', fontSize: 24, flexShrink: 0 }} />
          {!collapsed && (
            <Text
              style={{
                color: '#fff',
                fontSize: 16,
                fontWeight: 700,
                marginLeft: 10,
                whiteSpace: 'nowrap',
                letterSpacing: 1,
              }}
            >
              MindGuard
            </Text>
          )}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKey ? [selectedKey] : []}
          items={visibleMenuItems}
          onClick={handleMenuClick}
          style={{
            background: 'transparent',
            borderRight: 'none',
            marginTop: 8,
          }}
        />
      </Sider>

      <AntLayout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,0.08)',
            position: 'sticky',
            top: 0,
            zIndex: 100,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 40, height: 40 }}
          />

          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar
                style={{ backgroundColor: '#1677ff' }}
                icon={<UserOutlined />}
              />
              <Text style={{ fontWeight: 500 }}>
                {user?.name || '未登录'}{user?.role ? `（${roleLabelMap[user.role]}）` : ''}
              </Text>
            </Space>
          </Dropdown>
        </Header>

        <Content
          style={{
            margin: 24,
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
