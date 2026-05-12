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
  Tabs,
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
  batchUpdateAdherenceTickets,
  createInterventionPlan,
  createInterventionPlanFromTop5,
  dispatchAdherenceReminders,
  getAdherenceTicketStats,
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
  AdherenceTicketStats,
  InterventionAdherenceAlert,
  InterventionRecommendationItem,
  InterventionTop5Recommendation,
  User,
} from '../types'
const { Title, Text } = Typography
const { TextArea } = Input

// 直接从 localStorage 获取用户信息
const getUserFromStorage = (): User | null => {
  try {
    const stored = localStorage.getItem('mindguard-user')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

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

const DIRTY_TEXT_PATTERN = /(\?{2,}|�|锟)/i

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

type InterventionSectionKey = 'overview' | 'recommendations' | 'alerts' | 'tickets' | 'plans'

function domainTags(domains?: string): string[] {
  if (!domains) return []
  return domains
    .split(',')
    .map((d) => d.trim())
    .filter(Boolean)
}

function isDirtyText(value?: string | null): boolean {
  if (!value) return false
  return DIRTY_TEXT_PATTERN.test(value.trim())
}

function buildPlanTitle(domains?: string): string {
  const labels = domainTags(domains).map((domain) => DOMAIN_LABELS[domain] || domain)
  if (labels.length === 0) return 'AI-认知训练计划'
  if (labels.length === 1) return `AI-${labels[0]}训练`
  return `AI-${labels.slice(0, 2).join('与')}训练`
}

function buildPlanDescription(domains?: string): string {
  const labels = domainTags(domains).map((domain) => DOMAIN_LABELS[domain] || domain)
  if (labels.length === 0) return '个体化认知训练计划。'
  return `当前评估显示“${labels.join('、')}”相对薄弱，该干预可针对性改善相关认知功能。`
}

function normalizePlan(plan: InterventionPlan): InterventionPlan {
  const next = { ...plan }
  if (isDirtyText(next.title)) next.title = buildPlanTitle(next.domain_focus)
  if (isDirtyText(next.description) || !next.description?.trim()) next.description = buildPlanDescription(next.domain_focus)
  if (isDirtyText(next.frequency) || !next.frequency?.trim()) next.frequency = '每天1次'
  return next
}

function normalizeTicket(ticket: AdherenceTicket): AdherenceTicket {
  return {
    ...ticket,
    plan_title: isDirtyText(ticket.plan_title) ? buildPlanTitle(undefined) : ticket.plan_title,
    followup_note: isDirtyText(ticket.followup_note) ? undefined : ticket.followup_note,
    latest_interruption_reason: isDirtyText(ticket.latest_interruption_reason) ? undefined : ticket.latest_interruption_reason,
  }
}

function normalizeAlert(alert: InterventionAdherenceAlert): InterventionAdherenceAlert {
  return {
    ...alert,
    plan_title: isDirtyText(alert.plan_title) ? buildPlanTitle(undefined) : alert.plan_title,
    latest_interruption_reason: isDirtyText(alert.latest_interruption_reason) ? undefined : alert.latest_interruption_reason,
  }
}

export default function InterventionsPage() {
  const user = getUserFromStorage()
  const canManage = user?.role === 'admin' || user?.role === 'doctor'
  const [searchParams, setSearchParams] = useSearchParams()
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
  const [batchUpdatingTicket, setBatchUpdatingTicket] = useState(false)
  const [selectedTicketIds, setSelectedTicketIds] = useState<number[]>([])
  const [batchOwnerDoctorId, setBatchOwnerDoctorId] = useState<number | undefined>()
  const [batchReminderAt, setBatchReminderAt] = useState<Dayjs | null>(null)
  const [ticketStatsSummary, setTicketStatsSummary] = useState<AdherenceTicketStats | null>(null)

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
      setPlans(Array.isArray(data) ? (data as InterventionPlan[]).map(normalizePlan) : [])
    } catch {
      setPlans([])
    } finally {
      setPlanLoading(false)
    }
  }, [planStatusFilter])

  const fetchUsers = useCallback(async () => {
    try {
      const [elderRows, doctorRows] = await Promise.all([
        getElders({ page: 1, page_size: 100 }),
        getDoctors({ page: 1, page_size: 100 }),
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
      setAlerts(Array.isArray(data) ? data.map(normalizeAlert) : [])
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
      setTickets(Array.isArray(data) ? data.map(normalizeTicket) : [])
    } catch {
      setTickets([])
    } finally {
      setTicketLoading(false)
    }
  }, [canManage, ticketStatusFilter])

  const fetchTicketStats = useCallback(async () => {
    if (!canManage) return
    try {
      const stats = await getAdherenceTicketStats()
      setTicketStatsSummary(stats)
    } catch {
      setTicketStatsSummary(null)
    }
  }, [canManage])

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

  useEffect(() => {
    fetchTicketStats()
  }, [fetchTicketStats])

  useEffect(() => {
    setSelectedTicketIds((prev) => prev.filter((id) => tickets.some((ticket) => ticket.id === id)))
  }, [tickets])

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
      fetchTicketStats()
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
      fetchTicketStats()
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
      fetchTicketStats()
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
      fetchTicketStats()
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
      fetchTicketStats()
    } catch {
      // form message handles validation
    } finally {
      setUpdatingTicket(false)
    }
  }

  const handleBatchUpdateTickets = async (payload: {
    status?: AdherenceTicket['status']
    owner_doctor_id?: number
    reminder_at?: string
  }) => {
    if (selectedTicketIds.length === 0) {
      message.warning('请先勾选要处理的工单')
      return
    }
    if (!payload.status && !payload.owner_doctor_id && !payload.reminder_at) {
      message.warning('请先选择批处理动作')
      return
    }
    try {
      setBatchUpdatingTicket(true)
      const res = await batchUpdateAdherenceTickets({
        ticket_ids: selectedTicketIds,
        ...payload,
      })
      message.success(`批处理完成：更新 ${res.updated_count} 条，跳过 ${res.skipped_ids.length} 条`)
      setSelectedTicketIds([])
      if (payload.owner_doctor_id) setBatchOwnerDoctorId(undefined)
      if (payload.reminder_at) setBatchReminderAt(null)
      fetchTickets()
      fetchAlerts()
      fetchTicketStats()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '批处理失败')
    } finally {
      setBatchUpdatingTicket(false)
    }
  }

  const completionRate = (plan: InterventionPlan): number => {
    if (!plan.total_records) return 0
    return Math.round(((plan.completed_count || 0) / plan.total_records) * 100)
  }

  const ticketStats = useMemo(() => {
    if (ticketStatsSummary) {
      return {
        total: ticketStatsSummary.total_count,
        open: ticketStatsSummary.open_count,
        inProgress: ticketStatsSummary.in_progress_count,
        resolved: ticketStatsSummary.resolved_count,
        ignored: ticketStatsSummary.ignored_count,
        overdue: ticketStatsSummary.overdue_open_count,
        avgResponseHours: ticketStatsSummary.avg_response_hours,
        avgResolutionHours: ticketStatsSummary.avg_resolution_hours,
        within24hRate: ticketStatsSummary.resolved_within_24h_rate,
        within48hRate: ticketStatsSummary.resolved_within_48h_rate,
      }
    }
    const total = tickets.length
    const open = tickets.filter((t) => t.status === 'open').length
    const inProgress = tickets.filter((t) => t.status === 'in_progress').length
    const resolved = tickets.filter((t) => t.status === 'resolved').length
    const ignored = tickets.filter((t) => t.status === 'ignored').length
    const overdue = tickets.filter(
      (t) =>
        (t.status === 'open' || t.status === 'in_progress') &&
        Boolean(t.reminder_at) &&
        dayjs(t.reminder_at).isBefore(dayjs())
    ).length
    return {
      total,
      open,
      inProgress,
      resolved,
      ignored,
      overdue,
      avgResponseHours: undefined as number | undefined,
      avgResolutionHours: undefined as number | undefined,
      within24hRate: 0,
      within48hRate: 0,
    }
  }, [tickets, ticketStatsSummary])

  const sectionItems = useMemo(
    () =>
      canManage
        ? [
            { key: 'overview', label: '总览' },
            { key: 'recommendations', label: 'Top-5推荐' },
            { key: 'alerts', label: '依从性预警' },
            { key: 'tickets', label: '处置工单' },
            { key: 'plans', label: '干预计划' },
          ]
        : [
            { key: 'recommendations', label: 'Top-5推荐' },
            { key: 'plans', label: '干预计划' },
          ],
    [canManage]
  )

  const defaultSectionKey: InterventionSectionKey = canManage
    ? (focusedTicketId > 0 || searchParams.get('queue') === 'low_adherence' ? 'tickets' : 'overview')
    : 'recommendations'

  const sectionKeySet = new Set(sectionItems.map((item) => item.key))
  const activeSection = (searchParams.get('section') || defaultSectionKey) as InterventionSectionKey
  const currentSection: InterventionSectionKey = sectionKeySet.has(activeSection) ? activeSection : defaultSectionKey

  const handleSectionChange = (key: string) => {
    const next = new URLSearchParams(searchParams)
    if (key === defaultSectionKey) next.delete('section')
    else next.set('section', key)
    setSearchParams(next, { replace: true })
  }

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

  const overviewContent = canManage ? (
    <>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8} lg={4}><Card><Statistic title="工单总数" value={ticketStats.total} /></Card></Col>
        <Col xs={12} sm={8} lg={4}><Card><Statistic title="待处理" value={ticketStats.open} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
        <Col xs={12} sm={8} lg={4}><Card><Statistic title="处理中" value={ticketStats.inProgress} valueStyle={{ color: '#1677ff' }} /></Card></Col>
        <Col xs={12} sm={8} lg={4}><Card><Statistic title="已处理" value={ticketStats.resolved} valueStyle={{ color: '#52c41a' }} /></Card></Col>
        <Col xs={12} sm={8} lg={4}><Card><Statistic title="已忽略" value={ticketStats.ignored} /></Card></Col>
        <Col xs={12} sm={8} lg={4}><Card><Statistic title="超时待办" value={ticketStats.overdue} valueStyle={{ color: '#fa541c' }} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}><Card><Statistic title="平均响应时效" value={ticketStats.avgResponseHours ?? 0} suffix="h" precision={1} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="平均处置时长" value={ticketStats.avgResolutionHours ?? 0} suffix="h" precision={1} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="24h处置率" value={ticketStats.within24hRate} suffix="%" precision={1} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="48h处置率" value={ticketStats.within48hRate} suffix="%" precision={1} /></Card></Col>
      </Row>
    </>
  ) : null

  const top5Card = (
    <Card
      title={
        <Space>
          <BulbOutlined style={{ color: '#faad14' }} />
          <Text strong>Top-5 干预推荐（最新评估）</Text>
        </Space>
      }
      extra={<Button icon={<ReloadOutlined />} onClick={fetchTop5}>刷新推荐</Button>}
      style={{ borderRadius: 12 }}
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
  )

  const alertsCard = canManage ? (
    <Card
      title={
        <Space>
          <WarningOutlined style={{ color: '#ff4d4f' }} />
          <Text strong>依从性预警（触发依据）</Text>
        </Space>
      }
      extra={<Button icon={<ReloadOutlined />} onClick={fetchAlerts}>刷新预警</Button>}
      style={{ borderRadius: 12 }}
    >
      <Table
        rowKey={(row) => `${row.plan_id}-${row.elder_id}`}
        loading={alertLoading}
        size="small"
        pagination={{ pageSize: 8 }}
        dataSource={alerts}
        columns={alertColumns}
      />
    </Card>
  ) : null

  const ticketsCard = canManage ? (
    <Card
      title={
        <Space>
          <WarningOutlined style={{ color: '#fa541c' }} />
          <Text strong>预警处置工单</Text>
        </Space>
      }
      extra={
        <Space>
          <Tag color={selectedTicketIds.length > 0 ? 'blue' : 'default'}>
            已选 {selectedTicketIds.length} 条
          </Tag>
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
      style={{ borderRadius: 12 }}
    >
      <Space wrap style={{ marginBottom: 12 }}>
        <Button
          loading={batchUpdatingTicket}
          disabled={selectedTicketIds.length === 0}
          onClick={() => handleBatchUpdateTickets({ status: 'in_progress' })}
        >
          批量设为处理中
        </Button>
        <Button
          type="primary"
          loading={batchUpdatingTicket}
          disabled={selectedTicketIds.length === 0}
          onClick={() => handleBatchUpdateTickets({ status: 'resolved' })}
        >
          批量设为已处理
        </Button>
        <Select
          allowClear
          placeholder="批量指派医生"
          style={{ width: 220 }}
          value={batchOwnerDoctorId}
          onChange={(value) => setBatchOwnerDoctorId(value)}
          options={doctors.map((d) => ({ label: `${d.name}（${d.phone || d.id}）`, value: d.id }))}
        />
        <Button
          loading={batchUpdatingTicket}
          disabled={selectedTicketIds.length === 0 || !batchOwnerDoctorId}
          onClick={() => handleBatchUpdateTickets({ owner_doctor_id: batchOwnerDoctorId })}
        >
          批量指派
        </Button>
        <DatePicker
          showTime
          format="YYYY-MM-DD HH:mm"
          placeholder="批量提醒时间"
          value={batchReminderAt}
          onChange={(value) => setBatchReminderAt(value)}
        />
        <Button
          loading={batchUpdatingTicket}
          disabled={selectedTicketIds.length === 0 || !batchReminderAt}
          onClick={() =>
            handleBatchUpdateTickets({
              reminder_at: batchReminderAt?.format('YYYY-MM-DDTHH:mm:ss'),
            })
          }
        >
          批量设提醒
        </Button>
      </Space>
      <Table
        rowKey="id"
        loading={ticketLoading}
        dataSource={tickets}
        columns={ticketColumns}
        rowSelection={{
          selectedRowKeys: selectedTicketIds,
          onChange: (keys) => setSelectedTicketIds(keys.map((key) => Number(key))),
        }}
        scroll={{ x: 1200 }}
        pagination={{ pageSize: 8 }}
      />
    </Card>
  ) : null

  const plansCard = (
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
  )

  return (
    <div className="mg-page">
      <div className="mg-page-header">
        <div>
          <Title level={4} className="mg-page-title">
          干预管理
        </Title>
          <Text className="mg-page-subtitle">支持 Top-5 一键生成计划、依从性预警工单闭环与微信提醒派发。</Text>
        </div>
      </div>

      <Card className="mg-panel-card" style={{ borderRadius: 14, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }} styles={{ body: { padding: '8px 20px 20px' } }}>
        <Tabs
          activeKey={currentSection}
          onChange={handleSectionChange}
          items={sectionItems}
          tabBarStyle={{ marginBottom: 20 }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {currentSection === 'overview' && overviewContent}
          {currentSection === 'recommendations' && top5Card}
          {currentSection === 'alerts' && alertsCard}
          {currentSection === 'tickets' && ticketsCard}
          {currentSection === 'plans' && plansCard}
        </div>
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
