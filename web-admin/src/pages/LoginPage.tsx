import { useState } from 'react'
import { Card, Form, Input, Button, Typography, message, Alert, Space } from 'antd'
import { UserOutlined, LockOutlined, MedicineBoxOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'
import { useAuthStore } from '../store/auth'
import type { User } from '../types'
import loginIllustration from '../assets/login-health-illustration.svg'
import '../styles/login.css'

const { Title, Text } = Typography

type UserRole = User['role']

const getDefaultRouteByRole = (role?: UserRole) => {
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

interface LoginForm {
  phone: string
  password: string
}

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm<LoginForm>()
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [messageApi, contextHolder] = message.useMessage()

  const handleLogin = async (values: LoginForm) => {
    setLoading(true)
    try {
      const response = await login(values.phone, values.password)
      setAuth(response.user, response.access_token)
      messageApi.success('登录成功，欢迎回来。')
      setTimeout(() => navigate(getDefaultRouteByRole(response.user?.role)), 350)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      messageApi.error(error?.response?.data?.detail || '登录失败，请检查手机号和密码。')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = () => {
    form.setFieldsValue({ phone: '13800000001', password: 'admin123' })
  }

  return (
    <div className="mg-login-page">
      {contextHolder}
      <div className="mg-login-bg-orb mg-login-bg-orb-a" />
      <div className="mg-login-bg-orb mg-login-bg-orb-b" />
      <div className="mg-login-bg-grid" />

      <Card className="mg-login-card" bodyStyle={{ padding: 0 }}>
        <div className="mg-login-left">
          <div className="mg-login-brand">
            <div className="mg-login-brand-icon">
              <MedicineBoxOutlined />
            </div>
            <Title level={2} className="mg-login-brand-title">
              MindGuard 管理台
            </Title>
            <Text className="mg-login-brand-subtitle">社区老年认知障碍早筛与干预系统</Text>
          </div>

          <div className="mg-login-form-wrap">
            <Form form={form} layout="vertical" onFinish={handleLogin} requiredMark={false} size="large">
              <Form.Item
                name="phone"
                label="手机号"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' },
                ]}
              >
                <Input prefix={<UserOutlined />} placeholder="请输入手机号" autoComplete="username" />
              </Form.Item>

              <Form.Item name="password" label="登录密码" rules={[{ required: true, message: '请输入登录密码' }]}>
                <Input.Password prefix={<LockOutlined />} placeholder="请输入登录密码" autoComplete="current-password" />
              </Form.Item>

              <Form.Item style={{ marginBottom: 12 }}>
                <Button type="primary" htmlType="submit" loading={loading} block className="mg-login-submit">
                  {loading ? '登录中...' : '登录'}
                </Button>
              </Form.Item>
            </Form>

            <Alert
              className="mg-login-demo"
              showIcon={false}
              message={
                <Space direction="vertical" size={6}>
                  <Text className="mg-login-demo-title">演示账号</Text>
                  <Text>手机号：13800000001</Text>
                  <Text>密码：admin123</Text>
                  <Button type="link" onClick={fillDemo} className="mg-login-fill-btn">
                    一键填充
                  </Button>
                </Space>
              }
            />
          </div>
        </div>

        <div className="mg-login-visual" aria-hidden="true">
          <div className="mg-login-visual-glow" />
          <img className="mg-login-visual-illustration" src={loginIllustration} alt="认知筛查与守护插画" />
          <div className="mg-login-visual-chip mg-login-visual-chip-1">认知评估</div>
          <div className="mg-login-visual-chip mg-login-visual-chip-2">风险预警</div>
          <div className="mg-login-visual-chip mg-login-visual-chip-3">干预建议</div>
          <div className="mg-login-visual-card">
            <Text className="mg-login-visual-title">智慧筛查 · 实时守护</Text>
            <Text className="mg-login-visual-desc">多模态认知评估、风险预警、干预建议一体化工作台</Text>
          </div>
        </div>
      </Card>
    </div>
  )
}
