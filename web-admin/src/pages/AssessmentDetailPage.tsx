import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import { ArrowLeftOutlined, BarChartOutlined, BulbOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'

import { getSessionDetail } from '../services/api'
import type { AssessmentResult, AssessmentSession, DomainScores } from '../types'
import RiskBadge from '../components/RiskBadge'
import CognitiveRadar from '../components/CognitiveRadar'

const { Title, Text, Paragraph } = Typography

type SessionDetail = AssessmentSession & { result?: AssessmentResult; user_name?: string }

const MMSE_SUBITEMS: Array<{ key: string; label: string; max: number }> = [
  { key: 'orientation_time', label: '定向力（时间）', max: 5 },
  { key: 'orientation_place', label: '定向力（地点）', max: 5 },
  { key: 'registration', label: '即刻记忆', max: 3 },
  { key: 'attention_calculation', label: '注意/计算', max: 5 },
  { key: 'delayed_recall', label: '延迟回忆', max: 3 },
  { key: 'naming', label: '命名', max: 2 },
  { key: 'repetition', label: '复述', max: 1 },
  { key: 'three_step_command', label: '三步指令', max: 3 },
  { key: 'reading', label: '阅读理解', max: 1 },
  { key: 'writing', label: '书写', max: 1 },
  { key: 'figure_copy', label: '图形复制', max: 1 },
]

const MOCA_SUBITEMS: Array<{ key: string; label: string; max: number }> = [
  { key: 'trail_making', label: '交替连线', max: 1 },
  { key: 'visuospatial', label: '视空间', max: 4 },
  { key: 'naming', label: '命名', max: 3 },
  { key: 'attention', label: '注意力', max: 6 },
  { key: 'language', label: '语言', max: 3 },
  { key: 'abstraction', label: '抽象', max: 2 },
  { key: 'delayed_recall', label: '记忆（延迟回忆）', max: 5 },
  { key: 'orientation', label: '定向力', max: 6 },
]

const DOMAIN_LABELS: Array<{ key: keyof DomainScores; label: string; desc: string }> = [
  { key: 'memory', label: '记忆力', desc: '短时记忆与回忆能力' },
  { key: 'orientation', label: '定向力', desc: '时间、地点、人物定向' },
  { key: 'language', label: '语言能力', desc: '理解、表达与命名' },
  { key: 'attention', label: '注意力', desc: '持续注意与信息加工' },
  { key: 'visuospatial', label: '视空间', desc: '空间识别与构图能力' },
  { key: 'executive', label: '执行功能', desc: '计划、切换与组织能力' },
]

function toFixedSafe(value: number | undefined, digits = 1): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--'
  return value.toFixed(digits)
}

function buildDomainScores(result?: AssessmentResult): DomainScores {
  const fallback: DomainScores = {
    memory: 0,
    orientation: 0,
    language: 0,
    attention: 0,
    visuospatial: 0,
    executive: 0,
  }
  if (!result?.domain_scores) return fallback
  return {
    memory: Number(result.domain_scores.memory ?? 0),
    orientation: Number(result.domain_scores.orientation ?? 0),
    language: Number(result.domain_scores.language ?? 0),
    attention: Number(result.domain_scores.attention ?? 0),
    visuospatial: Number(result.domain_scores.visuospatial ?? 0),
    executive: Number(result.domain_scores.executive ?? 0),
  }
}

function mmseBand(score: number): string {
  if (score >= 24) return '正常范围（>=24）'
  if (score >= 18) return '轻中度下降（18-23）'
  return '明显受损（<18）'
}

function mocaBand(score: number): string {
  if (score >= 26) return '正常范围（>=26）'
  if (score >= 18) return '可疑下降（18-25）'
  return '中高风险（<18）'
}

const statusConfig: Record<string, { text: string; color: string }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '已暂停', color: 'warning' },
  failed: { text: '失败', color: 'error' },
}

export default function AssessmentDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [session, setSession] = useState<SessionDetail | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!sessionId) return
      setLoading(true)
      setError(null)
      try {
        const data = await getSessionDetail(Number(sessionId))
        setSession(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : '获取评估详情失败')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [sessionId])

  const result = session?.result
  const domainScores = useMemo(() => buildDomainScores(result), [result])
  const statusInfo = statusConfig[session?.status ?? ''] || { text: session?.status ?? '-', color: 'default' }

  const durationMinutes =
    session?.started_at && session?.completed_at
      ? dayjs(session.completed_at).diff(dayjs(session.started_at), 'minute')
      : null

  const mmseRows = MMSE_SUBITEMS.map((item) => {
    const score = Number(result?.mmse_subscores?.[item.key] ?? 0)
    return { ...item, score }
  })
  const mocaRows = MOCA_SUBITEMS.map((item) => {
    const score = Number(result?.moca_subscores?.[item.key] ?? 0)
    return { ...item, score }
  })

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '120px 0' }}>
        <Spin size="large" tip="正在加载评估报告..." />
      </div>
    )
  }

  if (!session) {
    return (
      <Alert
        type="error"
        message="未找到评估记录"
        description={error || '请返回列表重试'}
        action={
          <Button type="primary" onClick={() => navigate('/assessments')}>
            返回列表
          </Button>
        }
      />
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
          返回
        </Button>
        <div>
          <Title level={4} style={{ margin: 0 }}>
            评估详情
          </Title>
          <Text type="secondary">
            会话 #{String(session.id).padStart(4, '0')} · 创建于 {dayjs(session.created_at).format('YYYY-MM-DD HH:mm')}
          </Text>
        </div>
      </div>

      {error && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="接口返回异常"
          description={error}
        />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col span={20}>
            <Descriptions size="small" column={{ xs: 1, md: 2, xl: 4 }}>
              <Descriptions.Item label="评估对象">
                <Space>
                  <UserOutlined />
                  <Text strong>{session.user_name || `用户 #${session.user_id}`}</Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {session.started_at ? dayjs(session.started_at).format('YYYY-MM-DD HH:mm') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {session.completed_at ? dayjs(session.completed_at).format('YYYY-MM-DD HH:mm') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="耗时">{durationMinutes !== null ? `${durationMinutes} 分钟` : '-'}</Descriptions.Item>
            </Descriptions>
          </Col>
          <Col span={4} style={{ textAlign: 'right' }}>
            <Tag color={statusInfo.color} style={{ fontSize: 14 }}>
              {statusInfo.text}
            </Tag>
          </Col>
        </Row>
      </Card>

      {!result && (
        <Card>
          <Alert
            type="info"
            showIcon
            message="结果尚未生成"
            description="该评估尚未完成分析，请稍后刷新页面。"
          />
        </Card>
      )}

      {result && (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} lg={8}>
              <Card>
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">综合风险评级</Text>
                    <div style={{ marginTop: 10 }}>
                      <RiskBadge riskLevel={result.risk_level} size="large" />
                    </div>
                  </div>
                  <Divider style={{ margin: 0 }} />
                  <Statistic title="MMSE 总分" value={result.mmse_score} suffix="/ 30" />
                  <Progress percent={Math.round((Number(result.mmse_score || 0) / 30) * 100)} showInfo={false} />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {mmseBand(Number(result.mmse_score || 0))}
                  </Text>
                  <Statistic
                    title="MoCA（校正后）"
                    value={result.moca_score_corrected ?? result.moca_score ?? 0}
                    suffix="/ 30"
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {mocaBand(Number(result.moca_score_corrected ?? result.moca_score ?? 0))}
                  </Text>
                </Space>
              </Card>
            </Col>
            <Col xs={24} lg={16}>
              <Card
                title={
                  <Space>
                    <BarChartOutlined />
                    <Text strong>风险概率分布</Text>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size={18}>
                  <div>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text>认知正常（NC）</Text>
                      <Text strong>{(result.nc_probability * 100).toFixed(1)}%</Text>
                    </Space>
                    <Progress percent={Math.round(result.nc_probability * 100)} strokeColor="#52c41a" showInfo={false} />
                  </div>
                  <div>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text>轻度认知障碍（MCI）</Text>
                      <Text strong>{(result.mci_probability * 100).toFixed(1)}%</Text>
                    </Space>
                    <Progress percent={Math.round(result.mci_probability * 100)} strokeColor="#faad14" showInfo={false} />
                  </div>
                  <div>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text>阿尔茨海默病风险（AD）</Text>
                      <Text strong>{(result.ad_probability * 100).toFixed(1)}%</Text>
                    </Space>
                    <Progress percent={Math.round(result.ad_probability * 100)} strokeColor="#ff4d4f" showInfo={false} />
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>

          <Card title="医生版标准报告（E-03）" style={{ marginBottom: 16 }}>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Alert type="info" showIcon message={result.clinical_report?.risk_summary || '本报告基于多模态筛查结果生成，供医生参考。'} />
              <Row gutter={[16, 16]}>
                <Col xs={24} md={8}>
                  <Card size="small">
                    <Statistic title="MMSE 总分" value={result.mmse_score} suffix="/30" />
                    <Text type="secondary">{result.clinical_report?.scale_interpretation?.mmse || mmseBand(Number(result.mmse_score || 0))}</Text>
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small">
                    <Statistic title="MoCA 原始分" value={result.moca_score ?? 0} suffix="/30" />
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small">
                    <Statistic title="MoCA 校正后" value={result.moca_score_corrected ?? result.moca_score ?? 0} suffix="/30" />
                    {result.education_correction_applied ? (
                      <Tag color="blue" style={{ marginTop: 8 }}>
                        已应用教育校正 +{result.education_correction_points ?? 1}
                      </Tag>
                    ) : (
                      <Tag style={{ marginTop: 8 }}>未触发教育校正</Tag>
                    )}
                  </Card>
                </Col>
              </Row>

              <Row gutter={[16, 16]}>
                <Col xs={24} xl={12}>
                  <Table
                    size="small"
                    pagination={false}
                    rowKey="key"
                    dataSource={mmseRows}
                    columns={[
                      { title: 'MMSE 子项（11项）', dataIndex: 'label', key: 'label' },
                      {
                        title: '得分',
                        key: 'score',
                        align: 'right',
                        render: (_, row) => `${toFixedSafe(row.score, 1)} / ${row.max}`,
                      },
                    ]}
                  />
                </Col>
                <Col xs={24} xl={12}>
                  <Table
                    size="small"
                    pagination={false}
                    rowKey="key"
                    dataSource={mocaRows}
                    columns={[
                      { title: 'MoCA 子项（8项）', dataIndex: 'label', key: 'label' },
                      {
                        title: '得分',
                        key: 'score',
                        align: 'right',
                        render: (_, row) => `${toFixedSafe(row.score, 1)} / ${row.max}`,
                      },
                    ]}
                  />
                </Col>
              </Row>

              {(result.clinical_report?.clinical_note || result.clinical_report?.weak_domains?.length) && (
                <Card size="small" title="临床摘要">
                  {result.clinical_report?.clinical_note && <Paragraph style={{ marginBottom: 8 }}>{result.clinical_report.clinical_note}</Paragraph>}
                  {result.clinical_report?.weak_domains?.length ? (
                    <Space wrap>
                      {result.clinical_report.weak_domains.map((item, index) => (
                        <Tag key={`${item.domain || 'domain'}-${index}`}>
                          {(item.label || item.domain || '未知维度') + `：${toFixedSafe(item.score, 2)}`}
                        </Tag>
                      ))}
                    </Space>
                  ) : null}
                </Card>
              )}
            </Space>
          </Card>

          <Card title="六维认知域雷达图" style={{ marginBottom: 16 }}>
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} lg={14}>
                <CognitiveRadar domainScores={domainScores} height={360} />
              </Col>
              <Col xs={24} lg={10}>
                <Table
                  size="small"
                  rowKey="key"
                  pagination={false}
                  dataSource={DOMAIN_LABELS.map((d) => ({
                    key: d.key,
                    label: d.label,
                    desc: d.desc,
                    score: Number(domainScores[d.key] ?? 0),
                  }))}
                  columns={[
                    {
                      title: '认知域',
                      key: 'label',
                      render: (_, row) => (
                        <div>
                          <Text strong>{row.label}</Text>
                          <div style={{ fontSize: 12, color: '#999' }}>{row.desc}</div>
                        </div>
                      ),
                    },
                    {
                      title: '分值',
                      dataIndex: 'score',
                      key: 'score',
                      align: 'right',
                      render: (value: number) => toFixedSafe(value, 1),
                    },
                  ]}
                />
              </Col>
            </Row>
          </Card>

          <Card
            title={
              <Space>
                <BulbOutlined />
                <Text strong>建议与说明</Text>
              </Space>
            }
          >
            {(result.recommendation || '').split('\n').filter(Boolean).map((line, index) => (
              <Paragraph key={`${line}-${index}`} style={{ marginBottom: 6 }}>
                {line}
              </Paragraph>
            ))}
            <Divider />
            <Text type="secondary">
              本报告用于社区早筛和随访管理，不作为单独临床诊断依据。请结合病史、体检及专科评估综合判断。
            </Text>
          </Card>
        </>
      )}
    </div>
  )
}
