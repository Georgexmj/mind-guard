import { useEffect, useState } from 'react'
import {
  Alert,
  Avatar,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Progress,
  Row,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from 'antd'
import { ArrowLeftOutlined, CalendarOutlined, FileTextOutlined, UserOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'

import { getElderById, getSessionResult, getSessions } from '../services/api'
import type { AssessmentResult, AssessmentSession, User } from '../types'
import CognitiveRadar from '../components/CognitiveRadar'
import RiskBadge from '../components/RiskBadge'

const { Title, Text } = Typography

const statusConfig: Record<string, { text: string; color: string }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '待开始', color: 'default' },
  failed: { text: '失败', color: 'error' },
}

const educationLabel = (years?: number): string => {
  if (years == null) return '-'
  if (years <= 6) return '小学'
  if (years <= 9) return '初中'
  if (years <= 12) return '高中'
  if (years <= 15) return '大专'
  return '本科及以上'
}

const genderMap: Record<string, string> = {
  male: '男',
  female: '女',
}

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
      if (!id) {
        setError('缺少老人ID，无法加载详情。')
        setLoading(false)
        return
      }

      const elderId = Number(id)
      if (Number.isNaN(elderId)) {
        setError('老人ID格式不正确。')
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)
      try {
        const elderData = await getElderById(elderId)
        setElder(elderData)

        const sessionsData = await getSessions({ user_id: elderId })
        setSessions(sessionsData || [])

        const latestCompletedSession = (sessionsData || [])
          .filter((session) => session.status === 'completed')
          .sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf())[0]

        if (latestCompletedSession) {
          try {
            const result = await getSessionResult(latestCompletedSession.id)
            setLatestResult(result)
          } catch {
            setLatestResult(null)
            setError('老人基本信息已加载，但最新评估结果获取失败。')
          }
        } else {
          setLatestResult(null)
        }
      } catch {
        setElder(null)
        setSessions([])
        setLatestResult(null)
        setError('加载老人详情失败，请检查后端接口或权限配置。')
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
        return (
          <Tag color={cfg.color} style={{ borderRadius: 10 }}>
            {cfg.text}
          </Tag>
        )
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

  if (!elder) {
    return (
      <Alert
        type="error"
        showIcon
        message="未找到老人信息"
        description={error || '请返回列表后重试。'}
        action={
          <Button type="primary" onClick={() => navigate('/elders')}>
            返回列表
          </Button>
        }
      />
    )
  }

  return (
    <div className="mg-page">
      <div className="mg-page-header" style={{ alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/elders')} style={{ borderRadius: 8 }}>
          返回列表
        </Button>
        <div>
          <Title level={4} className="mg-page-title">
            老人详情
          </Title>
          <Text className="mg-page-subtitle">查看老人基本信息与评估历史</Text>
          </div>
        </div>
      </div>

      {error && <Alert type="warning" message={error} showIcon style={{ marginBottom: 16, borderRadius: 8 }} />}

      <Row gutter={[20, 20]}>
        <Col xs={24} lg={8}>
          <Card
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
            bodyStyle={{ padding: 24 }}
          >
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Avatar
                size={80}
                style={{
                  background: elder.gender === 'female' ? '#ffadd2' : '#bae0ff',
                  color: elder.gender === 'female' ? '#c41d7f' : '#0958d9',
                  fontSize: 32,
                  fontWeight: 700,
                  marginBottom: 12,
                }}
                icon={<UserOutlined />}
              >
                {elder.name?.[0]}
              </Avatar>
              <Title level={4} style={{ margin: '0 0 4px' }}>
                {elder.name}
              </Title>
              <Text type="secondary">{elder.phone || '未填写电话'}</Text>
            </div>

            <Divider style={{ margin: '16px 0' }} />

            <Descriptions column={1} size="small" labelStyle={{ color: '#888', width: 90 }}>
              <Descriptions.Item label="性别">{genderMap[elder.gender || ''] || '-'}</Descriptions.Item>
              <Descriptions.Item label="年龄">{calculateAge(elder.birth_date)}</Descriptions.Item>
              <Descriptions.Item label="出生日期">
                {elder.birth_date ? dayjs(elder.birth_date).format('YYYY年MM月DD日') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="文化程度">{educationLabel(elder.education_years)}</Descriptions.Item>
              <Descriptions.Item label="注册时间">{dayjs(elder.created_at).format('YYYY-MM-DD')}</Descriptions.Item>
            </Descriptions>

            <Divider style={{ margin: '16px 0' }} />

            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                评估总次数
              </Text>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#1677ff', marginTop: 4 }}>
                {sessions.length}
                <span style={{ fontSize: 14, color: '#999', fontWeight: 400, marginLeft: 4 }}>次</span>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          {latestResult ? (
            <Card
              title={
                <Space>
                  <span
                    style={{ width: 4, height: 18, background: '#1677ff', display: 'inline-block', borderRadius: 2 }}
                  />
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
                      <Text type="secondary" style={{ fontSize: 13 }}>
                        MMSE评分
                      </Text>
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
                      <Text strong style={{ color: '#52c41a' }}>
                        {(latestResult.nc_probability * 100).toFixed(1)}%
                      </Text>
                    </div>
                    <Progress percent={Math.round(latestResult.nc_probability * 100)} strokeColor="#52c41a" size="small" showInfo={false} />
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13 }}>轻度认知障碍</Text>
                      <Text strong style={{ color: '#faad14' }}>
                        {(latestResult.mci_probability * 100).toFixed(1)}%
                      </Text>
                    </div>
                    <Progress percent={Math.round(latestResult.mci_probability * 100)} strokeColor="#faad14" size="small" showInfo={false} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13 }}>阿尔茨海默病风险</Text>
                      <Text strong style={{ color: '#ff4d4f' }}>
                        {(latestResult.ad_probability * 100).toFixed(1)}%
                      </Text>
                    </div>
                    <Progress percent={Math.round(latestResult.ad_probability * 100)} strokeColor="#ff4d4f" size="small" showInfo={false} />
                  </div>
                </Col>
              </Row>
              <Divider style={{ margin: '16px 0' }} />
              <CognitiveRadar domainScores={latestResult.domain_scores} height={300} />
            </Card>
          ) : (
            <Alert
              type="info"
              showIcon
              message="暂无评估结果"
              description="该老人尚无已完成评估，或结果接口暂时不可用。"
              style={{ marginBottom: 20 }}
            />
          )}
        </Col>
      </Row>

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
          locale={{ emptyText: '暂无评估记录' }}
          pagination={{ pageSize: 5, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  )
}
