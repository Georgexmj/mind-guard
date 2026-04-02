import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Progress,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  EyeOutlined,
  ReloadOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'

import {
  createInterventionPlan,
  getElders,
  getInterventionPlans,
  getInterventionTop5Recommendations,
  updateInterventionPlan,
} from '../services/api'
import type {
  InterventionRecommendationItem,
  InterventionTop5Recommendation,
  User,
} from '../types'
import { useAuthStore } from '../store/auth'

const { Title, Text } = Typography
const { TextArea } = Input

interface InterventionPlan {
  id: number
  elder_id: number
  elder_name?: string
  created_by: number
  title: string
  description?: string
  domain_focus?: string
  frequency?: string
  duration_days?: number
  start_date?: string
  end_date?: string
  status: 'active' | 'paused' | 'completed' | 'cancelled'
  ai_priority?: number
  completed_count?: number
  total_records?: number
  created_at: string
}

const statusConfig: Record<string, { text: string; color: string }> = {
  active: { text: '进行中', color: 'processing' },
  paused: { text: '已暂停', color: 'warning' },
  completed: { text: '已完成', color: 'success' },
  cancelled: { text: '已取消', color: 'default' },
}

const DOMAIN_OPTIONS = [
  { label: '记忆力', value: 'memory' },
  { label: '定向力', value: 'orientation' },
  { label: '注意力', value: 'attention' },
  { label: '语言能力', value: 'language' },
  { label: '视空间', value: 'visuospatial' },
  { label: '执行功能', value: 'executive' },
]

const DOMAIN_LABELS: Record<string, string> = {
  memory: '记忆力',
  orientation: '定向力',
  attention: '注意力',
  language: '语言能力',
  visuospatial: '视空间',
  executive: '执行功能',
}

const FREQUENCY_OPTIONS = [
  { label: '每天1次', value: '每天1次' },
  { label: '每天2次', value: '每天2次' },
  { label: '每周3次', value: '每周3次' },
  { label: '每周5次', value: '每周5次' },
  { label: '隔天1次', value: '隔天1次' },
]

function domainTags(domains?: string): string[] {
  if (!domains) return []
  return domains
    .split(',')
    .map((d) => d.trim())
    .filter(Boolean)
}

export default function InterventionsPage() {
  const user = useAuthStore((state) => state.user)
  const canManagePlans = user?.role === 'admin' || user?.role === 'doctor'

  const [plans, setPlans] = useState<InterventionPlan[]>([])
  const [elders, setElders] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [modalOpen, setModalOpen] = useState(false)
  const [editingPlan, setEditingPlan] = useState<InterventionPlan | null>(null)
  const [recommendation, setRecommendation] = useState<InterventionTop5Recommendation | null>(null)
  const [recLoading, setRecLoading] = useState(false)
  const [recError, setRecError] = useState<string | null>(null)

  const [form] = Form.useForm()
  const navigate = useNavigate()

  const fetchPlans = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getInterventionPlans({ status: statusFilter })
      setPlans(Array.isArray(res) ? (res as InterventionPlan[]) : [])
    } catch {
      setPlans([])
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  const fetchElders = useCallback(async () => {
    try {
      const res = await getElders()
      setElders(Array.isArray(res) ? res : [])
    } catch {
      setElders([])
    }
  }, [])

  const fetchTop5 = useCallback(async () => {
    setRecLoading(true)
    setRecError(null)
    try {
      const res = await getInterventionTop5Recommendations()
      setRecommendation(res)
    } catch (error) {
      setRecommendation(null)
      setRecError(error instanceof Error ? error.message : '暂无可用推荐')
    } finally {
      setRecLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPlans()
  }, [fetchPlans])

  useEffect(() => {
    fetchElders()
    fetchTop5()
  }, [fetchElders, fetchTop5])

  const completionRate = (plan: InterventionPlan): number => {
    if (!plan.total_records) return 0
    return Math.round(((plan.completed_count || 0) / plan.total_records) * 100)
  }

  const openCreate = () => {
    setEditingPlan(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openCreateFromRecommendation = (item: InterventionRecommendationItem) => {
    setEditingPlan(null)
    form.resetFields()
    form.setFieldsValue({
      title: `AI推荐：${item.title}`,
      description: item.rationale,
      domain_focus: item.target_domains,
      frequency: item.frequency,
      duration_days: 30,
    })
    setModalOpen(true)
  }

  const openEdit = (plan: InterventionPlan) => {
    setEditingPlan(plan)
    form.setFieldsValue({
      ...plan,
      start_date: plan.start_date ? dayjs(plan.start_date) : undefined,
      end_date: plan.end_date ? dayjs(plan.end_date) : undefined,
      domain_focus: domainTags(plan.domain_focus),
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const payload = {
        ...values,
        domain_focus: values.domain_focus?.join(','),
        start_date: values.start_date?.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
      }
      if (editingPlan) {
        await updateInterventionPlan(editingPlan.id, payload)
      } else {
        await createInterventionPlan(payload)
      }
      setModalOpen(false)
      fetchPlans()
    } catch {
      // form/API errors handled by antd
    }
  }

  const activeCount = useMemo(() => plans.filter((p) => p.status === 'active').length, [plans])
  const avgCompletion = useMemo(
    () => (plans.length ? Math.round(plans.reduce((sum, p) => sum + completionRate(p), 0) / plans.length) : 0),
    [plans]
  )

  const columns: ColumnsType<InterventionPlan> = [
    {
      title: '干预计划',
      key: 'plan',
      width: 230,
      render: (_, row) => (
        <div>
          <div style={{ fontWeight: 600, color: '#1a1a2e', marginBottom: 2 }}>{row.title}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {row.elder_name || `老人 #${row.elder_id}`}
          </Text>
        </div>
      ),
    },
    {
      title: '认知域',
      dataIndex: 'domain_focus',
      key: 'domain_focus',
      width: 220,
      render: (domains: string) =>
        domainTags(domains).length ? (
          domainTags(domains).map((d) => (
            <Tag key={d} color="blue" style={{ borderRadius: 10, marginBottom: 2 }}>
              {DOMAIN_LABELS[d] || d}
            </Tag>
          ))
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: '频次',
      dataIndex: 'frequency',
      key: 'frequency',
      width: 110,
      render: (value) => value || '-',
    },
    {
      title: '完成率',
      key: 'completion',
      width: 150,
      render: (_, row) => (
        <div>
          <Progress
            percent={completionRate(row)}
            size="small"
            strokeColor={
              completionRate(row) >= 80
                ? '#52c41a'
                : completionRate(row) >= 50
                  ? '#faad14'
                  : '#ff4d4f'
            }
            style={{ marginBottom: 2 }}
          />
          <Text style={{ fontSize: 11, color: '#999' }}>
            {row.completed_count || 0}/{row.total_records || 0} 次
          </Text>
        </div>
      ),
    },
    {
      title: '起止日期',
      key: 'dates',
      width: 170,
      render: (_, row) => (
        <Text style={{ fontSize: 12 }}>
          {row.start_date ? dayjs(row.start_date).format('MM/DD') : '-'}
          {' ~ '}
          {row.end_date ? dayjs(row.end_date).format('MM/DD') : '-'}
        </Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      align: 'center',
      render: (value: string) => {
        const cfg = statusConfig[value] || { text: value, color: 'default' }
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
      width: 120,
      align: 'center',
      fixed: 'right',
      render: (_, row) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/elders/${row.elder_id}`)}
              style={{ padding: 0 }}
            />
          </Tooltip>
          {canManagePlans && (
            <Tooltip title="编辑计划">
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => openEdit(row)}
                style={{ padding: 0 }}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>
          干预管理
        </Title>
        <Text type="secondary">
          干预推荐 Top-5 已接入评估结果自动生成，可用于医生快速创建计划。
        </Text>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="总计划数" value={plans.length} suffix="项" valueStyle={{ color: '#1677ff' }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="进行中" value={activeCount} suffix="项" valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="平均完成率" value={avgCompletion} suffix="%" valueStyle={{ color: '#fa8c16' }} />
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <Space>
            <BulbOutlined style={{ color: '#faad14' }} />
            <Text strong>干预推荐 Top-5（基于最新评估）</Text>
          </Space>
        }
        extra={<Button icon={<ReloadOutlined />} onClick={fetchTop5}>刷新推荐</Button>}
        style={{ borderRadius: 12, marginBottom: 20 }}
      >
        {recError && <Alert type="warning" showIcon style={{ marginBottom: 12 }} message={recError} />}
        {recommendation && (
          <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
            会话 #{recommendation.session_id} · 风险等级 {recommendation.risk_level} · MMSE {recommendation.mmse_score ?? '-'}
          </Text>
        )}
        <Table
          rowKey="code"
          loading={recLoading}
          pagination={false}
          size="small"
          dataSource={recommendation?.recommendations || []}
          locale={{ emptyText: recLoading ? '加载中...' : '暂无推荐数据' }}
          columns={[
            { title: '排名', dataIndex: 'rank', key: 'rank', width: 60, align: 'center' },
            { title: '推荐项', dataIndex: 'title', key: 'title', width: 220 },
            {
              title: '目标认知域',
              key: 'target_domains',
              render: (_, row: InterventionRecommendationItem) => (
                <>
                  {row.target_domains.map((domain) => (
                    <Tag key={domain} color="blue">
                      {DOMAIN_LABELS[domain] || domain}
                    </Tag>
                  ))}
                </>
              ),
            },
            { title: '频次', dataIndex: 'frequency', key: 'frequency', width: 100 },
            { title: '时长', dataIndex: 'duration_minutes', key: 'duration_minutes', width: 90, render: (v) => `${v} 分钟` },
            { title: '优先级', dataIndex: 'priority_score', key: 'priority_score', width: 90 },
            {
              title: '操作',
              key: 'actions',
              width: 130,
              render: (_, row: InterventionRecommendationItem) =>
                canManagePlans ? (
                  <Button type="link" size="small" onClick={() => openCreateFromRecommendation(row)}>
                    用于建计划
                  </Button>
                ) : (
                  <Text type="secondary">-</Text>
                ),
            },
          ]}
        />
      </Card>

      <Card style={{ borderRadius: 12 }}>
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col flex="auto">
            <Select
              placeholder="筛选状态"
              allowClear
              style={{ width: 140 }}
              value={statusFilter}
              onChange={setStatusFilter}
              options={Object.entries(statusConfig).map(([value, cfg]) => ({ label: cfg.text, value }))}
            />
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchPlans}>刷新</Button>
              {canManagePlans && (
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建计划</Button>
              )}
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={plans}
          rowKey="id"
          loading={loading}
          scroll={{ x: 980 }}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 项` }}
        />
      </Card>

      {canManagePlans && (
        <Modal
          title={editingPlan ? '编辑干预计划' : '新建干预计划'}
          open={modalOpen}
          onOk={handleSubmit}
          onCancel={() => setModalOpen(false)}
          okText={editingPlan ? '保存' : '创建'}
          cancelText="取消"
          width={640}
          destroyOnClose
        >
          <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
            {!editingPlan && (
              <Form.Item
                name="elder_id"
                label="服务老人"
                rules={[{ required: true, message: '请选择服务对象' }]}
              >
                <Select
                  placeholder="选择老人"
                  showSearch
                  optionFilterProp="label"
                  options={elders.map((elder) => ({ label: elder.name, value: elder.id }))}
                />
              </Form.Item>
            )}

            <Form.Item
              name="title"
              label="计划标题"
              rules={[{ required: true, message: '请输入标题' }]}
            >
              <Input placeholder="如：记忆力强化训练计划" />
            </Form.Item>

            <Form.Item name="description" label="计划描述">
              <TextArea rows={3} placeholder="描述干预内容、目标和注意事项..." />
            </Form.Item>

            <Form.Item name="domain_focus" label="目标认知域">
              <Select mode="multiple" options={DOMAIN_OPTIONS} placeholder="选择一个或多个认知域" />
            </Form.Item>

            <Row gutter={12}>
              <Col span={12}>
                <Form.Item name="frequency" label="训练频次">
                  <Select options={FREQUENCY_OPTIONS} placeholder="选择频次" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="duration_days" label="计划天数">
                  <InputNumber min={1} max={365} style={{ width: '100%' }} addonAfter="天" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={12}>
              <Col span={12}>
                <Form.Item name="start_date" label="开始日期">
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="end_date" label="结束日期">
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            {editingPlan && (
              <Form.Item name="status" label="计划状态">
                <Select options={Object.entries(statusConfig).map(([value, cfg]) => ({ label: cfg.text, value }))} />
              </Form.Item>
            )}
          </Form>
        </Modal>
      )}
    </div>
  )
}
