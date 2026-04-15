import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Modal,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { ArrowLeftOutlined, DownloadOutlined, FileTextOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'

import { downloadDoctorReportPdf, getFamilyReadableReport, getSessionDetail } from '../services/api'
import type { AssessmentResult, AssessmentSession, DomainScores } from '../types'
import RiskBadge from '../components/RiskBadge'
import CognitiveRadar from '../components/CognitiveRadar'
import { useAuthStore } from '../store/auth'

const { Title, Text, Paragraph } = Typography

type SessionDetail = AssessmentSession & {
  result?: AssessmentResult
  user_name?: string
}

type FamilyReportData = {
  summary: string
  plain_interpretation: string
  next_reassessment_date?: string
  risk_change?: string
  daily_tips: string[]
  warning_signs: string[]
}

const statusConfig: Record<string, { text: string; color: string }> = {
  completed: { text: '已完成', color: 'success' },
  in_progress: { text: '进行中', color: 'processing' },
  pending: { text: '待开始', color: 'default' },
  failed: { text: '失败', color: 'error' },
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
  if (score >= 24) return '参考：正常范围（>=24）'
  if (score >= 18) return '参考：轻中度下降（18-23）'
  return '参考：明显受损（<18）'
}

function mocaBand(score: number): string {
  if (score >= 26) return '参考：正常范围（>=26）'
  if (score >= 18) return '参考：可疑下降（18-25）'
  return '参考：中高风险（<18）'
}

export default function AssessmentDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [session, setSession] = useState<SessionDetail | null>(null)

  const [familyReportOpen, setFamilyReportOpen] = useState(false)
  const [familyReportLoading, setFamilyReportLoading] = useState(false)
  const [familyReport, setFamilyReport] = useState<FamilyReportData | null>(null)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

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

    void fetchData()
  }, [sessionId])

  const result = session?.result
  const domainScores = useMemo(() => buildDomainScores(result), [result])
  const canExportDoctorPdf = user?.role === 'admin' || user?.role === 'doctor'
  const statusInfo = statusConfig[session?.status ?? ''] || { text: session?.status ?? '-', color: 'default' }

  const durationMinutes =
    session?.started_at && session?.completed_at
      ? dayjs(session.completed_at).diff(dayjs(session.started_at), 'minute')
      : null

  const handleDownloadDoctorPdf = async () => {
    if (!sessionId) return
    try {
      setDownloadingPdf(true)
      const blob = await downloadDoctorReportPdf(Number(sessionId))
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `mindguard_doctor_report_session_${sessionId}.pdf`
      anchor.click()
      URL.revokeObjectURL(url)
      message.success('医生报告 PDF 已下载')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '下载医生报告失败')
    } finally {
      setDownloadingPdf(false)
    }
  }

  const handleOpenFamilyReport = async () => {
    if (!sessionId) return
    try {
      setFamilyReportLoading(true)
      const payload = await getFamilyReadableReport(Number(sessionId))
      setFamilyReport(payload as FamilyReportData)
      setFamilyReportOpen(true)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '获取家属报告失败')
    } finally {
      setFamilyReportLoading(false)
    }
  }

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
        description={error || '请返回列表后重试'}
        action={
          <Button type="primary" onClick={() => navigate('/assessments')}>
            返回列表
          </Button>
        }
      />
    )
  }

  return (
    <div className="mg-page">
      <div className="mg-page-header" style={{ alignItems: 'center' }}>
        <Space wrap>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
            返回
          </Button>
          {canExportDoctorPdf && (
            <Button icon={<DownloadOutlined />} loading={downloadingPdf} onClick={() => void handleDownloadDoctorPdf()}>
              导出医生 PDF
            </Button>
          )}
          <Button icon={<FileTextOutlined />} loading={familyReportLoading} onClick={() => void handleOpenFamilyReport()}>
            家属可读版
          </Button>
        </Space>
        <div>
          <Title level={4} className="mg-page-title">
            评估详情
          </Title>
          <Text className="mg-page-subtitle">
            会话 #{String(session.id).padStart(4, '0')} · 创建于 {dayjs(session.created_at).format('YYYY-MM-DD HH:mm')}
          </Text>
        </div>
      </div>

      {error && <Alert type="warning" showIcon message={error} />}

      <Card className="mg-panel-card">
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
              <Descriptions.Item label="评估时长">
                {durationMinutes !== null ? `${durationMinutes} 分钟` : '-'}
              </Descriptions.Item>
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
        <Card className="mg-panel-card">
          <Alert
            type="info"
            showIcon
            message="结果尚未生成"
            description="该评估尚未完成分析，请稍后刷新查看。"
          />
        </Card>
      )}

      {result && (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={8}>
              <Card className="mg-panel-card">
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">综合风险评级</Text>
                    <div style={{ marginTop: 8 }}>
                      <RiskBadge riskLevel={result.risk_level} size="large" />
                    </div>
                  </div>

                  <Divider style={{ margin: 0 }} />

                  <Statistic title="MMSE 总分" value={result.mmse_score} suffix="/ 30" />
                  <Progress percent={Math.round((Number(result.mmse_score || 0) / 30) * 100)} showInfo={false} />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {mmseBand(Number(result.mmse_score || 0))}
                  </Text>

                  <Statistic title="MoCA（校正后）" value={result.moca_score_corrected ?? result.moca_score ?? 0} suffix="/ 30" />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {mocaBand(Number(result.moca_score_corrected ?? result.moca_score ?? 0))}
                  </Text>
                </Space>
              </Card>
            </Col>

            <Col xs={24} lg={16}>
              <Card className="mg-panel-card" title="风险概率分布">
                <Space direction="vertical" style={{ width: '100%' }} size={16}>
                  <div>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text>认知正常（NC）</Text>
                      <Text strong>{(result.nc_probability * 100).toFixed(1)}%</Text>
                    </Space>
                    <Progress percent={Math.round(result.nc_probability * 100)} strokeColor="#16a34a" showInfo={false} />
                  </div>
                  <div>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text>轻度认知障碍（MCI）</Text>
                      <Text strong>{(result.mci_probability * 100).toFixed(1)}%</Text>
                    </Space>
                    <Progress percent={Math.round(result.mci_probability * 100)} strokeColor="#d97706" showInfo={false} />
                  </div>
                  <div>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text>阿尔茨海默病风险（AD）</Text>
                      <Text strong>{(result.ad_probability * 100).toFixed(1)}%</Text>
                    </Space>
                    <Progress percent={Math.round(result.ad_probability * 100)} strokeColor="#dc2626" showInfo={false} />
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>

          <Card className="mg-panel-card" title="认知域雷达图">
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} lg={14}>
                <CognitiveRadar domainScores={domainScores} height={360} />
              </Col>
              <Col xs={24} lg={10}>
                <Table
                  size="small"
                  pagination={false}
                  rowKey="key"
                  dataSource={[
                    { key: 'memory', label: '记忆力', score: domainScores.memory },
                    { key: 'orientation', label: '定向力', score: domainScores.orientation },
                    { key: 'language', label: '语言能力', score: domainScores.language },
                    { key: 'attention', label: '注意力', score: domainScores.attention },
                    { key: 'visuospatial', label: '视空间', score: domainScores.visuospatial },
                    { key: 'executive', label: '执行功能', score: domainScores.executive },
                  ]}
                  columns={[
                    { title: '认知域', dataIndex: 'label', key: 'label' },
                    { title: '得分', dataIndex: 'score', key: 'score', align: 'right' },
                  ]}
                />
              </Col>
            </Row>
          </Card>

          <Card className="mg-panel-card" title="建议与说明">
            {(result.recommendation || '')
              .split('\n')
              .filter(Boolean)
              .map((line, index) => (
                <Paragraph key={`${line}-${index}`} style={{ marginBottom: 6 }}>
                  {line}
                </Paragraph>
              ))}
            <Divider />
            <Text type="secondary">
              本报告用于社区早筛与随访管理，不作为单独临床诊断依据。请结合病史、体检与专科评估综合判断。
            </Text>
          </Card>
        </>
      )}

      <Modal
        title="家属可读版报告"
        open={familyReportOpen}
        onCancel={() => setFamilyReportOpen(false)}
        footer={null}
        width={720}
      >
        {!familyReport ? (
          <Spin />
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size={12}>
            <Alert type="info" showIcon message={familyReport.summary} />
            <Paragraph>{familyReport.plain_interpretation}</Paragraph>
            <Text strong>风险变化：{familyReport.risk_change || 'unknown'}</Text>
            <Text strong>建议下次复评：{familyReport.next_reassessment_date || '-'}</Text>
            <Divider />
            <Text strong>日常建议</Text>
            {familyReport.daily_tips.map((item, index) => (
              <Paragraph key={`tip-${index}`} style={{ marginBottom: 4 }}>
                {index + 1}. {item}
              </Paragraph>
            ))}
            <Divider />
            <Text strong>出现以下信号请及时就医</Text>
            {familyReport.warning_signs.map((item, index) => (
              <Paragraph key={`warn-${index}`} style={{ marginBottom: 4 }}>
                {index + 1}. {item}
              </Paragraph>
            ))}
          </Space>
        )}
      </Modal>
    </div>
  )
}
