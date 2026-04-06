import { useEffect, useMemo, useState } from 'react'
import {
  Avatar,
  Badge,
  Button,
  Card,
  Col,
  List,
  Row,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd'
import {
  ArrowUpOutlined,
  CalendarOutlined,
  ExclamationCircleFilled,
  FileTextOutlined,
  TeamOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  getDashboardHighRiskList,
  getDashboardMonthlyTrend,
  getDashboardStats,
  getDashboardWorkbenchQueues,
  getSessions,
} from '../services/api'
import type { AssessmentSession, DashboardStats, WorkbenchQueues } from '../types'
import RiskBadge from '../components/RiskBadge'

const { Title, Text } = Typography

interface HighRiskItem {
  session_id: number
  elder_id: number
  elder_name: string
  phone?: string
  mmse_score?: number
  ad_probability?: number
  assessed_at?: string
}

const MOCK_STATS: DashboardStats = {
  total_elders: 128,
  total_sessions: 342,
  high_risk_count: 23,
  today_sessions: 7,
}

const MOCK_TREND = [
  { month: '2025-10', count: 28 },
  { month: '2025-11', count: 34 },
  { month: '2025-12', count: 41 },
  { month: '2026-01', count: 38 },
  { month: '2026-02', count: 52 },
  { month: '2026-03', count: 45 },
]

const MOCK_HIGH_RISK: HighRiskItem[] = []
const MOCK_SESSIONS: (AssessmentSession & { user_name?: string; risk_level?: string })[] = []
const MOCK_WORKBENCH: WorkbenchQueues = {
  high_risk: [],
  reassessment_due: [],
  low_adherence: [],
  counts: { high_risk: 0, reassessment_due: 0, low_adherence: 0 },
}

const statusText: Record<string, { text: string; color: string }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '待开始', color: 'default' },
  failed: { text: '失败', color: 'error' },
}

const statCards = (stats: DashboardStats) => [
  {
    title: '总老人数量',
    value: stats.total_elders,
    icon: <TeamOutlined />,
    color: '#1677ff',
    bgColor: '#e6f4ff',
    suffix: '人',
    trend: '+12',
  },
  {
    title: '总评估次数',
    value: stats.total_sessions,
    icon: <FileTextOutlined />,
    color: '#52c41a',
    bgColor: '#f6ffed',
    suffix: '次',
    trend: '+28',
  },
  {
    title: '高风险人数',
    value: stats.high_risk_count,
    icon: <WarningOutlined />,
    color: '#ff4d4f',
    bgColor: '#fff2f0',
    suffix: '人',
    trend: '+3',
  },
  {
    title: '今日评估',
    value: stats.today_sessions,
    icon: <CalendarOutlined />,
    color: '#722ed1',
    bgColor: '#f9f0ff',
    suffix: '次',
    trend: '+2',
  },
]

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats>(MOCK_STATS)
  const [sessions, setSessions] = useState<typeof MOCK_SESSIONS>(MOCK_SESSIONS)
  const [trend, setTrend] = useState<{ month: string; count: number }[]>(MOCK_TREND)
  const [highRisk, setHighRisk] = useState<HighRiskItem[]>(MOCK_HIGH_RISK)
  const [workbench, setWorkbench] = useState<WorkbenchQueues>(MOCK_WORKBENCH)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, sessionsRes, trendRes, highRiskRes, workbenchRes] = await Promise.allSettled([
          getDashboardStats(),
          getSessions({ page: 1, page_size: 8 }),
          getDashboardMonthlyTrend(6),
          getDashboardHighRiskList(5),
          getDashboardWorkbenchQueues(10),
        ])

        if (statsRes.status === 'fulfilled') setStats(statsRes.value)
        if (sessionsRes.status === 'fulfilled' && sessionsRes.value.length > 0) {
          setSessions(sessionsRes.value as typeof MOCK_SESSIONS)
        }
        if (trendRes.status === 'fulfilled' && trendRes.value.length > 0) {
          setTrend(trendRes.value)
        }
        if (highRiskRes.status === 'fulfilled' && (highRiskRes.value as HighRiskItem[]).length > 0) {
          setHighRisk(highRiskRes.value as HighRiskItem[])
        }
        if (workbenchRes.status === 'fulfilled') {
          setWorkbench(workbenchRes.value)
        }
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const pieOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
      legend: { orient: 'vertical', right: 20, top: 'center' },
      series: [
        {
          name: '风险分布',
          type: 'pie',
          radius: ['42%', '72%'],
          center: ['38%', '50%'],
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
          label: { show: false },
          data: [
            {
              value: Math.max(stats.total_elders - stats.high_risk_count - Math.round(stats.total_elders * 0.15), 0),
              name: '认知正常',
              itemStyle: { color: '#52c41a' },
            },
            {
              value: Math.round(stats.total_elders * 0.15),
              name: '轻度风险',
              itemStyle: { color: '#faad14' },
            },
            {
              value: stats.high_risk_count,
              name: '高风险',
              itemStyle: { color: '#ff4d4f' },
            },
          ],
        },
      ],
    }),
    [stats]
  )

  const trendOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: {
        type: 'category',
        data: trend.map((t) => t.month),
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          data: trend.map((t) => t.count),
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { color: '#1677ff', width: 3 },
          itemStyle: { color: '#1677ff', borderColor: '#fff', borderWidth: 2 },
        },
      ],
    }),
    [trend]
  )

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '120px 0' }}>
        <Spin size="large" tip="加载数据中..." />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>
          系统概览
        </Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          {dayjs().format('YYYY年MM月DD日')} · 数据实时更新
        </Text>
      </div>

      <Row gutter={[20, 20]} style={{ marginBottom: 24 }}>
        {statCards(stats).map((card) => (
          <Col xs={24} sm={12} lg={6} key={card.title}>
            <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }} bodyStyle={{ padding: '20px 24px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div style={{ flex: 1 }}>
                  <Text type="secondary" style={{ fontSize: 13 }}>
                    {card.title}
                  </Text>
                  <div style={{ marginTop: 8 }}>
                    <Statistic
                      value={card.value}
                      suffix={<span style={{ fontSize: 14, color: '#999' }}>{card.suffix}</span>}
                      valueStyle={{ color: card.color, fontSize: 32, fontWeight: 700 }}
                    />
                  </div>
                  <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <ArrowUpOutlined style={{ fontSize: 11, color: '#52c41a' }} />
                    <Text style={{ fontSize: 12, color: '#52c41a' }}>{card.trend}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      本月
                    </Text>
                  </div>
                </div>
                <div style={{ width: 52, height: 52, borderRadius: 14, background: card.bgColor, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, color: card.color }}>
                  {card.icon}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col xs={24} lg={9}>
          <Card title="认知风险分布" style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
            <ReactECharts option={pieOption} style={{ height: 260 }} opts={{ renderer: 'svg' }} />
          </Card>
        </Col>
        <Col xs={24} lg={15}>
          <Card title="月度评估趋势（近6个月）" style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
            <ReactECharts option={trendOption} style={{ height: 260 }} opts={{ renderer: 'svg' }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col xs={24} lg={8}>
          <Card
            title={<Space><Text strong>高风险队列</Text><Badge count={workbench.counts.high_risk} /></Space>}
            extra={<Button type="link" size="small" onClick={() => navigate('/assessments?risk_level=high_risk')}>查看全部</Button>}
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
          >
            <List
              size="small"
              dataSource={workbench.high_risk.slice(0, 5)}
              locale={{ emptyText: '暂无' }}
              renderItem={(item) => (
                <List.Item>
                  <Space direction="vertical" size={0}>
                    <Text>{item.elder_name}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>MMSE {item.mmse_score ?? '--'}</Text>
                  </Space>
                  <Button type="link" size="small" onClick={() => navigate(`/assessments/${item.session_id}`)}>
                    详情
                  </Button>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title={<Space><Text strong>待复评队列</Text><Badge count={workbench.counts.reassessment_due} /></Space>}
            extra={<Button type="link" size="small" onClick={() => navigate('/elders?queue=reassessment_due')}>查看全部</Button>}
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
          >
            <List
              size="small"
              dataSource={workbench.reassessment_due.slice(0, 5)}
              locale={{ emptyText: '暂无' }}
              renderItem={(item) => (
                <List.Item>
                  <Space direction="vertical" size={0}>
                    <Text>{item.elder_name}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.next_reassessment_date} ({item.days_to_due}天)
                    </Text>
                  </Space>
                  <Button type="link" size="small" onClick={() => navigate(`/elders/${item.elder_id}`)}>
                    跳转
                  </Button>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title={<Space><Text strong>低依从队列</Text><Badge count={workbench.counts.low_adherence} /></Space>}
            extra={<Button type="link" size="small" onClick={() => navigate('/interventions?queue=low_adherence')}>查看全部</Button>}
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
          >
            <List
              size="small"
              dataSource={workbench.low_adherence.slice(0, 5)}
              locale={{ emptyText: '暂无' }}
              renderItem={(item) => (
                <List.Item>
                  <Space direction="vertical" size={0}>
                    <Text>{item.elder_name || `老人#${item.elder_id}`}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      连续未完成 {item.consecutive_missed_days} 天
                    </Text>
                  </Space>
                  <Button
                    type="link"
                    size="small"
                    onClick={() => navigate(`/interventions?queue=low_adherence&ticket_id=${item.ticket_id}`)}
                  >
                    处理
                  </Button>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]}>
        <Col xs={24} lg={10}>
          <Card
            title={
              <Space>
                <Text strong>高风险预警</Text>
                <Badge count={highRisk.length} style={{ backgroundColor: '#ff4d4f' }} />
              </Space>
            }
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
            bodyStyle={{ padding: '0 16px' }}
          >
            <List
              dataSource={highRisk}
              locale={{ emptyText: '暂无高风险记录' }}
              renderItem={(item) => (
                <List.Item style={{ padding: '12px 8px', borderBottom: '1px solid #f5f5f5' }}>
                  <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 12 }}>
                    <Avatar style={{ background: '#fff2f0', color: '#ff4d4f', flexShrink: 0 }} size={38} icon={<ExclamationCircleFilled />} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 14, color: '#1a1a2e' }}>{item.elder_name}</div>
                      <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>
                        MMSE: {item.mmse_score ?? '--'} · AD概率: {item.ad_probability == null ? '--' : `${Math.round(item.ad_probability * 100)}%`}
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: '#bbb', flexShrink: 0 }}>
                      {item.assessed_at ? dayjs(item.assessed_at).format('MM-DD') : ''}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={14}>
          <Card
            title={<Text strong>最近评估记录</Text>}
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
            bodyStyle={{ padding: '0 16px' }}
          >
            <List
              dataSource={sessions.slice(0, 6)}
              renderItem={(session) => {
                const s = session as AssessmentSession & { user_name?: string; risk_level?: string }
                const statusInfo = statusText[s.status] || { text: s.status, color: 'default' }
                return (
                  <List.Item style={{ padding: '12px 8px', borderBottom: '1px solid #f5f5f5' }}>
                    <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 12 }}>
                      <Avatar style={{ background: '#e6f4ff', color: '#1677ff', flexShrink: 0 }} size={38}>
                        {(s.user_name || '?')[0]}
                      </Avatar>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: 14, color: '#1a1a2e' }}>{s.user_name || `用户 #${s.user_id}`}</div>
                        <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>{dayjs(s.created_at).format('MM-DD HH:mm')}</div>
                      </div>
                      <Space>
                        <Tag color={statusInfo.color} style={{ borderRadius: 10 }}>{statusInfo.text}</Tag>
                        {s.risk_level && <RiskBadge riskLevel={s.risk_level as 'normal' | 'mild_risk' | 'high_risk'} />}
                      </Space>
                    </div>
                  </List.Item>
                )
              }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
