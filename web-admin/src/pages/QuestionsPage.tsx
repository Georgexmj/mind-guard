import { useEffect, useState, useCallback } from 'react'
import {
  Card, Table, Button, Space, Typography, Tag, Modal, Form,
  Input, Select, InputNumber, Row, Col, Tooltip, Switch, message,
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { getQuestions, createQuestion } from '../services/api'

const { Title, Text } = Typography
const { TextArea } = Input

interface Question {
  id: number
  domain: string
  q_type: string
  content: string
  options?: string[]
  difficulty: number
  is_active?: boolean
}

const DOMAIN_OPTIONS = [
  { label: '记忆力', value: 'memory' },
  { label: '定向力', value: 'orientation' },
  { label: '注意力', value: 'attention' },
  { label: '语言能力', value: 'language' },
  { label: '视空间', value: 'visuospatial' },
  { label: '执行功能', value: 'executive' },
]

const TYPE_OPTIONS = [
  { label: '选择题', value: 'choice' },
  { label: '语音题', value: 'voice' },
  { label: '绘图题', value: 'drawing' },
  { label: '量表题', value: 'scale' },
]

const domainColors: Record<string, string> = {
  memory: 'purple', orientation: 'blue', attention: 'orange',
  language: 'green', visuospatial: 'cyan', executive: 'red',
}

const typeColors: Record<string, string> = {
  choice: 'blue', voice: 'pink', drawing: 'geekblue', scale: 'gold',
}

const MOCK_QUESTIONS: Question[] = [
  { id: 1, domain: 'memory', q_type: 'choice', content: '请记住以下三个词：苹果、汽车、诚实。现在，请问您刚才记忆的第一个词是什么？', options: ['苹果', '香蕉', '桌子', '书本'], difficulty: 0.3, is_active: true },
  { id: 2, domain: 'memory', q_type: 'choice', content: '几分钟前您记忆了三个词。请问第二个词是什么？', options: ['汽车', '飞机', '自行车', '火车'], difficulty: 0.5, is_active: true },
  { id: 3, domain: 'memory', q_type: 'voice', content: '请回忆并说出之前记忆的第三个词。', difficulty: 0.6, is_active: true },
  { id: 4, domain: 'orientation', q_type: 'choice', content: '现在是哪一年？', options: ['2024年', '2025年', '2026年', '2023年'], difficulty: 0.2, is_active: true },
  { id: 5, domain: 'orientation', q_type: 'voice', content: '请问您现在在哪个城市？', difficulty: 0.2, is_active: true },
  { id: 6, domain: 'attention', q_type: 'choice', content: '请从100开始，每次减7，第一次结果是多少？', options: ['93', '97', '91', '95'], difficulty: 0.5, is_active: true },
  { id: 7, domain: 'language', q_type: 'voice', content: '请用一句话描述：一位老奶奶在公园里喂鸽子。', difficulty: 0.5, is_active: true },
  { id: 8, domain: 'visuospatial', q_type: 'drawing', content: '请画一个时钟，显示时间为11点10分。', difficulty: 0.7, is_active: true },
  { id: 9, domain: 'executive', q_type: 'voice', content: '如果您在街上发现了一封已贴好邮票的信，您会怎么做？', difficulty: 0.6, is_active: true },
  { id: 10, domain: 'attention', q_type: 'scale', content: '请评估您在过去一周内注意力集中程度（0=完全无法集中，10=完全可以集中）。', difficulty: 0.4, is_active: true },
]

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>(MOCK_QUESTIONS)
  const [loading, setLoading] = useState(false)
  const [domainFilter, setDomainFilter] = useState<string | undefined>()
  const [typeFilter, setTypeFilter] = useState<string | undefined>()
  const [modalOpen, setModalOpen] = useState(false)
  const [optionCount, setOptionCount] = useState(4)
  const [form] = Form.useForm()

  const qType = Form.useWatch('q_type', form)

  const fetchQuestions = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getQuestions({ domain: domainFilter, q_type: typeFilter })
      if (Array.isArray(res) && res.length > 0) setQuestions(res as Question[])
    } catch {
      // keep mock data
    } finally {
      setLoading(false)
    }
  }, [domainFilter, typeFilter])

  useEffect(() => { fetchQuestions() }, [fetchQuestions])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      // Build options array from option_0..option_N fields
      const options = qType === 'choice'
        ? Array.from({ length: optionCount }, (_, i) => values[`option_${i}`]).filter(Boolean)
        : undefined
      const payload = {
        domain: values.domain,
        q_type: values.q_type,
        content: values.content,
        options,
        correct_answer: values.correct_answer,
        difficulty: values.difficulty ?? 0.5,
        irt_a: 1.0,
        irt_b: 0.0,
      }
      await createQuestion(payload)
      message.success('题目创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchQuestions()
    } catch {
      // keep modal open on error
    }
  }

  const columns: ColumnsType<Question> = [
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text) => <Tooltip title={text}><Text style={{ maxWidth: 340, display: 'block' }} ellipsis>{text}</Text></Tooltip>,
    },
    {
      title: '认知域',
      dataIndex: 'domain',
      key: 'domain',
      width: 100,
      align: 'center',
      render: (d) => {
        const opt = DOMAIN_OPTIONS.find((o) => o.value === d)
        return <Tag color={domainColors[d] || 'default'} style={{ borderRadius: 10 }}>{opt?.label || d}</Tag>
      },
    },
    {
      title: '题型',
      dataIndex: 'q_type',
      key: 'q_type',
      width: 90,
      align: 'center',
      render: (t) => {
        const opt = TYPE_OPTIONS.find((o) => o.value === t)
        return <Tag color={typeColors[t] || 'default'} style={{ borderRadius: 10 }}>{opt?.label || t}</Tag>
      },
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 80,
      align: 'center',
      render: (d) => (
        <Tag color={d >= 0.7 ? 'red' : d >= 0.4 ? 'orange' : 'green'} style={{ borderRadius: 10 }}>
          {d >= 0.7 ? '难' : d >= 0.4 ? '中' : '易'}
        </Tag>
      ),
    },
    {
      title: '启用',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 70,
      align: 'center',
      render: (active) => <Switch checked={active ?? true} size="small" disabled />,
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#1a1a2e' }}>题库管理</Title>
        <Text type="secondary">共 {questions.length} 道题目（含各认知域）</Text>
      </div>

      <Card
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={6}>
            <Select
              placeholder="筛选认知域"
              allowClear
              style={{ width: '100%' }}
              value={domainFilter}
              onChange={setDomainFilter}
              options={DOMAIN_OPTIONS}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Select
              placeholder="筛选题型"
              allowClear
              style={{ width: '100%' }}
              value={typeFilter}
              onChange={setTypeFilter}
              options={TYPE_OPTIONS}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchQuestions}>刷新</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setModalOpen(true) }}>
                新增题目
              </Button>
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={questions}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15, showTotal: (t) => `共 ${t} 道题` }}
        />
      </Card>

      <Modal
        title="新增题目"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        okText="创建"
        cancelText="取消"
        width={640}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="domain" label="认知域" rules={[{ required: true }]}>
                <Select options={DOMAIN_OPTIONS} placeholder="选择认知域" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="q_type" label="题型" rules={[{ required: true }]}>
                <Select options={TYPE_OPTIONS} placeholder="选择题型" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="content" label="题目内容" rules={[{ required: true, message: '请输入题目内容' }]}>
            <TextArea rows={3} placeholder="输入题目文本..." />
          </Form.Item>
          {qType === 'choice' && (
            <>
              <Form.Item label={`选项（${optionCount} 个）`}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {Array.from({ length: optionCount }, (_, i) => (
                    <Form.Item key={i} name={`option_${i}`} noStyle>
                      <Input prefix={<Text style={{ color: '#999' }}>{String.fromCharCode(65 + i)}.</Text>} placeholder={`选项 ${String.fromCharCode(65 + i)}`} />
                    </Form.Item>
                  ))}
                </Space>
                <Button type="dashed" size="small" style={{ marginTop: 8 }} onClick={() => setOptionCount((n) => Math.min(n + 1, 6))}>+ 添加选项</Button>
              </Form.Item>
              <Form.Item name="correct_answer" label="正确答案">
                <Input placeholder="输入正确答案的文字内容" />
              </Form.Item>
            </>
          )}
          <Form.Item name="difficulty" label="难度系数">
            <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} placeholder="0.0 ~ 1.0（0=最易，1=最难）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
