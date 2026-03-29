import { useEffect, useState, useCallback } from 'react'
import {
  Card,
  Table,
  Select,
  Button,
  Typography,
  Space,
  Tag,
  Avatar,
  Row,
  Col,
  Tooltip,
} from 'antd'
import {
  EyeOutlined,
  ReloadOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { getSessions } from '../services/api'
import type { AssessmentSession } from '../types'
import RiskBadge from '../components/RiskBadge'

const { Title, Text } = Typography

type SessionRow = AssessmentSession & {
  user_name?: string
  risk_level?: 'normal' | 'mild_risk' | 'high_risk'
  community_name?: string
}

const MOCK_SESSIONS: SessionRow[] = [
  { id: 1, user_id: 1, status: 'completed', started_at: '2024-03-22T09:00:00', completed_at: '2024-03-22T09:18:00', created_at: '2024-03-22T09:00:00', user_name: '王秀兰', risk_level: 'normal', community_name: '幸福社区' },
  { id: 2, user_id: 2, status: 'completed', started_at: '2024-03-22T10:30:00', completed_at: '2024-03-22T10:48:00', created_at: '2024-03-22T10:30:00', user_name: '李德明', risk_level: 'mild_risk', community_name: '幸福社区' },
  { id: 3, user_id: 3, status: 'in_progress', started_at: '2024-03-22T14:00:00', created_at: '2024-03-22T14:00:00', user_name: '张桂珍', community_name: '阳光社区' },
  { id: 4, user_id: 4, status: 'completed', started_at: '2024-03-21T09:00:00', completed_at: '2024-03-21T09:22:00', created_at: '2024-03-21T09:00:00', user_name: '陈福寿', risk_level: 'high_risk', community_name: '阳光社区' },
  { id: 5, user_id: 5, status: 'completed', started_at: '2024-03-21T14:30:00', completed_at: '2024-03-21T14:45:00', created_at: '2024-03-21T14:30:00', user_name: '刘淑华', risk_level: 'normal', community_name: '和谐社区' },
  { id: 6, user_id: 6, status: 'completed', started_at: '2024-03-20T09:00:00', completed_at: '2024-03-20T09:20:00', created_at: '2024-03-20T09:00:00', user_name: '赵建国', risk_level: 'mild_risk', community_name: '和谐社区' },
  { id: 7, user_id: 7, status: 'completed', started_at: '2024-03-20T11:00:00', completed_at: '2024-03-20T11:15:00', created_at: '2024-03-20T11:00:00', user_name: '周金凤', risk_level: 'normal', community_name: '幸福社区' },
  { id: 8, user_id: 8, status: 'failed', started_at: '2024-03-19T15:00:00', created_at: '2024-03-19T15:00:00', user_name: '吴永祥', community_name: '阳光社区' },
  { id: 9, user_id: 9, status: 'completed', started_at: '2024-03-19T09:30:00', completed_at: '2024-03-19T09:52:00', created_at: '2024-03-19T09:30:00', user_name: '孙美英', risk_level: 'high_risk', community_name: '幸福社区' },
  { id: 10, user_id: 10, status: 'completed', started_at: '2024-03-18T10:00:00', completed_at: '2024-03-18T10:18:00', created_at: '2024-03-18T10:00:00', user_name: '胡长寿', risk_level: 'normal', community_name: '和谐社区' },
  { id: 11, user_id: 1, status: 'pending', created_at: '2024-03-23T08:00:00', user_name: '王秀兰', community_name: '幸福社区' },
]

const statusConfig: Record<string, { text: string; color: string; icon: React.ReactNode }> = {
  completed: { text: '已完成', color: 'success', icon: <CheckCircleOutlined /> },
  in_progress: { text: '进行中', color: 'processing', icon: <ClockCircleOutlined /> },
  pending: { text: '待开始', color: 'default', icon: <ClockCircleOutlined /> },
  failed: { text: '已失败', color: 'error', icon: <ExclamationCircleOutlined /> },
}

export default function AssessmentsPage() {
  const [sessions, setSessions] = useState<SessionRow[]>(MOCK_SESSIONS)
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [page, setPage] = useState(1)
  const pageSize = 10
  const navigate = useNavigate()

  const fetchSessions = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getSessions({ status: statusFilter, page, page_size: pageSize })
      if (res && res.length > 0) {
        setSessions(res as SessionRow[])
      }
    } catch {
      // Use mock data
    } finally {
      setLoading(false)
    }
  }, [statusFilter, page, pageSize])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const filteredSessions = statusFilter
    ? sessions.filter((s) => s.status === statusFilter)
    : sessions

  const handleReset = () => {
    setStatusFilter(undefined)
    setPage(1)
  }

  const getDuration = (session: SessionRow) => {
    if (session.started_at && session.completed_at) {
      const mins = dayjs(session.completed_at).diff(dayjs(session.started_at), 'minute')
      return `${mins} 分钟`
    }
    return '-'
  }

  const columns: ColumnsType<SessionRow> = [
    {
      title: '评估编号',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id) => (
        <Text style={{ fontFamily: 'monospace', color: '#1677ff', fontWeight: 600 }}>
          #{String(id).padStart(4, '0')}
        </Text>
      ),
    },
    {
      title: '老人信息',
      key: 'user',
      width: 180,
      render: (_, record) => (
        <Space>
          <Avatar
            size={32}
            style={{ background: '#e6f4ff', color: '#1677ff', fontWeight: 700, fontSize: 14 }}
          >
            {(record.user_name || '?')[0]}
          </Avatar>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{record.user_name || `用户#${record.user_id}`}</div>
            <div style={{ fontSize: 12, color: '#999' }}>{record.community_name || '-'}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '开始时间',
      key: 'time',
      width: 160,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text style={{ fontSize: 13 }}>
            {record.started_at ? dayjs(record.started_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Text>
          {record.completed_at && (
            <Text type="secondary" style={{ fontSize: 11 }}>
              耗时 {getDuration(record)}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      align: 'center',
      render: (status) => {
        const cfg = statusConfig[status] || { text: status, color: 'default', icon: null }
        return (
          <Tag
            color={cfg.color}
            icon={cfg.icon}
            style={{ borderRadius: 12, padding: '0 10px' }}
          >
            {cfg.text}
          </Tag>
        )
      },
    },
    {
      title: '风险等级',
      key: 'risk',
      width: 120,
      align: 'center',
      render: (_, record) =>
        record.risk_level ? (
          <RiskBadge riskLevel={record.risk_level} />
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>-</Text>
        ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 130,
      render: (date) => (
        <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm:ss')}>
          <Text style={{ fontSize: 12, color: '#999' }}>{dayjs(date).format('MM-DD HH:mm')}</Text>
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      align: 'center',
      fixed: 'right',
      render: (_, record) =>
        record.status === 'completed' ? (
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/assessments/${record.id}`)}
            style={{ padding: 0 }}
          >
            查看报告
          </Button>
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>暂无</Text>
        ),
    },
  ]

  // Stats summary
  const totalCount = sessions.length
  const completedCount = sessions.filter((s) => s.status === 'completed').length
  const highRiskCount = sessions.filter((s) => s.risk_level === 'high_risk').length
  const inProgressCount = sessions.filter((s) => s.status === 'in_progress').length

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>评估管理</Title>
        <Text type="secondary">管理所有认知评估记录</Text>
      </div>

      {/* Quick stats */}
      <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
        {[
          { label: '全部评估', value: totalCount, color: '#1677ff', bg: '#e6f4ff', icon: <FileTextOutlined /> },
          { label: '已完成', value: completedCount, color: '#52c41a', bg: '#f6ffed', icon: <CheckCircleOutlined /> },
          { label: '进行中', value: inProgressCount, color: '#1677ff', bg: '#e6f4ff', icon: <ClockCircleOutlined /> },
          { label: '高风险', value: highRiskCount, color: '#ff4d4f', bg: '#fff2f0', icon: <ExclamationCircleOutlined /> },
        ].map((item) => (
          <Col xs={12} sm={6} key={item.label}>
            <Card
              style={{ borderRadius: 10, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', cursor: 'pointer' }}
              bodyStyle={{ padding: '14px 18px' }}
            >
              <Space>
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 10,
                    background: item.bg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: item.color,
                    fontSize: 18,
                  }}
                >
                  {item.icon}
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#888' }}>{item.label}</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: item.color, lineHeight: 1.2 }}>{item.value}</div>
                </div>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        {/* Filter Bar */}
        <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="筛选状态"
              style={{ width: '100%' }}
              allowClear
              value={statusFilter}
              onChange={(val) => {
                setStatusFilter(val)
                setPage(1)
              }}
              options={[
                { label: '已完成', value: 'completed' },
                { label: '进行中', value: 'in_progress' },
                { label: '待开始', value: 'pending' },
                { label: '已失败', value: 'failed' },
              ]}
            />
          </Col>
          <Col>
            <Button icon={<ReloadOutlined />} onClick={handleReset} style={{ borderRadius: 8 }}>
              重置
            </Button>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={filteredSessions}
          rowKey="id"
          loading={loading}
          scroll={{ x: 850 }}
          pagination={{
            current: page,
            pageSize,
            total: filteredSessions.length,
            onChange: (p) => setPage(p),
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条记录`,
          }}
        />
      </Card>
    </div>
  )
}
