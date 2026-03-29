import { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  message,
  Alert,
  Divider,
  Space,
} from 'antd'
import { UserOutlined, LockOutlined, MedicineBoxOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'
import { useAuthStore } from '../store/auth'

const { Title, Text, Paragraph } = Typography

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
      messageApi.success('登录成功，欢迎回来！')
      setTimeout(() => navigate('/dashboard'), 500)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      messageApi.error(
        error?.response?.data?.detail || '登录失败，请检查手机号和密码'
      )
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = () => {
    form.setFieldsValue({ phone: '13800138000', password: 'admin123456' })
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 40%, #1677ff 100%)',
        padding: 24,
      }}
    >
      {contextHolder}

      {/* Background decoration */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage:
            'radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08) 0%, transparent 50%)',
        }}
      />

      <Card
        style={{
          width: '100%',
          maxWidth: 440,
          borderRadius: 16,
          boxShadow: '0 24px 64px rgba(0,0,0,0.25)',
          border: 'none',
          position: 'relative',
        }}
        bodyStyle={{ padding: '40px 48px' }}
      >
        {/* Logo & Title */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div
            style={{
              width: 72,
              height: 72,
              background: 'linear-gradient(135deg, #1677ff, #764ba2)',
              borderRadius: 20,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 16,
              boxShadow: '0 8px 24px rgba(22,119,255,0.3)',
            }}
          >
            <MedicineBoxOutlined style={{ fontSize: 36, color: '#fff' }} />
          </div>
          <Title level={2} style={{ margin: 0, color: '#1a1a2e', fontWeight: 700 }}>
            CogniCare
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            认知障碍筛查系统 · 管理平台
          </Text>
        </div>

        {/* Login Form */}
        <Form
          form={form}
          layout="vertical"
          onFinish={handleLogin}
          requiredMark={false}
          size="large"
        >
          <Form.Item
            name="phone"
            label={<Text strong>手机号码</Text>}
            rules={[
              { required: true, message: '请输入手机号码' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#bbb' }} />}
              placeholder="请输入手机号码"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            label={<Text strong>登录密码</Text>}
            rules={[{ required: true, message: '请输入登录密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bbb' }} />}
              placeholder="请输入登录密码"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          <Form.Item style={{ marginTop: 8, marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: 48,
                borderRadius: 8,
                fontSize: 16,
                fontWeight: 600,
                background: 'linear-gradient(135deg, #1677ff, #764ba2)',
                border: 'none',
                boxShadow: '0 4px 16px rgba(22,119,255,0.3)',
              }}
            >
              {loading ? '登录中...' : '登 录'}
            </Button>
          </Form.Item>
        </Form>

        <Divider style={{ color: '#bbb', fontSize: 12 }}>演示账号</Divider>

        <Alert
          type="info"
          showIcon={false}
          style={{ borderRadius: 8, background: '#f0f7ff', border: '1px solid #bae0ff' }}
          message={
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Paragraph style={{ margin: 0, fontSize: 13 }}>
                <Text type="secondary">手机号：</Text>
                <Text strong copyable>13800138000</Text>
              </Paragraph>
              <Paragraph style={{ margin: 0, fontSize: 13 }}>
                <Text type="secondary">密　码：</Text>
                <Text strong copyable>admin123456</Text>
              </Paragraph>
              <Button
                size="small"
                type="link"
                onClick={fillDemo}
                style={{ padding: 0, height: 'auto', fontSize: 12 }}
              >
                点击一键填入
              </Button>
            </Space>
          }
        />
      </Card>
    </div>
  )
}
