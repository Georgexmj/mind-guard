import { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Progress,
  Button,
  Space,
  Spin,
  Alert,
  Descriptions,
  Table,
  Tag,
  Divider,
} from 'antd'
import {
  ArrowLeftOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  BulbOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { getSessionDetail } from '../services/api'
import type { AssessmentSession, AssessmentResult, DomainScores } from '../types'
import RiskBadge from '../components/RiskBadge'
import CognitiveRadar from '../components/CognitiveRadar'

const { Title, Text, Paragraph } = Typography

// Rich mock data for demo
const MOCK_SESSION: AssessmentSession & { result?: AssessmentResult; user_name?: string } = {
  id: 4,
  user_id: 4,
  status: 'completed',
  started_at: '2024-03-21T09:00:00',
  completed_at: '2024-03-21T09:22:00',
  created_at: '2024-03-21T09:00:00',
  user_name: '陈福寿',
  result: {
    id: 4,
    session_id: 4,
    risk_level: 'high_risk',
    nc_probability: 0.08,
    mci_probability: 0.31,
    ad_probability: 0.61,
    mmse_score: 18,
    domain_scores: {
      memory: 3.2,
      orientation: 5.1,
      language: 5.8,
      attention: 4.4,
      visuospatial: 3.7,
      executive: 4.0,
    },
    recommendation:
      '受试者在记忆力、视空间功能和执行功能方面存在明显缺损，MMSE评分(18分)低于正常阈值(24分)，认知障碍风险较高。强烈建议：\n1. 尽快前往神经内科或精神科进行专业评估；\n2. 完善神经影像学检查(头颅MRI)、神经心理学评估；\n3. 对家属进行认知障碍照护指导；\n4. 建议启动社区认知干预计划，每周参与认知训练活动；\n5. 一个月后进行随访复查。',
    created_at: '2024-03-21T09:22:00',
  },
}

const domainConfig: { key: keyof DomainScores; label: string; desc: string }[] = [
  { key: 'memory', label: '记忆力', desc: '短期记忆、工作记忆' },
  { key: 'orientation', label: '定向力', desc: '时间、地点、人物定向' },
  { key: 'language', label: '语言能力', desc: '语言理解、表达、命名' },
  { key: 'attention', label: '注意力', desc: '持续注意、选择性注意' },
  { key: 'visuospatial', label: '视空间', desc: '空间感知、视觉构建' },
  { key: 'executive', label: '执行功能', desc: '计划、组织、灵活性' },
]

const getScoreColor = (score: number): string => {
  if (score >= 8) return '#52c41a'
  if (score >= 5) return '#faad14'
  return '#ff4d4f'
}

const getScoreStatus = (score: number): 'success' | 'normal' | 'exception' => {
  if (score >= 8) return 'success'
  if (score >= 5) return 'normal'
  return 'exception'
}

const getScoreLabel = (score: number): string => {
  if (score >= 8) return '正常'
  if (score >= 5) return '轻度异常'
  return '明显受损'
}

const statusConfig: Record<string, { text: string; color: string }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '待开始', color: 'default' },
  failed: { text: '已失败', color: 'error' },
}

export default function AssessmentDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<typeof MOCK_SESSION | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!sessionId) return
      setLoading(true)
      try {
        const data = await getSessionDetail(Number(sessionId))
        setSession(data as typeof MOCK_SESSION)
      } catch {
        setError('无法连接到服务器，已加载演示数据')
        setSession(MOCK_SESSION)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [sessionId])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '120px 0' }}>
        <Spin size="large" tip="加载评估报告..." />
      </div>
    )
  }

  if (!session) {
    return (
      <Alert
        type="error"
        message="评估记录不存在"
        description="未找到该评估记录，请返回列表重新选择。"
        action={
          <Button onClick={() => navigate('/assessments')} type="primary">
            返回列表
          </Button>
        }
      />
    )
  }

  const result = session.result
  const duration =
    session.started_at && session.completed_at
      ? dayjs(session.completed_at).diff(dayjs(session.started_at), 'minute')
      : null
  const statusInfo = statusConfig[session.status] || { text: session.status, color: 'default' }

  const domainTableData = domainConfig.map((item) => ({
    key: item.key,
    label: item.label,
    desc: item.desc,
    score: result?.domain_scores[item.key] ?? 0,
  }))

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 16 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(-1)}
          style={{ borderRadius: 8 }}
        >
          返回
        </Button>
        <div>
          <Title level={4} style={{ margin: 0 }}>评估详情报告</Title>
          <Text type="secondary">
            评估编号 #{String(session.id).padStart(4, '0')} ·{' '}
            {dayjs(session.created_at).format('YYYY年MM月DD日 HH:mm')}
          </Text>
        </div>
      </div>

      {error && (
        <Alert
          type="warning"
          message={error}
          showIcon
          style={{ marginBottom: 16, borderRadius: 8 }}
          closable
        />
      )}

      {/* Session Info Card */}
      <Card
        style={{
          borderRadius: 12,
          border: 'none',
          boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
          marginBottom: 20,
        }}
        bodyStyle={{ padding: '20px 28px' }}
      >
        <Row gutter={[24, 16]} align="middle">
          <Col xs={24} sm={16}>
            <Descriptions column={{ xs: 1, sm: 2, md: 3 }} size="small">
              <Descriptions.Item
                label={
                  <Space>
                    <UserOutlined style={{ color: '#1677ff' }} />
                    <span>评估对象</span>
                  </Space>
                }
              >
                <Text strong>{session.user_name || `用户 #${session.user_id}`}</Text>
              </Descriptions.Item>
              <Descriptions.Item
                label={
                  <Space>
                    <ClockCircleOutlined style={{ color: '#722ed1' }} />
                    <span>开始时间</span>
                  </Space>
                }
              >
                {session.started_at
                  ? dayjs(session.started_at).format('MM-DD HH:mm')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item
                label={
                  <Space>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    <span>完成时间</span>
                  </Space>
                }
              >
                {session.completed_at
                  ? dayjs(session.completed_at).format('MM-DD HH:mm')
                  : '-'}
              </Descriptions.Item>
              {duration !== null && (
                <Descriptions.Item label="评估时长">
                  <Text strong style={{ color: '#1677ff' }}>{duration} 分钟</Text>
                </Descriptions.Item>
              )}
            </Descriptions>
          </Col>
          <Col xs={24} sm={8} style={{ textAlign: 'right' }}>
            <Tag
              color={statusInfo.color}
              style={{ fontSize: 14, padding: '4px 16px', borderRadius: 16 }}
            >
              {statusInfo.text}
            </Tag>
          </Col>
        </Row>
      </Card>

      {result ? (
        <>
          {/* Risk Level + MMSE Row */}
          <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
            {/* Risk Level Card */}
            <Col xs={24} md={8}>
              <Card
                style={{
                  borderRadius: 12,
                  border: 'none',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                  height: '100%',
                }}
                bodyStyle={{ padding: 28 }}
              >
                <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 16 }}>
                  综合风险评估
                </Text>
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <RiskBadge riskLevel={result.risk_level} size="large" />
                </div>
                <Divider style={{ margin: '20px 0' }} />
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>MMSE 认知评分</Text>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'baseline',
                      gap: 6,
                      marginTop: 6,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 48,
                        fontWeight: 800,
                        color: getScoreColor(result.mmse_score / 3),
                        lineHeight: 1,
                      }}
                    >
                      {result.mmse_score}
                    </span>
                    <span style={{ fontSize: 18, color: '#999' }}>/30</span>
                  </div>
                  <Progress
                    percent={Math.round((result.mmse_score / 30) * 100)}
                    strokeColor={{
                      '0%': '#ff4d4f',
                      '60%': '#faad14',
                      '80%': '#52c41a',
                    }}
                    showInfo={false}
                    style={{ marginTop: 8 }}
                  />
                  <Text style={{ fontSize: 11, color: '#999' }}>
                    正常标准: ≥24分 · 轻度损害: 18-23分 · 中重度损害: &lt;18分
                  </Text>
                </div>
              </Card>
            </Col>

            {/* Probability Bars */}
            <Col xs={24} md={16}>
              <Card
                title={
                  <Space>
                    <BarChartOutlined style={{ color: '#1677ff' }} />
                    <Text strong>认知诊断概率分析</Text>
                  </Space>
                }
                style={{
                  borderRadius: 12,
                  border: 'none',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                  height: '100%',
                }}
              >
                <div style={{ padding: '8px 0' }}>
                  {/* NC */}
                  <div style={{ marginBottom: 28 }}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginBottom: 10,
                      }}
                    >
                      <Space>
                        <div
                          style={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            background: '#52c41a',
                          }}
                        />
                        <Text strong style={{ fontSize: 15 }}>
                          认知正常 (Normal Cognition)
                        </Text>
                      </Space>
                      <Text
                        strong
                        style={{ fontSize: 22, color: '#52c41a' }}
                      >
                        {(result.nc_probability * 100).toFixed(1)}%
                      </Text>
                    </div>
                    <Progress
                      percent={Math.round(result.nc_probability * 100)}
                      strokeColor="#52c41a"
                      trailColor="#f0f0f0"
                      strokeWidth={16}
                      showInfo={false}
                      style={{ borderRadius: 8 }}
                    />
                  </div>

                  {/* MCI */}
                  <div style={{ marginBottom: 28 }}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginBottom: 10,
                      }}
                    >
                      <Space>
                        <div
                          style={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            background: '#faad14',
                          }}
                        />
                        <Text strong style={{ fontSize: 15 }}>
                          轻度认知障碍 (MCI)
                        </Text>
                      </Space>
                      <Text
                        strong
                        style={{ fontSize: 22, color: '#faad14' }}
                      >
                        {(result.mci_probability * 100).toFixed(1)}%
                      </Text>
                    </div>
                    <Progress
                      percent={Math.round(result.mci_probability * 100)}
                      strokeColor="#faad14"
                      trailColor="#f0f0f0"
                      strokeWidth={16}
                      showInfo={false}
                    />
                  </div>

                  {/* AD */}
                  <div>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginBottom: 10,
                      }}
                    >
                      <Space>
                        <div
                          style={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            background: '#ff4d4f',
                          }}
                        />
                        <Text strong style={{ fontSize: 15 }}>
                          阿尔茨海默病 (AD)
                        </Text>
                      </Space>
                      <Text
                        strong
                        style={{ fontSize: 22, color: '#ff4d4f' }}
                      >
                        {(result.ad_probability * 100).toFixed(1)}%
                      </Text>
                    </div>
                    <Progress
                      percent={Math.round(result.ad_probability * 100)}
                      strokeColor="#ff4d4f"
                      trailColor="#f0f0f0"
                      strokeWidth={16}
                      showInfo={false}
                    />
                  </div>
                </div>
              </Card>
            </Col>
          </Row>

          {/* Cognitive Radar Chart */}
          <Card
            title={
              <Space>
                <span
                  style={{
                    width: 4,
                    height: 18,
                    background: '#1677ff',
                    display: 'inline-block',
                    borderRadius: 2,
                  }}
                />
                <Text strong style={{ fontSize: 16 }}>
                  认知维度雷达图
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  多维度认知功能可视化分析
                </Text>
              </Space>
            }
            style={{
              borderRadius: 12,
              border: 'none',
              boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
              marginBottom: 20,
            }}
          >
            <Row gutter={[24, 24]} align="middle">
              <Col xs={24} lg={14}>
                <CognitiveRadar domainScores={result.domain_scores} height={400} />
              </Col>
              <Col xs={24} lg={10}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong style={{ fontSize: 14 }}>各维度评分详情</Text>
                  <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 2 }}>
                    满分 10 分，绿色参考线为正常范围(≥8)
                  </Text>
                </div>
                <Table
                  dataSource={domainTableData}
                  rowKey="key"
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: '维度',
                      dataIndex: 'label',
                      key: 'label',
                      width: 90,
                      render: (text, record) => (
                        <div>
                          <Text strong style={{ fontSize: 13 }}>{text}</Text>
                          <div style={{ fontSize: 11, color: '#aaa' }}>{record.desc}</div>
                        </div>
                      ),
                    },
                    {
                      title: '评分',
                      dataIndex: 'score',
                      key: 'score',
                      width: 120,
                      render: (score: number) => (
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                            <Text strong style={{ color: getScoreColor(score), fontSize: 14 }}>
                              {score.toFixed(1)}
                            </Text>
                            <Tag
                              color={score >= 8 ? 'success' : score >= 5 ? 'warning' : 'error'}
                              style={{ borderRadius: 8, fontSize: 11, padding: '0 6px' }}
                            >
                              {getScoreLabel(score)}
                            </Tag>
                          </div>
                          <Progress
                            percent={score * 10}
                            status={getScoreStatus(score)}
                            showInfo={false}
                            size="small"
                            strokeColor={getScoreColor(score)}
                          />
                        </div>
                      ),
                    },
                  ]}
                  style={{ borderRadius: 8 }}
                />
              </Col>
            </Row>
          </Card>

          {/* Recommendation */}
          <Card
            title={
              <Space>
                <BulbOutlined style={{ color: '#faad14', fontSize: 18 }} />
                <Text strong style={{ fontSize: 16 }}>
                  干预建议
                </Text>
              </Space>
            }
            style={{
              borderRadius: 12,
              border: 'none',
              boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
            }}
            headStyle={{ borderBottom: '1px solid #f0f0f0' }}
          >
            <div
              style={{
                background: 'linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%)',
                borderRadius: 10,
                padding: '20px 24px',
                borderLeft: '4px solid #1677ff',
              }}
            >
              {result.recommendation.split('\n').map((line, idx) =>
                line.trim() ? (
                  <Paragraph
                    key={idx}
                    style={{
                      margin: idx === 0 ? '0 0 8px' : '4px 0',
                      lineHeight: 1.8,
                      fontSize: 14,
                      color: '#1a1a2e',
                    }}
                  >
                    {line}
                  </Paragraph>
                ) : null
              )}
            </div>
            <div
              style={{
                marginTop: 16,
                padding: '12px 16px',
                background: '#fffbe6',
                borderRadius: 8,
                border: '1px solid #ffe58f',
              }}
            >
              <Text style={{ fontSize: 13, color: '#876800' }}>
                <strong>注意：</strong>
                本系统评估结果仅供参考，不作为医学诊断依据。如有疑虑，请务必前往正规医疗机构就诊，由专业医生进行综合评估。
              </Text>
            </div>
          </Card>
        </>
      ) : (
        <Card
          style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
        >
          <Alert
            type="info"
            message="暂无评估结果"
            description="该评估尚未完成或结果正在处理中，请稍后查看。"
            showIcon
          />
        </Card>
      )}
    </div>
  )
}
