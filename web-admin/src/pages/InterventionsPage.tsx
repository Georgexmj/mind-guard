import { useEffect, useState, useCallback } from 'react'
import {
  Card, Table, Button, Space, Typography, Tag, Modal, Form,
  Input, Select, DatePicker, InputNumber, Row, Col, Tooltip,
  Progress, Statistic,
} from 'antd'
import {
  PlusOutlined, EditOutlined, EyeOutlined, CheckCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { getInterventionPlans, createInterventionPlan, updateInterventionPlan, getElders } from '../services/api'
import type { User } from '../types'

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
  active:    { text: '进行中', color: 'processing' },
  paused:    { text: '已暂停', color: 'warning' },
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

const MOCK_PLANS: InterventionPlan[] = [
  { id: 1, elder_id: 1, elder_name: '王秀兰', created_by: 2, title: '记忆力强化训练', description: '每日进行词语联想和图片记忆练习', domain_focus: 'memory,attention', frequency: '每天一次', duration_days: 30, start_date: '2026-03-01', end_date: '2026-03-31', status: 'active', ai_priority: 8.5, completed_count: 18, total_records: 26, created_at: '2026-03-01T08:00:00' },
  { id: 2, elder_id: 4, elder_name: '陈福寿', created_by: 2, title: '综合认知干预方案', description: '针对高风险老人的多域联合训练', domain_focus: 'memory,executive,language', frequency: '每周三次', duration_days: 60, start_date: '2026-02-15', end_date: '2026-04-15', status: 'active', ai_priority: 9.2, completed_count: 12, total_records: 15, created_at: '2026-02-15T09:00:00' },
  { id: 3, elder_id: 9, elder_name: '孙美英', created_by: 2, title: '语言能力训练计划', description: '通过朗读、讲故事等方式提升语言流利度', domain_focus: 'language', frequency: '每天两次', duration_days: 21, start_date: '2026-03-10', end_date: '2026-03-31', status: 'active', ai_priority: 7.8, completed_count: 25, total_records: 34, created_at: '2026-03-10T10:00:00' },
  { id: 4, elder_id: 2, elder_name: '李德明', created_by: 2, title: '定向力训练', description: '日历辨别、地点识别、时间感知练习', domain_focus: 'orientation', frequency: '每天一次', duration_days: 14, start_date: '2026-02-01', end_date: '2026-02-14', status: 'completed', ai_priority: 6.5, completed_count: 14, total_records: 14, created_at: '2026-02-01T08:00:00' },
]

export default function InterventionsPage() {
  const [plans, setPlans] = useState<InterventionPlan[]>(MOCK_PLANS)
  const [elders, setElders] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingPlan, setEditingPlan] = useState<InterventionPlan | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [form] = Form.useForm()
  const navigate = useNavigate()

  const fetchPlans = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getInterventionPlans({ status: statusFilter })
      if (Array.isArray(res) && res.length > 0) setPlans(res as InterventionPlan[])
    } catch {
      // keep mock data
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  const fetchElders = useCallback(async () => {
    try {
      const res = await getElders()
      setElders(res)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => { fetchPlans() }, [fetchPlans])
  useEffect(() => { fetchElders() }, [fetchElders])

  const openCreate = () => {
    setEditingPlan(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (plan: InterventionPlan) => {
    setEditingPlan(plan)
    form.setFieldsValue({
      ...plan,
      start_date: plan.start_date ? dayjs(plan.start_date) : undefined,
      end_date: plan.end_date ? dayjs(plan.end_date) : undefined,
      domain_focus: plan.domain_focus ? plan.domain_focus.split(',') : [],
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
      // validation or API error — keep modal open
    }
  }

  const completionRate = (plan: InterventionPlan) => {
    if (!plan.total_records) return 0
    return Math.round(((plan.completed_count || 0) / plan.total_records) * 100)
  }

  const columns: ColumnsType<InterventionPlan> = [
    {
      title: '干预计划',
      key: 'plan',
      width: 220,
      render: (_, r) => (
        <div>
          <div style={{ fontWeight: 600, color: '#1a1a2e', marginBottom: 2 }}>{r.title}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>{r.elder_name || `老人 #${r.elder_id}`}</Text>
        </div>
      ),
    },
    {
      title: '认知域',
      dataIndex: 'domain_focus',
      key: 'domains',
      width: 200,
      render: (domains: string) =>
        domains
          ? domains.split(',').map((d) => {
              const opt = DOMAIN_OPTIONS.find((o) => o.value === d.trim())
              return <Tag key={d} color="blue" style={{ borderRadius: 10, marginBottom: 2 }}>{opt?.label || d}</Tag>
            })
          : <Text type="secondary">—</Text>,
    },
    {
      title: '频次',
      dataIndex: 'frequency',
      key: 'frequency',
      width: 100,
      render: (f) => f || '—',
    },
    {
      title: '完成率',
      key: 'completion',
      width: 140,
      render: (_, r) => (
        <div>
          <Progress
            percent={completionRate(r)}
            size="small"
            strokeColor={completionRate(r) >= 80 ? '#52c41a' : completionRate(r) >= 50 ? '#faad14' : '#ff4d4f'}
            style={{ marginBottom: 2 }}
          />
          <Text style={{ fontSize: 11, color: '#999' }}>
            {r.completed_count}/{r.total_records} 次
          </Text>
        </div>
      ),
    },
    {
      title: '起止日期',
      key: 'dates',
      width: 160,
      render: (_, r) => (
        <Text style={{ fontSize: 12 }}>
          {r.start_date ? dayjs(r.start_date).format('MM/DD') : '—'}
          {' ~ '}
          {r.end_date ? dayjs(r.end_date).format('MM/DD') : '—'}
        </Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      align: 'center',
      render: (s) => {
        const cfg = statusConfig[s] || { text: s, color: 'default' }
        return <Tag color={cfg.color} style={{ borderRadius: 10 }}>{cfg.text}</Tag>
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      align: 'center',
      fixed: 'right',
      render: (_, r) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/elders/${r.elder_id}`)}
              style={{ padding: 0 }}
            />
          </Tooltip>
          <Tooltip title="编辑计划">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openEdit(r)}
              style={{ padding: 0 }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  const activeCount = plans.filter((p) => p.status === 'active').length
  const avgCompletion = plans.length
    ? Math.round(plans.reduce((sum, p) => sum + completionRate(p), 0) / plans.length)
    : 0

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>干预管理</Title>
        <Text type="secondary">AI推荐 + 医生制定的个性化认知干预计划</Text>
      </div>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        {[
          { title: '总计划数', value: plans.length, suffix: '项', color: '#1677ff' },
          { title: '进行中', value: activeCount, suffix: '项', color: '#52c41a' },
          { title: '平均完成率', value: avgCompletion, suffix: '%', color: '#fa8c16' },
        ].map((card) => (
          <Col xs={24} sm={8} key={card.title}>
            <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }} bodyStyle={{ padding: '16px 20px' }}>
              <Statistic title={card.title} value={card.value} suffix={card.suffix} valueStyle={{ color: card.color, fontSize: 28 }} />
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        {/* Toolbar */}
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col flex="auto">
            <Select
              placeholder="筛选状态"
              allowClear
              style={{ width: 140 }}
              value={statusFilter}
              onChange={setStatusFilter}
              options={Object.entries(statusConfig).map(([v, c]) => ({ label: c.text, value: v }))}
            />
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchPlans}>刷新</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建计划</Button>
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={plans}
          rowKey="id"
          loading={loading}
          scroll={{ x: 900 }}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 项` }}
        />
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        title={editingPlan ? '编辑干预计划' : '新建干预计划'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText={editingPlan ? '保存' : '创建'}
        cancelText="取消"
        width={600}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {!editingPlan && (
            <Form.Item name="elder_id" label="服务老人" rules={[{ required: true, message: '请选择服务对象' }]}>
              <Select
                placeholder="选择老人"
                showSearch
                optionFilterProp="label"
                options={elders.map((e) => ({ label: e.name, value: e.id }))}
              />
            </Form.Item>
          )}
          <Form.Item name="title" label="计划标题" rules={[{ required: true, message: '请输入标题' }]}>
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
                <Select placeholder="选择频次" options={[
                  { label: '每天一次', value: '每天一次' },
                  { label: '每天两次', value: '每天两次' },
                  { label: '每周三次', value: '每周三次' },
                  { label: '每周五次', value: '每周五次' },
                ]} />
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
              <Select options={Object.entries(statusConfig).map(([v, c]) => ({ label: c.text, value: v }))} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}
