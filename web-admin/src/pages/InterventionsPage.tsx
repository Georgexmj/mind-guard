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
  Typography,
  message,
} from 'antd'
import {
  BulbOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SendOutlined,
  SyncOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs, { type Dayjs } from 'dayjs'
import { useSearchParams } from 'react-router-dom'

import {
  createInterventionPlan,
  createInterventionPlanFromTop5,
  dispatchAdherenceReminders,
  getAdherenceTickets,
  getDoctors,
  getElders,
  getInterventionAdherenceAlerts,
  getInterventionPlans,
  getInterventionTop5Recommendations,
  syncAdherenceTickets,
  updateAdherenceTicket,
  updateInterventionPlan,
} from '../services/api'
import type {
  AdherenceTicket,
  InterventionAdherenceAlert,
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

const planStatusMap: Record<InterventionPlan['status'], { text: string; color: string }> = {
  active: { text: '进行中', color: 'processing' },
  paused: { text: '已暂停', color: 'warning' },
  completed: { text: '已完成', color: 'success' },
  cancelled: { text: '已取消', color: 'default' },
}

const ticketStatusMap: Record<AdherenceTicket['status'], { text: string; color: string }> = {
  open: { text: '待处理', color: 'error' },
  in_progress: { text: '处理中', color: 'processing' },
  resolved: { text: '已处理', color: 'success' },
  ignored: { text: '已忽略', color: 'default' },
}

const DOMAIN_OPTIONS = [
  { label: '记忆', value: 'memory' },
  { label: '定向', value: 'orientation' },
  { label: '注意', value: 'attention' },
  { label: '语言', value: 'language' },
  { label: '视空间', value: 'visuospatial' },
  { label: '执行功能', value: 'executive' },
]

const DOMAIN_LABELS: Record<string, string> = {
  memory: '记忆',
  orientation: '定向',
  attention: '注意',
  language: '语言',
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

interface PlanFormValues {
  elder_id?: number
  title: string
  description?: string
  domain_focus?: string[]
  frequency?: string
  duration_days?: number
  start_date?: Dayjs
  end_date?: Dayjs
  status?: InterventionPlan['status']
}

interface TicketFormValues {
  status?: AdherenceTicket['status']
  owner_doctor_id?: number
  reminder_at?: Dayjs
  followup_note?: string
}

function domainTags(domains?: string): string[] {
  if (!domains) return []
  return domains
    .split(',')
    .map((d) => d.trim())
    .filter(Boolean)
}

export default function InterventionsPage() {
  const user = useAuthStore((state) => state.user)
  const canManage = user?.role === 'admin' || user?.role === 'doctor'
  const [searchParams] = useSearchParams()
  const focusedTicketId = Number(searchParams.get('ticket_id') || 0)

  const [plans, setPlans] = useState<InterventionPlan[]>([])
  const [elders, setElders] = useState<User[]>([])
  const [doctors, setDoctors] = useState<User[]>([])

  const [recommendation, setRecommendation] = useState<InterventionTop5Recommendation | null>(null)
  const [alerts, setAlerts] = useState<InterventionAdherenceAlert[]>([])
  const [tickets, setTickets] = useState<AdherenceTicket[]>([])

  const [planLoading, setPlanLoading] = useState(false)
  const [recLoading, setRecLoading] = useState(false)
  const [alertLoading, setAlertLoading] = useState(false)
  const [ticketLoading, setTicketLoading] = useState(false)

  const [planStatusFilter, setPlanStatusFilter] = useState<string | undefined>()
  const [ticketStatusFilter, setTicketStatusFilter] = useState<AdherenceTicket['status'] | undefined>()

  const [planModalOpen, setPlanModalOpen] = useState(false)
  const [editingPlan, setEditingPlan] = useState<InterventionPlan | null>(null)
  const [ticketModalOpen, setTicketModalOpen] = useState(false)
  const [editingTicket, setEditingTicket] = useState<AdherenceTicket | null>(null)

  const [creatingFromRecoCode, setCreatingFromRecoCode] = useState<string | null>(null)
  const [syncingTickets, setSyncingTickets] = useState(false)
  const [dispatchingReminder, setDispatchingReminder] = useState(false)
  const [updatingTicket, setUpdatingTicket] = useState(false)

  const [planForm] = Form.useForm<PlanFormValues>()
  const [ticketForm] = Form.useForm<TicketFormValues>()

  useEffect(() => {
    if (searchParams.get('queue') === 'low_adherence') {
      setTicketStatusFilter('open')
    }
  }, [searchParams])

  const fetchPlans = useCallback(async () => {
    setPlanLoading(true)
    try {
      const data = await getInterventionPlans({ status: planStatusFilter })
      setPlans(Array.isArray(data) ? (data as InterventionPlan[]) : [])
    } catch {
      setPlans([])
    } finally {
      setPlanLoading(false)
    }
  }, [planStatusFilter])

  const fetchUsers = useCallback(async () => {
    try {
      const [elderRows, doctorRows] = await Promise.all([
        getElders({ page: 1, page_size: 300 }),
        getDoctors({ page: 1, page_size: 300 }),
      ])
      setElders(Array.isArray(elderRows) ? elderRows : [])
      setDoctors(Array.isArray(doctorRows) ? doctorRows : [])
    } catch {
      setElders([])
      setDoctors([])
    }
  }, [])

  const fetchTop5 = useCallback(async () => {
    setRecLoading(true)
    try {
      const data = await getInterventionTop5Recommendations()
      setRecommendation(data)
    } catch {
      setRecommendation(null)
    } finally {
      setRecLoading(false)
    }
  }, [])

  const fetchAlerts = useCallback(async () => {
    if (!canManage) return
    setAlertLoading(true)
    try {
      const data = await getInterventionAdherenceAlerts({ days: 14, threshold: 2, sync_ticket: true })
      setAlerts(Array.isArray(data) ? data : [])
    } catch {
      setAlerts([])
    } finally {
      setAlertLoading(false)
    }
  }, [canManage])

  const fetchTickets = useCallback(async () => {
    if (!canManage) return
    setTicketLoading(true)
    try {
      const data = await getAdherenceTickets({ status: ticketStatusFilter, page: 1, page_size: 100 })
      setTickets(Array.isArray(data) ? data : [])
    } catch {
      setTickets([])
    } finally {
      setTicketLoading(false)
    }
  }, [canManage, ticketStatusFilter])

  useEffect(() => {
    fetchUsers()
    fetchTop5()
  }, [fetchUsers, fetchTop5])

  useEffect(() => {
    fetchPlans()
  }, [fetchPlans])

  useEffect(() => {
    fetchAlerts()
    fetchTickets()
  }, [fetchAlerts, fetchTickets])

  const openCreatePlan = () => {
    setEditingPlan(null)
    planForm.resetFields()
    setPlanModalOpen(true)
  }

  const openEditPlan = (plan: InterventionPlan) => {
    setEditingPlan(plan)
    planForm.setFieldsValue({
      ...plan,
      domain_focus: domainTags(plan.domain_focus),
      start_date: plan.start_date ? dayjs(plan.start_date) : undefined,
      end_date: plan.end_date ? dayjs(plan.end_date) : undefined,
    })
    setPlanModalOpen(true)
  }

  const handleSavePlan = async () => {
    try {
      const values = await planForm.validateFields()
      const payload = {
        ...values,
        domain_focus: values.domain_focus?.join(','),
        start_date: values.start_date?.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
      }

      if (editingPlan) {
        await updateInterventionPlan(editingPlan.id, payload)
        message.success('干预计划已更新')
      } else {
        await createInterventionPlan(payload)
        message.success('干预计划已创建')
      }

      setPlanModalOpen(false)
      fetchPlans()
      fetchAlerts()
      fetchTickets()
    } catch {
      // handled by form validation
    }
  }

  const handleCreateFromTop5 = async (item: InterventionRecommendationItem) => {
    if (!canManage || !recommendation?.elder_id) return
    try {
      setCreatingFromRecoCode(item.code)
      await createInterventionPlanFromTop5({
        elder_id: recommendation.elder_id,
        session_id: recommendation.session_id,
        recommendation_code: item.code,
        duration_days: 30,
      })
      message.success('已从 Top-5 一键生成计划')
      fetchPlans()
      fetchAlerts()
      fetchTickets()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '创建计划失败')
    } finally {
      setCreatingFromRecoCode(null)
    }
  }

  const handleSyncTickets = async () => {
    setSyncingTickets(true)
    try {
      const res = await syncAdherenceTickets({ days: 14, threshold: 2 })
      message.success(`工单同步完成：新增 ${res.generated_count}，待处理 ${res.open_count}`)
      fetchAlerts()
      fetchTickets()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '工单同步失败')
    } finally {
      setSyncingTickets(false)
    }
  }

  const handleDispatchReminder = async () => {
    setDispatchingReminder(true)
    try {
      const res = await dispatchAdherenceReminders(true)
      message.success(`提醒派发完成：候选 ${res.candidate_count}，已推送 ${res.pushed_count}`)
      fetchTickets()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '提醒派发失败')
    } finally {
      setDispatchingReminder(false)
    }
  }

  const openTicketModal = (ticket: AdherenceTicket) => {
    setEditingTicket(ticket)
    ticketForm.setFieldsValue({
      status: ticket.status,
      owner_doctor_id: ticket.owner_doctor_id,
      reminder_at: ticket.reminder_at ? dayjs(ticket.reminder_at) : undefined,
      followup_note: ticket.followup_note,
    })
    setTicketModalOpen(true)
  }

  const handleUpdateTicket = async () => {
    if (!editingTicket) return
    try {
      const values = await ticketForm.validateFields()
      setUpdatingTicket(true)
      await updateAdherenceTicket(editingTicket.id, {
        status: values.status,
        owner_doctor_id: values.owner_doctor_id,
        reminder_at: values.reminder_at?.format('YYYY-MM-DDTHH:mm:ss'),
        followup_note: values.followup_note,
      })
      message.success('工单已更新')
      setTicketModalOpen(false)
      fetchTickets()
      fetchAlerts()
    } catch {
      // form message handles validation
    } finally {
      setUpdatingTicket(false)
    }
  }

  const completionRate = (plan: InterventionPlan): number => {
    if (!plan.total_records) return 0
    return Math.round(((plan.completed_count || 0) / plan.total_records) * 100)
  }

  const ticketStats = useMemo(() => {
    const total = tickets.length
    const open = tickets.filter((t) => t.status === 'open').length
    const inProgress = tickets.filter((t) => t.status === 'in_progress').length
    const resolved = tickets.filter((t) => t.status === 'resolved').length
    return { total, open, inProgress, resolved }
  }, [tickets])

  const planColumns: ColumnsType<InterventionPlan> = [
    {
      title: '计划',
      key: 'title',
      width: 220,
      render: (_, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{row.title}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {row.elder_name || `老人 #${row.elder_id}`}
          </Text>
        </Space>
      ),
    },
    {
      title: '认知域',
      key: 'domain',
      width: 220,
      render: (_, row) => (
        <>
          {domainTags(row.domain_focus).map((domain) => (
            <Tag key={domain} color="blue">
              {DOMAIN_LABELS[domain] || domain}
            </Tag>
          ))}
        </>
      ),
    },
    { title: '频次', dataIndex: 'frequency', key: 'frequency', width: 110 },
    {
      title: '完成率',
      key: 'completion',
      width: 160,
      render: (_, row) => (
        <>
          <Progress size="small" percent={completionRate(row)} />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {row.completed_count || 0}/{row.total_records || 0}
          </Text>
        </>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: InterventionPlan['status']) => {
        const cfg = planStatusMap[status]
        return <Tag color={cfg.color}>{cfg.text}</Tag>
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      align: 'center',
      render: (_, row) =>
        canManage ? (
          <Button type="link" icon={<EditOutlined />} onClick={() => openEditPlan(row)}>
            编辑
          </Button>
        ) : (
          '-'
        ),
    },
  ]

  const alertColumns: ColumnsType<InterventionAdherenceAlert> = [
    { title: '老人', dataIndex: 'elder_name', key: 'elder_name', width: 110 },
    { title: '计划', dataIndex: 'plan_title', key: 'plan_title', width: 220 },
    {
      title: '连续未完成',
      dataIndex: 'consecutive_missed_days',
      key: 'consecutive_missed_days',
      width: 120,
      render: (v) => <Tag color={v >= 5 ? 'error' : 'warning'}>{v} 天</Tag>,
    },
    { title: '完成率', dataIndex: 'completion_rate', key: 'completion_rate', width: 100, render: (v) => `${v}%` },
    { title: '中断原因', dataIndex: 'latest_interruption_reason', key: 'latest_interruption_reason', render: (v) => v || '-' },
    { title: '风险等级', dataIndex: 'risk_level', key: 'risk_level', width: 110, render: (v) => v || '-' },
  ]

  const ticketColumns: ColumnsType<AdherenceTicket> = [
    {
      title: '工单',
      key: 'ticket',
      width: 250,
      render: (_, row) => (
        <Space direction="vertical" size={0}>
          <Space>
            <Text strong>#{row.id}</Text>
            {focusedTicketId === row.id && <Tag color="gold">当前关注</Tag>}
          </Space>
          <Text>{row.plan_title || `计划 #${row.plan_id}`}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {row.elder_name || `老人 #${row.elder_id}`}
          </Text>
        </Space>
      ),
    },
    {
      title: '风险/依从',
      key: 'risk',
      width: 180,
      render: (_, row) => (
        <Space direction="vertical" size={0}>
          <Text style={{ fontSize: 12 }}>风险：{row.risk_level || '-'}</Text>
          <Text style={{ fontSize: 12 }}>连续未完成：{row.consecutive_missed_days} 天</Text>
          <Text style={{ fontSize: 12 }}>近7-14天完成率：{row.completion_rate}%</Text>
        </Space>
      ),
    },
    {
      title: '工单状态',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (status: AdherenceTicket['status']) => {
        const cfg = ticketStatusMap[status]
        return <Tag color={cfg.color}>{cfg.text}</Tag>
      },
    },
    {
      title: '责任医生',
      key: 'owner',
      width: 120,
      render: (_, row) => row.owner_doctor_name || (row.owner_doctor_id ? `医生 #${row.owner_doctor_id}` : '-'),
    },
    {
      title: '提醒时间',
      dataIndex: 'reminder_at',
      key: 'reminder_at',
      width: 160,
      render: (value?: string) => (value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '回访记录',
      dataIndex: 'followup_note',
      key: 'followup_note',
      render: (value?: string) => value || '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      align: 'center',
      render: (_, row) => (
        <Button type="link" icon={<EditOutlined />} onClick={() => openTicketModal(row)}>
          处理
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>
          干预管理
        </Title>
        <Text type="secondary">支持 Top-5 一键生成计划、依从性预警工单闭环与微信提醒派发。</Text>
      </div>

      {canManage && (
        <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
          <Col xs={12} sm={6}><Card><Statistic title="工单总数" value={ticketStats.total} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="待处理" value={ticketStats.open} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="处理中" value={ticketStats.inProgress} valueStyle={{ color: '#1677ff' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="已处理" value={ticketStats.resolved} valueStyle={{ color: '#52c41a' }} /></Card></Col>
        </Row>
      )}

      <Card
        title={
          <Space>
            <BulbOutlined style={{ color: '#faad14' }} />
            <Text strong>Top-5 干预推荐（最新评估）</Text>
          </Space>
        }
        extra={<Button icon={<ReloadOutlined />} onClick={fetchTop5}>刷新推荐</Button>}
        style={{ borderRadius: 12, marginBottom: 20 }}
      >
        {recommendation ? (
          <Text type="secondary" style={{ display: 'block', marginBottom: 10 }}>
            会话 #{recommendation.session_id} · 风险 {recommendation.risk_level} · MMSE {recommendation.mmse_score ?? '-'}
          </Text>
        ) : (
          <Alert type="warning" showIcon message="暂无可用推荐，请先完成一条评估结果。" style={{ marginBottom: 10 }} />
        )}

        <Table
          rowKey="code"
          size="small"
          loading={recLoading}
          pagination={false}
          dataSource={recommendation?.recommendations || []}
          columns={[
            { title: '排名', dataIndex: 'rank', key: 'rank', width: 70 },
            { title: '推荐项', dataIndex: 'title', key: 'title', width: 200 },
            {
              title: '目标认知域',
              key: 'domains',
              render: (_, row: InterventionRecommendationItem) => (
                <>
                  {row.target_domains.map((d) => (
                    <Tag key={d} color="blue">{DOMAIN_LABELS[d] || d}</Tag>
                  ))}
                </>
              ),
            },
            { title: '频次', dataIndex: 'frequency', key: 'frequency', width: 100 },
            { title: '时长', dataIndex: 'duration_minutes', key: 'duration_minutes', width: 90, render: (v) => `${v} 分钟` },
            {
              title: '操作',
              key: 'action',
              width: 130,
              render: (_, row: InterventionRecommendationItem) =>
                canManage ? (
                  <Button
                    type="link"
                    loading={creatingFromRecoCode === row.code}
                    onClick={() => handleCreateFromTop5(row)}
                  >
                    一键生成计划
                  </Button>
                ) : (
                  '-'
                ),
            },
          ]}
        />
      </Card>

      {canManage && (
        <Card
          title={
            <Space>
              <WarningOutlined style={{ color: '#ff4d4f' }} />
              <Text strong>依从性预警（触发依据）</Text>
            </Space>
          }
          extra={<Button icon={<ReloadOutlined />} onClick={fetchAlerts}>刷新预警</Button>}
          style={{ borderRadius: 12, marginBottom: 20 }}
        >
          <Table
            rowKey={(row) => `${row.plan_id}-${row.elder_id}`}
            loading={alertLoading}
            size="small"
            pagination={{ pageSize: 5 }}
            dataSource={alerts}
            columns={alertColumns}
          />
        </Card>
      )}

      {canManage && (
        <Card
          title={
            <Space>
              <WarningOutlined style={{ color: '#fa541c' }} />
              <Text strong>预警处置工单</Text>
            </Space>
          }
          extra={
            <Space>
              <Select
                allowClear
                placeholder="工单状态"
                style={{ width: 130 }}
                value={ticketStatusFilter}
                onChange={(value) => setTicketStatusFilter(value)}
                options={[
                  { label: '待处理', value: 'open' },
                  { label: '处理中', value: 'in_progress' },
                  { label: '已处理', value: 'resolved' },
                  { label: '已忽略', value: 'ignored' },
                ]}
              />
              <Button icon={<SyncOutlined />} loading={syncingTickets} onClick={handleSyncTickets}>同步工单</Button>
              <Button icon={<SendOutlined />} loading={dispatchingReminder} onClick={handleDispatchReminder}>派发提醒</Button>
              <Button icon={<ReloadOutlined />} onClick={fetchTickets}>刷新</Button>
            </Space>
          }
          style={{ borderRadius: 12, marginBottom: 20 }}
        >
          <Table
            rowKey="id"
            loading={ticketLoading}
            dataSource={tickets}
            columns={ticketColumns}
            scroll={{ x: 1200 }}
            pagination={{ pageSize: 8 }}
          />
        </Card>
      )}

      <Card
        style={{ borderRadius: 12 }}
        title={<Text strong>干预计划列表</Text>}
        extra={
          <Space>
            <Select
              allowClear
              placeholder="计划状态"
              style={{ width: 130 }}
              value={planStatusFilter}
              onChange={(value) => setPlanStatusFilter(value)}
              options={Object.entries(planStatusMap).map(([value, cfg]) => ({ label: cfg.text, value }))}
            />
            <Button icon={<ReloadOutlined />} onClick={fetchPlans}>刷新</Button>
            {canManage && (
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreatePlan}>
                新建计划
              </Button>
            )}
          </Space>
        }
      >
        <Table
          rowKey="id"
          loading={planLoading}
          dataSource={plans}
          columns={planColumns}
          scroll={{ x: 950 }}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>

      {canManage && (
        <Modal
          title={editingPlan ? '编辑干预计划' : '新建干预计划'}
          open={planModalOpen}
          onOk={handleSavePlan}
          onCancel={() => setPlanModalOpen(false)}
          okText={editingPlan ? '保存' : '创建'}
          cancelText="取消"
          width={640}
          destroyOnClose
        >
          <Form form={planForm} layout="vertical" style={{ marginTop: 16 }}>
            {!editingPlan && (
              <Form.Item name="elder_id" label="服务老人" rules={[{ required: true, message: '请选择老人' }]}>
                <Select
                  showSearch
                  optionFilterProp="label"
                  options={elders.map((e) => ({ label: e.name, value: e.id }))}
                  placeholder="选择老人"
                />
              </Form.Item>
            )}

            <Form.Item name="title" label="计划标题" rules={[{ required: true, message: '请输入计划标题' }]}>
              <Input placeholder="例如：记忆强化训练计划" />
            </Form.Item>

            <Form.Item name="description" label="计划说明">
              <TextArea rows={3} placeholder="说明目标、执行方式、注意事项" />
            </Form.Item>

            <Form.Item name="domain_focus" label="目标认知域">
              <Select mode="multiple" options={DOMAIN_OPTIONS} placeholder="可多选" />
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
                <Select options={Object.entries(planStatusMap).map(([value, cfg]) => ({ label: cfg.text, value }))} />
              </Form.Item>
            )}
          </Form>
        </Modal>
      )}

      {canManage && (
        <Modal
          title={`处理工单 #${editingTicket?.id || ''}`}
          open={ticketModalOpen}
          onCancel={() => setTicketModalOpen(false)}
          onOk={handleUpdateTicket}
          okText="保存"
          confirmLoading={updatingTicket}
          destroyOnClose
        >
          <Form form={ticketForm} layout="vertical" style={{ marginTop: 16 }}>
            <Form.Item name="status" label="工单状态" rules={[{ required: true, message: '请选择状态' }]}>
              <Select
                options={[
                  { label: '待处理', value: 'open' },
                  { label: '处理中', value: 'in_progress' },
                  { label: '已处理', value: 'resolved' },
                  { label: '已忽略', value: 'ignored' },
                ]}
              />
            </Form.Item>

            <Form.Item name="owner_doctor_id" label="责任医生">
              <Select
                allowClear
                placeholder="选择责任医生"
                options={doctors.map((d) => ({ label: `${d.name}（${d.phone || d.id}）`, value: d.id }))}
              />
            </Form.Item>

            <Form.Item name="reminder_at" label="下次提醒时间">
              <DatePicker style={{ width: '100%' }} showTime format="YYYY-MM-DD HH:mm" />
            </Form.Item>

            <Form.Item name="followup_note" label="回访记录">
              <TextArea rows={4} placeholder="记录已处理动作、家属沟通情况、后续计划" />
            </Form.Item>
          </Form>
        </Modal>
      )}
    </div>
  )
}
