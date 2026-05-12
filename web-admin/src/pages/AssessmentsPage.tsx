import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Avatar,
  Button,
  Card,
  Col,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  EyeOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { getDashboardHighRiskList, getSessions } from '../services/api'
import type { AssessmentSession } from '../types'
import RiskBadge from '../components/RiskBadge'

const { Title, Text } = Typography

type SessionRow = AssessmentSession & {
  user_name?: string
  community_name?: string
  risk_level?: 'normal' | 'mild_risk' | 'high_risk'
}

const statusLabelMap: Record<string, string> = {
  pending: '待开始',
  in_progress: '进行中',
  completed: '已完成',
  failed: '失败',
}

const statusColorMap: Record<string, string> = {
  pending: 'default',
  in_progress: 'processing',
  completed: 'success',
  failed: 'error',
}

export default function AssessmentsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const riskLevelFilter = (searchParams.get('risk_level') || '').trim()
  const queueRiskHigh = riskLevelFilter === 'high_risk'

  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState<SessionRow[]>([])
  const [highRiskSessionIdSet, setHighRiskSessionIdSet] = useState<Set<number>>(new Set())

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [sessionsRes, highRiskRes] = await Promise.allSettled([
        getSessions({ page: 1, page_size: 500 }),
        queueRiskHigh ? getDashboardHighRiskList(500) : Promise.resolve([]),
      ])

      if (sessionsRes.status === 'fulfilled') {
        setRows((sessionsRes.value || []) as SessionRow[])
      } else {
        setRows([])
      }

      if (highRiskRes.status === 'fulfilled' && Array.isArray(highRiskRes.value)) {
        const ids = new Set<number>()
        ;(highRiskRes.value as Array<{ session_id?: number }>).forEach((item) => {
          if (typeof item.session_id === 'number') ids.add(item.session_id)
        })
        setHighRiskSessionIdSet(ids)
      } else {
        setHighRiskSessionIdSet(new Set())
      }
    } finally {
      setLoading(false)
    }
  }, [queueRiskHigh])

  useEffect(() => {
    void fetchData()
  }, [fetchData])

  const filteredRows = useMemo(() => {
    let list = [...rows]
    if (statusFilter) {
      list = list.filter((item) => item.status === statusFilter)
    }

    if (queueRiskHigh) {
      list = list.filter(
        (item) => highRiskSessionIdSet.has(item.id) || item.risk_level === 'high_risk'
      )
    } else if (riskLevelFilter) {
      list = list.filter((item) => item.risk_level === riskLevelFilter)
    }

    return list.sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf())
  }, [rows, statusFilter, queueRiskHigh, riskLevelFilter, highRiskSessionIdSet])

  const clearRiskFilter = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('risk_level')
    setSearchParams(next)
  }

  const columns: ColumnsType<SessionRow> = [
    {
      title: '评估编号',
      dataIndex: 'id',
      width: 110,
      render: (value: number) => <Text code>#{String(value).padStart(4, '0')}</Text>,
    },
    {
      title: '老人信息',
      width: 220,
      render: (_, row) => (
        <Space>
          <Avatar style={{ background: '#e6f4ff', color: '#1677ff', fontWeight: 700 }}>
            {(row.user_name || row.user?.name || '?')[0]}
          </Avatar>
          <div>
            <div style={{ fontWeight: 600 }}>{row.user_name || row.user?.name || `用户 #${row.user_id}`}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {row.community_name || '-'}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      align: 'center',
      render: (status: string) => (
        <Tag color={statusColorMap[status] || 'default'}>{statusLabelMap[status] || status}</Tag>
      ),
    },
    {
      title: '风险等级',
      width: 130,
      align: 'center',
      render: (_, row) => {
        if (row.risk_level) return <RiskBadge riskLevel={row.risk_level} />
        if (highRiskSessionIdSet.has(row.id)) return <RiskBadge riskLevel="high_risk" />
        return <Text type="secondary">-</Text>
      },
    },
    {
      title: '开始时间',
      width: 180,
      render: (_, row) => (row.started_at ? dayjs(row.started_at).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      width: 120,
      align: 'center',
      render: (_, row) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          disabled={row.status !== 'completed'}
          onClick={() => navigate(`/assessments/${row.id}`)}
        >
          查看报告
        </Button>
      ),
    },
  ]

  return (
    <div className="mg-page">
      <div className="mg-page-header">
        <div>
          <Title level={4} className="mg-page-title">
            评估管理
          </Title>
          <Text className="mg-page-subtitle">管理认知评估会话与报告</Text>
        </div>
      </div>

      <Card
        className="mg-panel-card"
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
        styles={{ body: { padding: '20px 24px' } }}
      >
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="按状态筛选"
              allowClear
              value={statusFilter}
              style={{ width: '100%' }}
              onChange={(value) => setStatusFilter(value)}
              options={[
                { label: '待开始', value: 'pending' },
                { label: '进行中', value: 'in_progress' },
                { label: '已完成', value: 'completed' },
                { label: '失败', value: 'failed' },
              ]}
            />
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => void fetchData()}>
                刷新
              </Button>
              {queueRiskHigh && (
                <Button icon={<ExclamationCircleOutlined />} onClick={clearRiskFilter}>
                  取消高风险筛选
                </Button>
              )}
            </Space>
          </Col>
        </Row>

        {queueRiskHigh && (
          <div style={{ marginBottom: 12 }}>
            <Tag color="red">当前为工作台跳转：高风险队列</Tag>
          </div>
        )}

        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={filteredRows}
          scroll={{ x: 980 }}
          pagination={{
            pageSize: 12,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>
    </div>
  )
}
