import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Avatar,
  Button,
  Card,
  Col,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd'
import { DeleteOutlined, EyeOutlined, LinkOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import {
  createFamilyRelationship,
  deleteFamilyRelationship,
  getDashboardWorkbenchQueues,
  getCommunities,
  getElders,
  getFamilies,
  getFamilyRelationships,
} from '../services/api'
import type { Community, FamilyRelationship, User } from '../types'
import RiskBadge from '../components/RiskBadge'

const { Title, Text } = Typography

type ElderRow = User & {
  community_name?: string
  last_assessment?: string
  risk_level?: 'normal' | 'mild_risk' | 'high_risk'
}

const genderMap: Record<string, string> = { male: '男', female: '女' }

function educationLabel(years?: number): string {
  if (years == null) return '未填写'
  if (years <= 6) return '小学'
  if (years <= 9) return '初中'
  if (years <= 12) return '高中'
  if (years <= 15) return '大专'
  return '本科及以上'
}

function calcAge(birthDate?: string): string {
  if (!birthDate) return '-'
  return `${dayjs().diff(dayjs(birthDate), 'year')}岁`
}

export default function EldersPage() {
  const [elders, setElders] = useState<ElderRow[]>([])
  const [communities, setCommunities] = useState<Community[]>([])
  const [loading, setLoading] = useState(false)

  const [searchName, setSearchName] = useState('')
  const [communityFilter, setCommunityFilter] = useState<number | undefined>()

  const [bindModalOpen, setBindModalOpen] = useState(false)
  const [families, setFamilies] = useState<User[]>([])
  const [relations, setRelations] = useState<FamilyRelationship[]>([])
  const [relationLoading, setRelationLoading] = useState(false)
  const [bindForm] = Form.useForm()
  const [queueElderIdSet, setQueueElderIdSet] = useState<Set<number>>(new Set())

  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const queueFilter = (searchParams.get('queue') || '').trim()

  const fetchElders = useCallback(async () => {
    setLoading(true)
    try {
      const rows = await getElders({ page: 1, page_size: 200, community_id: communityFilter })
      const normalized = (rows || []) as ElderRow[]
      setElders(normalized)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载老人列表失败')
      setElders([])
    } finally {
      setLoading(false)
    }
  }, [communityFilter])

  const fetchCommunities = useCallback(async () => {
    try {
      const rows = await getCommunities()
      setCommunities(rows || [])
    } catch {
      setCommunities([])
    }
  }, [])

  const fetchRelationData = useCallback(async () => {
    setRelationLoading(true)
    try {
      const [familyRows, relationRows] = await Promise.all([
        getFamilies({ page: 1, page_size: 500 }),
        getFamilyRelationships(),
      ])
      setFamilies(Array.isArray(familyRows) ? familyRows : [])
      setRelations(Array.isArray(relationRows) ? relationRows : [])
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载家属绑定数据失败')
      setFamilies([])
      setRelations([])
    } finally {
      setRelationLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchElders()
  }, [fetchElders])

  useEffect(() => {
    fetchCommunities()
  }, [fetchCommunities])

  useEffect(() => {
    const loadQueueFilter = async () => {
      if (queueFilter !== 'reassessment_due') {
        setQueueElderIdSet(new Set())
        return
      }
      try {
        const queues = await getDashboardWorkbenchQueues(500)
        const idSet = new Set<number>()
        ;(queues.reassessment_due || []).forEach((item) => {
          if (typeof item.elder_id === 'number') idSet.add(item.elder_id)
        })
        setQueueElderIdSet(idSet)
      } catch {
        setQueueElderIdSet(new Set())
      }
    }
    loadQueueFilter()
  }, [queueFilter])

  const filteredRows = useMemo(() => {
    const keyword = searchName.trim().toLowerCase()
    let result = elders
    if (queueFilter === 'reassessment_due') {
      result = result.filter((item) => queueElderIdSet.has(item.id))
    }
    if (!keyword) return result
    return result.filter((item) =>
      `${item.name || ''}${item.phone || ''}`.toLowerCase().includes(keyword)
    )
  }, [elders, queueFilter, queueElderIdSet, searchName])

  const handleReset = () => {
    setSearchName('')
    setCommunityFilter(undefined)
  }

  const clearQueueFilter = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('queue')
    setSearchParams(next)
  }

  const openBindModal = async () => {
    setBindModalOpen(true)
    await fetchRelationData()
  }

  const handleCreateRelation = async () => {
    try {
      const values = await bindForm.validateFields()
      await createFamilyRelationship({
        elder_id: values.elder_id,
        family_id: values.family_id,
        relationship: values.relationship,
        notify_level: values.notify_level ?? 1,
        is_primary: Boolean(values.is_primary),
      })
      message.success('绑定成功')
      bindForm.resetFields()
      fetchRelationData()
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message)
      }
    }
  }

  const handleDeleteRelation = async (relationId: number) => {
    try {
      await deleteFamilyRelationship(relationId)
      message.success('解绑成功')
      fetchRelationData()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '解绑失败')
    }
  }

  const columns: ColumnsType<ElderRow> = [
    {
      title: '老人信息',
      key: 'info',
      width: 230,
      render: (_, row) => (
        <Space>
          <Avatar style={{ background: '#e6f4ff', color: '#1677ff', fontWeight: 700 }}>{row.name?.[0] || '?'}</Avatar>
          <div>
            <div style={{ fontWeight: 600 }}>{row.name}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>{genderMap[row.gender || ''] || '-'} · {row.phone || '-'}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '年龄',
      key: 'age',
      width: 80,
      align: 'center',
      render: (_, row) => calcAge(row.birth_date),
    },
    {
      title: '文化程度',
      dataIndex: 'education_years',
      key: 'education',
      width: 110,
      align: 'center',
      render: (years) => <Tag color="blue">{educationLabel(years)}</Tag>,
    },
    {
      title: '所属社区',
      dataIndex: 'community_name',
      key: 'community_name',
      width: 160,
      render: (value) => value || '-',
    },
    {
      title: '最近评估',
      dataIndex: 'last_assessment',
      key: 'last_assessment',
      width: 120,
      align: 'center',
      render: (date) => (date ? dayjs(date).format('MM-DD') : <Text type="secondary">暂无</Text>),
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 120,
      align: 'center',
      render: (risk) => (risk ? <RiskBadge riskLevel={risk} /> : <Tag>未评估</Tag>),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      align: 'center',
      fixed: 'right',
      render: (_, row) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => navigate(`/elders/${row.id}`)}>
          查看详情
        </Button>
      ),
    },
  ]

  const relationColumns: ColumnsType<FamilyRelationship> = [
    { title: '老人', dataIndex: 'elder_name', key: 'elder_name', render: (_, row) => row.elder_name || `#${row.elder_id}` },
    { title: '家属', dataIndex: 'family_name', key: 'family_name', render: (_, row) => row.family_name || `#${row.family_id}` },
    { title: '关系', dataIndex: 'relationship', key: 'relationship' },
    { title: '通知级别', dataIndex: 'notify_level', key: 'notify_level', width: 100 },
    {
      title: '主联系人',
      dataIndex: 'is_primary',
      key: 'is_primary',
      width: 100,
      render: (v: boolean) => (v ? <Tag color="green">是</Tag> : <Tag>否</Tag>),
    },
    {
      title: '操作',
      key: 'actions',
      width: 90,
      render: (_, row) => (
        <Button danger type="link" icon={<DeleteOutlined />} onClick={() => handleDeleteRelation(row.id)}>
          解绑
        </Button>
      ),
    },
  ]

  return (
    <div className="mg-page">
      <div className="mg-page-header">
        <div>
          <Title level={4} className="mg-page-title">老人管理</Title>
          <Text className="mg-page-subtitle">共 {filteredRows.length} 位老人</Text>
        </div>
      </div>

      <Card className="mg-panel-card" style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }} bodyStyle={{ padding: '20px 24px' }}>
        <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="搜索老人姓名/手机号"
              prefix={<SearchOutlined style={{ color: '#bbb' }} />}
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="选择社区"
              style={{ width: '100%' }}
              allowClear
              value={communityFilter}
              onChange={(val) => setCommunityFilter(val)}
              options={communities.map((c) => ({ label: c.name, value: c.id }))}
            />
          </Col>
          <Col>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={fetchElders}>刷新</Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>重置</Button>
              {queueFilter === 'reassessment_due' && (
                <Button onClick={clearQueueFilter}>取消待复评筛选</Button>
              )}
              <Button icon={<LinkOutlined />} onClick={openBindModal}>家属绑定管理</Button>
            </Space>
          </Col>
        </Row>

        {queueFilter === 'reassessment_due' && (
          <div style={{ marginBottom: 12 }}>
            <Tag color="gold">当前为工作台跳转：待复评队列</Tag>
          </div>
        )}

        <Table
          columns={columns}
          dataSource={filteredRows}
          rowKey="id"
          loading={loading}
          scroll={{ x: 980 }}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条记录` }}
        />
      </Card>

      <Modal
        title="家属绑定管理"
        open={bindModalOpen}
        onCancel={() => setBindModalOpen(false)}
        footer={null}
        width={980}
      >
        <Card size="small" style={{ marginBottom: 12 }}>
          <Form form={bindForm} layout="inline">
            <Form.Item name="elder_id" rules={[{ required: true, message: '请选择老人' }]}>
              <Select
                style={{ width: 190 }}
                placeholder="选择老人"
                options={elders.map((item) => ({ label: item.name, value: item.id }))}
              />
            </Form.Item>
            <Form.Item name="family_id" rules={[{ required: true, message: '请选择家属' }]}>
              <Select
                style={{ width: 190 }}
                placeholder="选择家属"
                options={families.map((item) => ({ label: item.name, value: item.id }))}
              />
            </Form.Item>
            <Form.Item name="relationship" initialValue="daughter" rules={[{ required: true, message: '请输入关系' }]}>
              <Input style={{ width: 150 }} placeholder="daughter/son/spouse" />
            </Form.Item>
            <Form.Item name="notify_level" initialValue={1}>
              <Select
                style={{ width: 140 }}
                options={[
                  { label: '全部提醒', value: 1 },
                  { label: '高风险提醒', value: 2 },
                  { label: '不提醒', value: 3 },
                ]}
              />
            </Form.Item>
            <Form.Item>
              <Button type="primary" onClick={handleCreateRelation}>新增绑定</Button>
            </Form.Item>
          </Form>
        </Card>

        <Table
          size="small"
          rowKey="id"
          loading={relationLoading}
          columns={relationColumns}
          dataSource={relations}
          pagination={{ pageSize: 8 }}
        />
      </Modal>
    </div>
  )
}
