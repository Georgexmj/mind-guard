import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Row, Space, Spin, Tag, Typography } from 'antd'
import {
  ArrowUpOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  NotificationOutlined,
  RiseOutlined,
  ThunderboltOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { getElderDashboard } from '../services/api'
import type { ElderDashboardPayload } from '../types'
import '../styles/elder-dashboard.css'

const { Title, Text } = Typography

const toneIconMap = {
  teal: <RiseOutlined />,
  violet: <ClockCircleOutlined />,
  orange: <ThunderboltOutlined />,
  rose: <WarningOutlined />,
}

const statusTagMap = {
  pending: { text: '待完成', color: 'default' },
  due: { text: '即将开始', color: 'processing' },
  done: { text: '已完成', color: 'success' },
}

export default function ElderDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ElderDashboardPayload | null>(null)

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const payload = await getElderDashboard()
        setData(payload)
      } catch {
        setError('老人端看板加载失败，请稍后刷新重试。')
      } finally {
        setLoading(false)
      }
    }
    void run()
  }, [])

  const riskTone = useMemo(() => {
    const level = data?.risk_level || 'normal'
    if (level === 'high_risk') return 'high'
    if (level === 'mild_risk') return 'mild'
    return 'normal'
  }, [data?.risk_level])

  if (loading) {
    return (
      <div className="elder-dashboard-loading">
        <Spin size="large" tip="正在加载老人端看板..." />
      </div>
    )
  }

  if (!data) {
    return (
      <Alert
        type="error"
        showIcon
        message={error || '暂无可展示数据'}
      />
    )
  }

  return (
    <div className="elder-dashboard">
      <section className="elder-hero">
        <div>
          <Text className="elder-hero-kicker">认知守护 · 老人端</Text>
          <Title level={2} className="elder-hero-title">
            {data.greeting}，{data.elder_name}
          </Title>
          <Text className="elder-hero-subtitle">
            {data.next_assessment_at
              ? `下次建议评估：${dayjs(data.next_assessment_at).format('YYYY年MM月DD日 HH:mm')}`
              : '当前暂无待评估计划，请保持训练节奏'}
          </Text>
        </div>
        <div className="elder-hero-actions">
          <Tag className={`elder-risk-tag elder-risk-tag-${riskTone}`}>
            {data.risk_level === 'high_risk' ? '高风险关注' : data.risk_level === 'mild_risk' ? '轻度风险关注' : '风险平稳'}
          </Tag>
          <Button size="large" className="elder-ghost-btn" icon={<CalendarOutlined />}>
            查看评估记录
          </Button>
          <Button size="large" type="primary" className="elder-primary-btn" icon={<ThunderboltOutlined />}>
            开始今日训练
          </Button>
        </div>
      </section>

      {error && <Alert type="warning" showIcon message={error} style={{ marginBottom: 12 }} />}

      <Row gutter={[14, 14]} className="elder-stats-grid">
        {data.metrics.map((metric) => (
          <Col key={metric.key} xs={24} sm={12} xl={6}>
            <Card className={`elder-stat-card elder-stat-${metric.tone}`}>
              <div className="elder-stat-top">
                <Text>{metric.label}</Text>
                <div className="elder-stat-icon">{toneIconMap[metric.tone]}</div>
              </div>
              <div className="elder-stat-value">
                {metric.value}
                <span>{metric.unit || ''}</span>
              </div>
              <div className="elder-stat-delta">
                <ArrowUpOutlined />
                {metric.delta > 0 ? `+${metric.delta}` : metric.delta}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[14, 14]}>
        <Col xs={24} lg={15}>
          <Card className="elder-panel" title={<span className="elder-panel-title">今日安排</span>} extra={<Button type="link">查看全部</Button>}>
            <div className="elder-schedule-list">
              {data.schedule.map((item) => {
                const status = statusTagMap[item.status]
                return (
                  <div className="elder-schedule-row" key={item.id}>
                    <div>
                      <div className="elder-schedule-title">{item.title}</div>
                      <div className="elder-schedule-meta">
                        <ClockCircleOutlined /> {dayjs(item.at).format('HH:mm')} · {item.duration_minutes} 分钟
                      </div>
                    </div>
                    <Tag color={status.color}>{status.text}</Tag>
                  </div>
                )
              })}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={9}>
          <Card className="elder-panel" title={<span className="elder-panel-title">风险分布</span>}>
            <div className="elder-risk-bars">
              {data.risk_distribution.map((bucket) => {
                const total = data.risk_distribution.reduce((acc, cur) => acc + cur.count, 0) || 1
                const percent = Math.round((bucket.count / total) * 100)
                return (
                  <div key={bucket.label} className="elder-risk-row">
                    <div className="elder-risk-row-top">
                      <Text>{bucket.label}</Text>
                      <Text strong>{bucket.count}人</Text>
                    </div>
                    <div className="elder-risk-track">
                      <div className="elder-risk-fill" style={{ width: `${percent}%`, background: bucket.color }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[14, 14]}>
        <Col xs={24} lg={14}>
          <Card
            className="elder-panel"
            title={
              <Space className="elder-panel-title-wrap">
                <NotificationOutlined />
                <span className="elder-panel-title">最新提醒</span>
              </Space>
            }
          >
            <div className="elder-alert-list">
              {data.alerts.length === 0 && <Text type="secondary">暂无提醒</Text>}
              {data.alerts.map((alert) => (
                <div key={alert.id} className={`elder-alert elder-alert-${alert.level}`}>
                  <div>
                    <div className="elder-alert-title">{alert.title}</div>
                    <div className="elder-alert-content">{alert.content}</div>
                  </div>
                  <Text className="elder-alert-time">{dayjs(alert.created_at).format('MM-DD HH:mm')}</Text>
                </div>
              ))}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            className="elder-panel"
            title={
              <Space className="elder-panel-title-wrap">
                <CheckCircleOutlined />
                <span className="elder-panel-title">康复建议</span>
              </Space>
            }
          >
            <ul className="elder-tip-list">
              {data.tips.map((tip, index) => (
                <li key={tip}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  {tip}
                </li>
              ))}
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

