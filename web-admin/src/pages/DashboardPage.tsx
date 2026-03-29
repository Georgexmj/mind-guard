import { useEffect, useState } from 'react'
import {
  Row, Col, Card, Statistic, Typography, List, Spin, Tag, Space, Avatar, Badge,
} from 'antd'
import {
  TeamOutlined, FileTextOutlined, WarningOutlined, CalendarOutlined,
  ArrowUpOutlined, ExclamationCircleFilled,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'
import { getDashboardStats, getSessions, getDashboardMonthlyTrend, getDashboardHighRiskList } from '../services/api'
import type { DashboardStats, AssessmentSession } from '../types'
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

const MOCK_HIGH_RISK: HighRiskItem[] = [
  { session_id: 4, elder_id: 4, elder_name: '陈福寿', phone: '137****0004', mmse_score: 18, ad_probability: 0.62, assessed_at: '2026-03-15T10:30:00' },
  { session_id: 9, elder_id: 9, elder_name: '孙美英', phone: '131****0009', mmse_score: 21, ad_probability: 0.48, assessed_at: '2026-03-17T14:00:00' },
  { session_id: 12, elder_id: 2, elder_name: '李德明', phone: '139****0002', mmse_score: 23, ad_probability: 0.35, assessed_at: '2026-03-18T09:15:00' },
]

const MOCK_SESSIONS: (AssessmentSession & { user_name?: string; risk_level?: string })[] = [
  { id: 1, user_id: 1, status: 'completed', created_at: dayjs().subtract(1, 'hour').toISOString(), user_name: '王秀兰', risk_level: 'normal' },
  { id: 2, user_id: 2, status: 'completed', created_at: dayjs().subtract(2, 'hour').toISOString(), user_name: '李德明', risk_level: 'mild_risk' },
  { id: 3, user_id: 3, status: 'in_progress', created_at: dayjs().subtract(3, 'hour').toISOString(), user_name: '张桂珍', risk_level: undefined },
  { id: 4, user_id: 4, status: 'completed', created_at: dayjs().subtract(5, 'hour').toISOString(), user_name: '陈福寿', risk_level: 'high_risk' },
  { id: 5, user_id: 5, status: 'completed', created_at: dayjs().subtract(8, 'hour').toISOString(), user_name: '刘淑华', risk_level: 'normal' },
]

const statCards = (stats: DashboardStats) => [
  { title: '总老人数', value: stats.total_elders, icon: <TeamOutlined />, color: '#1677ff', bgColor: '#e6f4ff', suffix: '人', trend: '+12' },
  { title: '总评估次数', value: stats.total_sessions, icon: <FileTextOutlined />, color: '#52c41a', bgColor: '#f6ffed', suffix: '次', trend: '+28' },
  { title: '高风险人数', value: stats.high_risk_count, icon: <WarningOutlined />, color: '#ff4d4f', bgColor: '#fff2f0', suffix: '人', trend: '+3' },
  { title: '今日评估', value: stats.today_sessions, icon: <CalendarOutlined />, color: '#722ed1', bgColor: '#f9f0ff', suffix: '次', trend: '+2' },
]

const statusText: Record<string, { text: string; color: string }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '待开始', color: 'default' },
  failed: { text: '已失败', color: 'error' },
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>(MOCK_STATS)
  const [sessions, setSessions] = useState<typeof MOCK_SESSIONS>(MOCK_SESSIONS)
  const [trend, setTrend] = useState<{ month: string; count: number }[]>(MOCK_TREND)
  const [highRisk, setHighRisk] = useState<HighRiskItem[]>(MOCK_HIGH_RISK)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, sessionsRes, trendRes, highRiskRes] = await Promise.allSettled([
          getDashboardStats(),
          getSessions({ page: 1, page_size: 8 }),
          getDashboardMonthlyTrend(6),
          getDashboardHighRiskList(5),
        ])
        if (statsRes.status === 'fulfilled') setStats(statsRes.value)
        if (sessionsRes.status === 'fulfilled' && sessionsRes.value.length > 0)
          setSessions(sessionsRes.value as typeof MOCK_SESSIONS)
        if (trendRes.status === 'fulfilled' && trendRes.value.length > 0)
          setTrend(trendRes.value)
        if (highRiskRes.status === 'fulfilled' && (highRiskRes.value as HighRiskItem[]).length > 0)
          setHighRisk(highRiskRes.value as HighRiskItem[])
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const pieOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)', backgroundColor: 'rgba(0,21,41,0.85)', textStyle: { color: '#fff' }, borderColor: 'transparent' },
    legend: { orient: 'vertical', right: 20, top: 'center', textStyle: { fontSize: 13, color: '#555' }, itemGap: 14 },
    series: [{
      name: '风险分布', type: 'pie', radius: ['42%', '72%'], center: ['38%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' }, itemStyle: { shadowBlur: 12, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' } },
      data: [
        { value: stats.total_elders - stats.high_risk_count - Math.round(stats.total_elders * 0.15), name: '认知正常', itemStyle: { color: '#52c41a' } },
        { value: Math.round(stats.total_elders * 0.15), name: '轻度风险', itemStyle: { color: '#faad14' } },
        { value: stats.high_risk_count, name: '高风险', itemStyle: { color: '#ff4d4f' } },
      ],
    }],
  }

  const trendOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: trend.map((t) => t.month),
      axisLabel: { fontSize: 12, color: '#999' },
      axisLine: { lineStyle: { color: '#e8e8e8' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: '#999' },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
    },
    series: [{
      data: trend.map((t) => t.count),
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { color: '#1677ff', width: 3 },
      itemStyle: { color: '#1677ff', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(22,119,255,0.25)' }, { offset: 1, color: 'rgba(22,119,255,0.02)' }],
        },
      },
    }],
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '120px 0' }}><Spin size="large" tip="加载数据中..." /></div>
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>系统概览</Title>
        <Text type="secondary" style={{ fontSize: 13 }}>{dayjs().format('YYYY年MM月DD日')} · 数据实时更新</Text>
      </div>

      {/* Stat Cards */}
      <Row gutter={[20, 20]} style={{ marginBottom: 24 }}>
        {statCards(stats).map((card) => (
          <Col xs={24} sm={12} lg={6} key={card.title}>
            <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflow: 'hidden' }} bodyStyle={{ padding: '20px 24px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div style={{ flex: 1 }}>
                  <Text type="secondary" style={{ fontSize: 13 }}>{card.title}</Text>
                  <div style={{ marginTop: 8 }}>
                    <Statistic value={card.value} suffix={<span style={{ fontSize: 14, color: '#999' }}>{card.suffix}</span>} valueStyle={{ color: card.color, fontSize: 32, fontWeight: 700 }} />
                  </div>
                  <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <ArrowUpOutlined style={{ fontSize: 11, color: '#52c41a' }} />
                    <Text style={{ fontSize: 12, color: '#52c41a' }}>{card.trend}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>本月</Text>
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

      {/* Row 1: Pie + Monthly Trend */}
      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col xs={24} lg={9}>
          <Card
            title={<Space><span style={{ width: 4, height: 18, background: '#1677ff', display: 'inline-block', borderRadius: 2 }} /><Text strong>认知风险分布</Text></Space>}
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
            bodyStyle={{ padding: '8px 0' }}
          >
            <ReactECharts option={pieOption} style={{ height: 260 }} opts={{ renderer: 'svg' }} />
          </Card>
        </Col>
        <Col xs={24} lg={15}>
          <Card
            title={<Space><span style={{ width: 4, height: 18, background: '#52c41a', display: 'inline-block', borderRadius: 2 }} /><Text strong>月度评估趋势（近6个月）</Text></Space>}
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
            bodyStyle={{ padding: '8px 16px' }}
          >
            <ReactECharts option={trendOption} style={{ height: 260 }} opts={{ renderer: 'svg' }} />
          </Card>
        </Col>
      </Row>

      {/* Row 2: High-Risk Alerts + Recent Sessions */}
      <Row gutter={[20, 20]}>
        <Col xs={24} lg={10}>
          <Card
            title={
              <Space>
                <span style={{ width: 4, height: 18, background: '#ff4d4f', display: 'inline-block', borderRadius: 2 }} />
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
            title={<Space><span style={{ width: 4, height: 18, background: '#722ed1', display: 'inline-block', borderRadius: 2 }} /><Text strong>最近评估记录</Text></Space>}
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
