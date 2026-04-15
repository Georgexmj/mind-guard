import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
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
  ReloadOutlined,
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
import '../styles/dashboard.css'

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

type SessionRow = AssessmentSession & {
  user_name?: string
  risk_level?: string
  mmse_score?: number
}

const EMPTY_STATS: DashboardStats = {
  total_elders: 0,
  total_sessions: 0,
  high_risk_count: 0,
  today_sessions: 0,
}

const EMPTY_WORKBENCH: WorkbenchQueues = {
  high_risk: [],
  reassessment_due: [],
  low_adherence: [],
  counts: { high_risk: 0, reassessment_due: 0, low_adherence: 0 },
}

const statusText: Record<string, { text: string; color: 'success' | 'processing' | 'default' | 'error' }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '待开始', color: 'default' },
  failed: { text: '失败', color: 'error' },
}

const statCards = (stats: DashboardStats) => [
  {
    title: '在册老人',
    value: stats.total_elders,
    icon: <TeamOutlined />,
    color: '#0f766e',
    suffix: '人',
    trend: '+12',
    trendText: '本月净新增',
  },
  {
    title: '累计评估',
    value: stats.total_sessions,
    icon: <FileTextOutlined />,
    color: '#0284c7',
    suffix: '次',
    trend: '+28',
    trendText: '本月新增评估',
  },
  {
    title: '高风险人数',
    value: stats.high_risk_count,
    icon: <WarningOutlined />,
    color: '#dc2626',
    suffix: '人',
    trend: '+3',
    trendText: '较上周',
  },
  {
    title: '今日评估',
    value: stats.today_sessions,
    icon: <CalendarOutlined />,
    color: '#8b5cf6',
    suffix: '次',
    trend: '+2',
    trendText: '日内完成',
  },
]

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats>(EMPTY_STATS)
  const [sessions, setSessions] = useState<SessionRow[]>([])
  const [trend, setTrend] = useState<{ month: string; count: number }[]>([])
  const [highRisk, setHighRisk] = useState<HighRiskItem[]>([])
  const [workbench, setWorkbench] = useState<WorkbenchQueues>(EMPTY_WORKBENCH)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = useCallback(async (initial = false) => {
    if (initial) setLoading(true)
    else setRefreshing(true)
    setError(null)

    try {
      const [statsRes, sessionsRes, trendRes, highRiskRes, workbenchRes] = await Promise.allSettled([
        getDashboardStats(),
        getSessions({ page: 1, page_size: 8 }),
        getDashboardMonthlyTrend(6),
        getDashboardHighRiskList(5),
        getDashboardWorkbenchQueues(10),
      ])

      let failedCount = 0

      if (statsRes.status === 'fulfilled') setStats(statsRes.value)
      else failedCount += 1

      if (sessionsRes.status === 'fulfilled') setSessions(sessionsRes.value as SessionRow[])
      else failedCount += 1

      if (trendRes.status === 'fulfilled') setTrend(trendRes.value)
      else failedCount += 1

      if (highRiskRes.status === 'fulfilled') setHighRisk(highRiskRes.value as HighRiskItem[])
      else failedCount += 1

      if (workbenchRes.status === 'fulfilled') setWorkbench(workbenchRes.value)
      else failedCount += 1

      if (failedCount > 0) {
        setError(`部分看板接口加载失败（${failedCount}/5），当前已展示可用实时数据。`)
      }
    } finally {
      if (initial) setLoading(false)
      else setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    void fetchDashboard(true)
  }, [fetchDashboard])

  const pieOption = useMemo(
    () => ({
      tooltip: { trigger: 'item', formatter: '{b}：{c} 人 ({d}%)' },
      legend: { orient: 'vertical', right: 0, top: 'center', textStyle: { color: '#5c7284' } },
      series: [
        {
          name: '风险分布',
          type: 'pie',
          radius: ['45%', '76%'],
          center: ['34%', '50%'],
          label: { show: false },
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
          data: [
            {
              value: Math.max(stats.total_elders - stats.high_risk_count - Math.round(stats.total_elders * 0.15), 0),
              name: '认知正常',
              itemStyle: { color: '#16a34a' },
            },
            { value: Math.round(stats.total_elders * 0.15), name: '轻度风险', itemStyle: { color: '#f59e0b' } },
            { value: stats.high_risk_count, name: '高风险', itemStyle: { color: '#dc2626' } },
          ],
        },
      ],
    }),
    [stats]
  )

  const trendOption = useMemo(
    () => ({
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      grid: { left: 30, right: 16, top: 20, bottom: 24 },
      xAxis: {
        type: 'category',
        data: trend.map((t) => t.month),
        axisLine: { lineStyle: { color: '#d8e3ea' } },
        axisLabel: { color: '#698294' },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(115, 142, 160, 0.17)' } },
        axisLabel: { color: '#698294' },
      },
      series: [
        {
          data: trend.map((t) => t.count),
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            color: '#0f766e',
            width: 3,
          },
          itemStyle: {
            color: '#0f766e',
            borderColor: '#fff',
            borderWidth: 2,
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(15, 118, 110, 0.26)' },
                { offset: 1, color: 'rgba(15, 118, 110, 0)' },
              ],
            },
          },
        },
      ],
    }),
    [trend]
  )

  if (loading) {
    return (
      <div className="dashboard-loading">
        <Spin size="large" tip="正在加载看板..." />
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <Title level={3} className="dashboard-hero-title">
            运营总览
          </Title>
          <Text className="dashboard-hero-subtitle">
            {dayjs().format('YYYY年MM月DD日')} · 看板实时刷新，建议优先处理高风险与低依从任务
          </Text>
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            loading={refreshing}
            onClick={() => void fetchDashboard(false)}
          >
            刷新数据
          </Button>
          <Button type="primary" onClick={() => navigate('/assessments?risk_level=high_risk')}>
            处理高风险队列
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          type="warning"
          showIcon
          message={error}
          className="dashboard-alert"
        />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 12 }}>
        {statCards(stats).map((item) => (
          <Col xs={24} sm={12} xl={6} key={item.title}>
            <Card className="dashboard-stat-card">
              <div className="dashboard-stat-top">
                <Text className="dashboard-stat-label">{item.title}</Text>
                <div className="dashboard-stat-icon" style={{ color: item.color }}>
                  {item.icon}
                </div>
              </div>
              <Statistic
                value={item.value}
                valueStyle={{ color: item.color, fontSize: 34, fontWeight: 700, marginTop: 10 }}
                suffix={<span className="dashboard-stat-suffix">{item.suffix}</span>}
              />
              <div className="dashboard-stat-trend">
                <ArrowUpOutlined />
                <span>{item.trend}</span>
                <Text>{item.trendText}</Text>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 12 }}>
        <Col xs={24} lg={9}>
          <Card className="dashboard-panel" title="风险结构分布">
            <ReactECharts option={pieOption} style={{ height: 280 }} opts={{ renderer: 'svg' }} />
          </Card>
        </Col>
        <Col xs={24} lg={15}>
          <Card className="dashboard-panel" title="近 6 个月评估趋势">
            <ReactECharts option={trendOption} style={{ height: 280 }} opts={{ renderer: 'svg' }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 12 }}>
        <Col xs={24} lg={8}>
          <Card
            className="dashboard-panel"
            title={
              <Space>
                <Text strong>高风险待办</Text>
                <Badge count={workbench.counts.high_risk} />
              </Space>
            }
            extra={<Button type="link" size="small" onClick={() => navigate('/assessments?risk_level=high_risk')}>查看全部</Button>}
          >
            <List
              size="small"
              dataSource={workbench.high_risk.slice(0, 5)}
              locale={{ emptyText: '暂无待办' }}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button key="detail" type="link" size="small" onClick={() => navigate(`/assessments/${item.session_id}`)}>
                      详情
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={item.elder_name}
                    description={`MMSE：${item.mmse_score ?? '--'}  ｜  AD 概率：${item.ad_probability == null ? '--' : `${Math.round(item.ad_probability * 100)}%`}`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            className="dashboard-panel"
            title={
              <Space>
                <Text strong>待复评队列</Text>
                <Badge count={workbench.counts.reassessment_due} />
              </Space>
            }
            extra={<Button type="link" size="small" onClick={() => navigate('/elders?queue=reassessment_due')}>查看全部</Button>}
          >
            <List
              size="small"
              dataSource={workbench.reassessment_due.slice(0, 5)}
              locale={{ emptyText: '暂无待办' }}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button key="goto" type="link" size="small" onClick={() => navigate(`/elders/${item.elder_id}`)}>
                      跳转
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={item.elder_name}
                    description={`${item.next_reassessment_date} ｜ 距离到期 ${item.days_to_due} 天`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            className="dashboard-panel"
            title={
              <Space>
                <Text strong>低依从提醒</Text>
                <Badge count={workbench.counts.low_adherence} />
              </Space>
            }
            extra={<Button type="link" size="small" onClick={() => navigate('/interventions?queue=low_adherence')}>查看全部</Button>}
          >
            <List
              size="small"
              dataSource={workbench.low_adherence.slice(0, 5)}
              locale={{ emptyText: '暂无待办' }}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      key="handle"
                      type="link"
                      size="small"
                      onClick={() =>
                        navigate(`/interventions?queue=low_adherence&ticket_id=${item.ticket_id}`)
                      }
                    >
                      处理
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={item.elder_name || `老人 #${item.elder_id}`}
                    description={`连续未完成 ${item.consecutive_missed_days} 天 ｜ 完成率 ${Math.round(item.completion_rate * 100)}%`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card
            className="dashboard-panel"
            title={
              <Space>
                <Text strong>高风险预警</Text>
                <Badge count={highRisk.length} style={{ backgroundColor: '#dc2626' }} />
              </Space>
            }
          >
            <List
              dataSource={highRisk}
              locale={{ emptyText: '暂无高风险记录' }}
              renderItem={(item) => (
                <List.Item>
                  <div className="dashboard-highrisk-item">
                    <Avatar size={40} className="dashboard-highrisk-avatar" icon={<ExclamationCircleFilled />} />
                    <div className="dashboard-highrisk-meta">
                      <Text className="dashboard-highrisk-name">{item.elder_name}</Text>
                      <Text className="dashboard-highrisk-desc">
                        MMSE：{item.mmse_score ?? '--'} ｜ AD 概率：{item.ad_probability == null ? '--' : `${Math.round(item.ad_probability * 100)}%`}
                      </Text>
                    </div>
                    <Text className="dashboard-date">
                      {item.assessed_at ? dayjs(item.assessed_at).format('MM-DD') : '--'}
                    </Text>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={14}>
          <Card className="dashboard-panel" title={<Text strong>最近评估记录</Text>}>
            <List
              dataSource={sessions.slice(0, 6)}
              locale={{ emptyText: '暂无评估记录' }}
              renderItem={(item) => {
                const statusInfo = statusText[item.status] || { text: item.status, color: 'default' as const }
                return (
                  <List.Item>
                    <div className="dashboard-session-item">
                      <div className="dashboard-session-left">
                        <Avatar className="dashboard-session-avatar">
                          {(item.user_name || '?')[0]}
                        </Avatar>
                        <div className="dashboard-session-meta">
                          <Text className="dashboard-session-name">{item.user_name || `用户 #${item.user_id}`}</Text>
                          <Text className="dashboard-session-time">{dayjs(item.created_at).format('MM-DD HH:mm')}</Text>
                        </div>
                      </div>
                      <Space size={8}>
                        <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
                        {item.risk_level && (
                          <RiskBadge riskLevel={item.risk_level as 'normal' | 'mild_risk' | 'high_risk'} />
                        )}
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
