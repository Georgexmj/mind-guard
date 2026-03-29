import { useEffect, useState, useCallback } from 'react'
import {
  Card,
  Table,
  Input,
  Select,
  Button,
  Space,
  Typography,
  Avatar,
  Tooltip,
  Row,
  Col,
  Tag,
} from 'antd'
import {
  SearchOutlined,
  UserOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { getElders, getCommunities } from '../services/api'
import type { User, Community } from '../types'
import RiskBadge from '../components/RiskBadge'

const { Title, Text } = Typography

// Extended type to include display fields
type ElderRow = User & {
  community_name?: string
  last_assessment?: string
  risk_level?: 'normal' | 'mild_risk' | 'high_risk'
}

const educationLabel = (years?: number): string => {
  if (years == null) return '未填写'
  if (years <= 6) return '小学'
  if (years <= 9) return '初中'
  if (years <= 12) return '高中'
  if (years <= 15) return '大专'
  return '本科及以上'
}

// Mock fallback data
const MOCK_ELDERS: ElderRow[] = [
  { id: 1, uuid: 'u1', name: '王秀兰', phone: '138****0001', role: 'elder', community_id: 1, created_at: '2024-01-10', birth_date: '1948-03-15', gender: 'female', education_years: 6, community_name: '幸福社区', last_assessment: '2024-03-20', risk_level: 'normal' },
  { id: 2, uuid: 'u2', name: '李德明', phone: '139****0002', role: 'elder', community_id: 1, created_at: '2024-01-12', birth_date: '1945-07-22', gender: 'male', education_years: 9, community_name: '幸福社区', last_assessment: '2024-03-18', risk_level: 'mild_risk' },
  { id: 3, uuid: 'u3', name: '张桂珍', phone: '136****0003', role: 'elder', community_id: 2, created_at: '2024-01-15', birth_date: '1950-11-08', gender: 'female', education_years: 12, community_name: '阳光社区', last_assessment: '2024-03-22', risk_level: 'normal' },
  { id: 4, uuid: 'u4', name: '陈福寿', phone: '137****0004', role: 'elder', community_id: 2, created_at: '2024-01-20', birth_date: '1942-05-30', gender: 'male', education_years: 6, community_name: '阳光社区', last_assessment: '2024-03-15', risk_level: 'high_risk' },
  { id: 5, uuid: 'u5', name: '刘淑华', phone: '135****0005', role: 'elder', community_id: 3, created_at: '2024-02-01', birth_date: '1952-09-12', gender: 'female', education_years: 15, community_name: '和谐社区', last_assessment: '2024-03-21', risk_level: 'normal' },
  { id: 6, uuid: 'u6', name: '赵建国', phone: '132****0006', role: 'elder', community_id: 3, created_at: '2024-02-05', birth_date: '1947-12-01', gender: 'male', education_years: 12, community_name: '和谐社区', last_assessment: '2024-03-19', risk_level: 'mild_risk' },
  { id: 7, uuid: 'u7', name: '周金凤', phone: '133****0007', role: 'elder', community_id: 1, created_at: '2024-02-10', birth_date: '1955-04-18', gender: 'female', education_years: 15, community_name: '幸福社区', last_assessment: '2024-03-22', risk_level: 'normal' },
  { id: 8, uuid: 'u8', name: '吴永祥', phone: '134****0008', role: 'elder', community_id: 2, created_at: '2024-02-15', birth_date: '1940-08-25', gender: 'male', education_years: 6, community_name: '阳光社区', last_assessment: undefined, risk_level: undefined },
  { id: 9, uuid: 'u9', name: '孙美英', phone: '131****0009', role: 'elder', community_id: 1, created_at: '2024-02-20', birth_date: '1953-02-14', gender: 'female', education_years: 9, community_name: '幸福社区', last_assessment: '2024-03-17', risk_level: 'high_risk' },
  { id: 10, uuid: 'u10', name: '胡长寿', phone: '130****0010', role: 'elder', community_id: 3, created_at: '2024-03-01', birth_date: '1944-06-07', gender: 'male', education_years: 9, community_name: '和谐社区', last_assessment: '2024-03-20', risk_level: 'normal' },
]

const calculateAge = (birthDate?: string): number | string => {
  if (!birthDate) return '-'
  return dayjs().diff(dayjs(birthDate), 'year')
}

const genderMap: Record<string, string> = { male: '男', female: '女' }

export default function EldersPage() {
  const [elders, setElders] = useState<ElderRow[]>(MOCK_ELDERS)
  const [communities, setCommunities] = useState<Community[]>([])
  const [loading, setLoading] = useState(false)
  const [searchName, setSearchName] = useState('')
  const [communityFilter, setCommunityFilter] = useState<number | undefined>()
  const [total, setTotal] = useState(MOCK_ELDERS.length)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const navigate = useNavigate()

  const fetchElders = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getElders({
        page,
        page_size: pageSize,
        community_id: communityFilter,
      })
      if (Array.isArray(res) && res.length > 0) {
        setElders(res as ElderRow[])
        setTotal(res.length)
      }
    } catch {
      // Use mock data on failure
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, communityFilter])

  const fetchCommunities = useCallback(async () => {
    try {
      const res = await getCommunities()
      setCommunities(res)
    } catch {
      setCommunities([
        { id: 1, name: '幸福社区', province: '湖南省', city: '张家界市' },
        { id: 2, name: '阳光社区', province: '湖南省', city: '张家界市' },
        { id: 3, name: '和谐社区', province: '湖南省', city: '张家界市' },
      ])
    }
  }, [])

  useEffect(() => {
    fetchCommunities()
  }, [fetchCommunities])

  useEffect(() => {
    fetchElders()
  }, [fetchElders])

  const handleSearch = () => {
    setPage(1)
  }

  const handleReset = () => {
    setSearchName('')
    setCommunityFilter(undefined)
    setPage(1)
  }

  const columns: ColumnsType<ElderRow> = [
    {
      title: '老人信息',
      key: 'info',
      width: 200,
      render: (_, record) => (
        <Space>
          <Avatar
            style={{
              background: record.gender === 'female' ? '#ffadd2' : '#bae0ff',
              color: record.gender === 'female' ? '#c41d7f' : '#0958d9',
              fontWeight: 700,
            }}
            size={36}
          >
            {record.name?.[0] || '?'}
          </Avatar>
          <div>
            <div style={{ fontWeight: 600, color: '#1a1a2e' }}>{record.name}</div>
            <div style={{ fontSize: 12, color: '#999' }}>
              {genderMap[record.gender || ''] || '-'} · {record.phone || '-'}
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '年龄',
      dataIndex: 'birth_date',
      key: 'age',
      width: 80,
      align: 'center',
      render: (birthDate) => (
        <Text>{calculateAge(birthDate)} {birthDate ? '岁' : ''}</Text>
      ),
    },
    {
      title: '文化程度',
      dataIndex: 'education_years',
      key: 'education',
      width: 100,
      align: 'center',
      render: (years) => <Tag color="blue" style={{ borderRadius: 10 }}>{educationLabel(years)}</Tag>,
    },
    {
      title: '所属社区',
      dataIndex: 'community_name',
      key: 'community',
      width: 140,
      render: (name) => (
        <Space>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#1677ff',
              display: 'inline-block',
            }}
          />
          {name || '-'}
        </Space>
      ),
    },
    {
      title: '最近评估',
      dataIndex: 'last_assessment',
      key: 'last_assessment',
      width: 130,
      align: 'center',
      render: (date) =>
        date ? (
          <Tooltip title={dayjs(date).format('YYYY-MM-DD')}>
            <Text style={{ fontSize: 13 }}>{dayjs(date).fromNow?.() || dayjs(date).format('MM-DD')}</Text>
          </Tooltip>
        ) : (
          <Text type="secondary">暂无记录</Text>
        ),
    },
    {
      title: '风险状态',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 120,
      align: 'center',
      render: (riskLevel) =>
        riskLevel ? (
          <RiskBadge riskLevel={riskLevel} />
        ) : (
          <Tag color="default" style={{ borderRadius: 10 }}>未评估</Tag>
        ),
    },
    {
      title: '加入时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 110,
      align: 'center',
      render: (date) => <Text style={{ fontSize: 12, color: '#999' }}>{dayjs(date).format('YYYY-MM-DD')}</Text>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      align: 'center',
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/elders/${record.id}`)}
          style={{ padding: 0 }}
        >
          查看详情
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>老人管理</Title>
        <Text type="secondary">共 {total} 位注册老人</Text>
      </div>

      <Card
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        {/* Filter Bar */}
        <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="搜索老人姓名"
              prefix={<SearchOutlined style={{ color: '#bbb' }} />}
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
              style={{ borderRadius: 8 }}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="选择社区"
              style={{ width: '100%', borderRadius: 8 }}
              allowClear
              value={communityFilter}
              onChange={(val) => setCommunityFilter(val)}
              options={communities.map((c) => ({ label: c.name, value: c.id }))}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Space>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleSearch}
                style={{ borderRadius: 8 }}
              >
                搜索
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={handleReset}
                style={{ borderRadius: 8 }}
              >
                重置
              </Button>
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={elders}
          rowKey="id"
          loading={loading}
          scroll={{ x: 900 }}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p) => setPage(p),
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条记录`,
            style: { marginBottom: 0 },
          }}
          rowClassName={() => 'table-row-hover'}
          style={{ borderRadius: 8, overflow: 'hidden' }}
        />
      </Card>
    </div>
  )
}
