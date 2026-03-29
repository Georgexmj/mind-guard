import { useEffect, useState } from 'react'
import {
  Card,
  Descriptions,
  Table,
  Button,
  Typography,
  Space,
  Tag,
  Row,
  Col,
  Spin,
  Alert,
  Avatar,
  Divider,
  Progress,
} from 'antd'
import {
  UserOutlined,
  ArrowLeftOutlined,
  FileTextOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { getElderById, getSessions, getSessionResult } from '../services/api'
import type { User, AssessmentSession, AssessmentResult } from '../types'
import RiskBadge from '../components/RiskBadge'
import CognitiveRadar from '../components/CognitiveRadar'

const { Title, Text, Paragraph } = Typography

// Mock data for demo
const MOCK_ELDER: User = {
  id: 1,
  uuid: 'u1',
  name: '王秀兰',
  phone: '138****0001',
  role: 'elder',
  community_id: 1,
  created_at: '2024-01-10',
  birth_date: '1948-03-15',
  gender: 'female',
  education_years: 6,
}

const MOCK_SESSIONS: AssessmentSession[] = [
  { id: 1, user_id: 1, status: 'completed', started_at: '2024-03-20T09:00:00', completed_at: '2024-03-20T09:18:00', created_at: '2024-03-20T09:00:00' },
  { id: 5, user_id: 1, status: 'completed', started_at: '2024-02-15T14:30:00', completed_at: '2024-02-15T14:45:00', created_at: '2024-02-15T14:30:00' },
  { id: 9, user_id: 1, status: 'completed', started_at: '2024-01-20T10:00:00', completed_at: '2024-01-20T10:20:00', created_at: '2024-01-20T10:00:00' },
]

const MOCK_RESULT: AssessmentResult = {
  id: 1,
  session_id: 1,
  risk_level: 'normal',
  nc_probability: 0.78,
  mci_probability: 0.17,
  ad_probability: 0.05,
  mmse_score: 27,
  domain_scores: {
    memory: 7.8,
    orientation: 8.5,
    language: 8.0,
    attention: 7.2,
    visuospatial: 7.5,
    executive: 7.9,
  },
  recommendation: '受试者认知功能评估结果在正常范围内，建议保持良好的生活习惯，定期进行认知训练活动，如阅读、下棋、社交等。建议6个月后进行复查。',
  created_at: '2024-03-20T09:18:00',
}

const statusConfig: Record<string, { text: string; color: string }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '待开始', color: 'default' },
  failed: { text: '已失败', color: 'error' },
}

const educationLabel = (years?: number): string => {
  if (years == null) return '-'
  if (years <= 6) return '小学'
  if (years <= 9) return '初中'
  if (years <= 12) return '高中'
  if (years <= 15) return '大专'
  return '本科及以上'
}

const genderMap: Record<string, string> = { male: '男', female: '女' }

export default function ElderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [elder, setElder] = useState<User | null>(null)
  const [sessions, setSessions] = useState<AssessmentSession[]>([])
  const [latestResult, setLatestResult] = useState<AssessmentResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return
      setLoading(true)
      try {
        const [elderData, sessionsData] = await Promise.allSettled([
          getElderById(Number(id)),
          getSessions({ user_id: Number(id) }),
        ])
        if (elderData.status === 'fulfilled') {
          setElder(elderData.value)
        } else {
          setElder(MOCK_ELDER)
        }
        if (sessionsData.status === 'fulfilled' && sessionsData.value.length > 0) {
          setSessions(sessionsData.value)
          // Load latest result
          const completedSession = sessionsData.value.find((s) => s.status === 'completed')
          if (completedSession) {
            try {
              const result = await getSessionResult(completedSession.id)
              setLatestResult(result)
            } catch {
              setLatestResult(MOCK_RESULT)
            }
          }
        } else {
          setSessions(MOCK_SESSIONS)
          setLatestResult(MOCK_RESULT)
        }
      } catch {
        setError('加载数据失败，显示演示数据')
        setElder(MOCK_ELDER)
        setSessions(MOCK_SESSIONS)
        setLatestResult(MOCK_RESULT)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [id])

  const calculateAge = (birthDate?: string) => {
    if (!birthDate) return '-'
    return `${dayjs().diff(dayjs(birthDate), 'year')} 岁`
  }

  const sessionColumns: ColumnsType<AssessmentSession> = [
    {
      title: '评估时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (
        <Space>
          <CalendarOutlined style={{ color: '#1677ff' }} />
          {dayjs(date).format('YYYY-MM-DD HH:mm')}
        </Space>
      ),
    },
    {
      title: '时长',
      key: 'duration',
      render: (_, record) => {
        if (record.started_at && record.completed_at) {
          const mins = dayjs(record.completed_at).diff(dayjs(record.started_at), 'minute')
          return <Text>{mins} 分钟</Text>
        }
        return <Text type="secondary">-</Text>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const cfg = statusConfig[status] || { text: status, color: 'default' }
        return <Tag color={cfg.color} style={{ borderRadius: 10 }}>{cfg.text}</Tag>
      },
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) =>
        record.status === 'completed' ? (
          <Button
            type="link"
            icon={<FileTextOutlined />}
            onClick={() => navigate(`/assessments/${record.id}`)}
            style={{ padding: 0 }}
          >
            查看报告
          </Button>
        ) : (
          <Text type="secondary">暂无报告</Text>
        ),
    },
  ]

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '120px 0' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 16 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/elders')}
          style={{ borderRadius: 8 }}
        >
          返回列表
        </Button>
        <div>
          <Title level={4} style={{ margin: 0 }}>老人详情</Title>
          <Text type="secondary">查看老人基本信息与评估历史</Text>
        </div>
      </div>

      {error && (
        <Alert type="warning" message={error} showIcon style={{ marginBottom: 16, borderRadius: 8 }} />
      )}

      <Row gutter={[20, 20]}>
        {/* Basic Info */}
        <Col xs={24} lg={8}>
          <Card
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
            bodyStyle={{ padding: 24 }}
          >
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Avatar
                size={80}
                style={{
                  background: elder?.gender === 'female' ? '#ffadd2' : '#bae0ff',
                  color: elder?.gender === 'female' ? '#c41d7f' : '#0958d9',
                  fontSize: 32,
                  fontWeight: 700,
                  marginBottom: 12,
                }}
                icon={<UserOutlined />}
              >
                {elder?.name?.[0]}
              </Avatar>
              <Title level={4} style={{ margin: '0 0 4px' }}>{elder?.name}</Title>
              <Text type="secondary">{elder?.phone || '未填写电话'}</Text>
            </div>

            <Divider style={{ margin: '16px 0' }} />

            <Descriptions column={1} size="small" labelStyle={{ color: '#888', width: 80 }}>
              <Descriptions.Item label="性别">
                {genderMap[elder?.gender || ''] || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="年龄">
                {calculateAge(elder?.birth_date)}
              </Descriptions.Item>
              <Descriptions.Item label="出生日期">
                {elder?.birth_date ? dayjs(elder.birth_date).format('YYYY年MM月DD日') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="文化程度">
                {educationLabel(elder?.education_years)}
              </Descriptions.Item>
              <Descriptions.Item label="注册时间">
                {dayjs(elder?.created_at).format('YYYY-MM-DD')}
              </Descriptions.Item>
            </Descriptions>

            <Divider style={{ margin: '16px 0' }} />

            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>评估总次数</Text>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#1677ff', marginTop: 4 }}>
                {sessions.length}
                <span style={{ fontSize: 14, color: '#999', fontWeight: 400, marginLeft: 4 }}>次</span>
              </div>
            </div>
          </Card>
        </Col>

        {/* Latest Result */}
        <Col xs={24} lg={16}>
          {latestResult && (
            <Card
              title={
                <Space>
                  <span style={{ width: 4, height: 18, background: '#1677ff', display: 'inline-block', borderRadius: 2 }} />
                  <Text strong>最新评估结果</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {dayjs(latestResult.created_at).format('YYYY-MM-DD HH:mm')}
                  </Text>
                </Space>
              }
              style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', marginBottom: 20 }}
            >
              <Row gutter={[16, 16]} align="middle">
                <Col xs={24} sm={10}>
                  <div style={{ textAlign: 'center', padding: '16px 0' }}>
                    <RiskBadge riskLevel={latestResult.risk_level} size="large" />
                    <div style={{ marginTop: 16 }}>
                      <Text type="secondary" style={{ fontSize: 13 }}>MMSE评分</Text>
                      <div style={{ fontSize: 36, fontWeight: 700, color: '#1677ff' }}>
                        {latestResult.mmse_score}
                        <span style={{ fontSize: 16, color: '#999', fontWeight: 400 }}>/30</span>
                      </div>
                    </div>
                  </div>
                </Col>
                <Col xs={24} sm={14}>
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13 }}>认知正常</Text>
                      <Text strong style={{ color: '#52c41a' }}>{(latestResult.nc_probability * 100).toFixed(1)}%</Text>
                    </div>
                    <Progress percent={Math.round(latestResult.nc_probability * 100)} strokeColor="#52c41a" size="small" showInfo={false} />
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13 }}>轻度认知障碍</Text>
                      <Text strong style={{ color: '#faad14' }}>{(latestResult.mci_probability * 100).toFixed(1)}%</Text>
                    </div>
                    <Progress percent={Math.round(latestResult.mci_probability * 100)} strokeColor="#faad14" size="small" showInfo={false} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13 }}>阿尔茨海默病</Text>
                      <Text strong style={{ color: '#ff4d4f' }}>{(latestResult.ad_probability * 100).toFixed(1)}%</Text>
                    </div>
                    <Progress percent={Math.round(latestResult.ad_probability * 100)} strokeColor="#ff4d4f" size="small" showInfo={false} />
                  </div>
                </Col>
              </Row>
              <Divider style={{ margin: '16px 0' }} />
              <CognitiveRadar domainScores={latestResult.domain_scores} height={300} />
            </Card>
          )}
        </Col>
      </Row>

      {/* Assessment History */}
      <Card
        title={
          <Space>
            <span style={{ width: 4, height: 18, background: '#722ed1', display: 'inline-block', borderRadius: 2 }} />
            <Text strong>评估历史记录</Text>
          </Space>
        }
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
      >
        <Table
          columns={sessionColumns}
          dataSource={sessions}
          rowKey="id"
          pagination={{ pageSize: 5, showTotal: (t) => `共 ${t} 条` }}
        />
      </Card>
    </div>
  )
}
