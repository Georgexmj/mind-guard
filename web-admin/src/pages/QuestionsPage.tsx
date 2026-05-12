import { useCallback, useEffect, useState } from 'react'
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd'
import {
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

import {
  createQuestion,
  deleteQuestion,
  exportQuestionsCsv,
  getQuestions,
  updateQuestion,
} from '../services/api'
import type { User } from '../types'

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

interface Question {
  id: number
  domain: string
  q_type: 'choice' | 'voice' | 'drawing' | 'scale' | string
  content: string
  options?: string[]
  correct_answer?: string
  difficulty: number
  is_active?: boolean
}

interface QuestionFormValues {
  domain: string
  q_type: string
  content: string
  correct_answer?: string
  difficulty?: number
  is_active?: boolean
  [key: string]: any
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

const DOMAIN_COLORS: Record<string, string> = {
  memory: 'purple',
  orientation: 'blue',
  attention: 'orange',
  language: 'green',
  visuospatial: 'cyan',
  executive: 'red',
}

const TYPE_COLORS: Record<string, string> = {
  choice: 'blue',
  voice: 'magenta',
  drawing: 'geekblue',
  scale: 'gold',
}

export default function QuestionsPage() {
  const user = getUserFromStorage()
  const canManageQuestions = user?.role === 'admin'

  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)

  const [domainFilter, setDomainFilter] = useState<string>()
  const [typeFilter, setTypeFilter] = useState<string>()

  const [modalOpen, setModalOpen] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null)
  const [optionCount, setOptionCount] = useState(4)

  const [form] = Form.useForm<QuestionFormValues>()
  const qType = Form.useWatch('q_type', form)

  const fetchQuestions = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getQuestions({
        domain: domainFilter,
        q_type: typeFilter,
        page_size: 200,
      })
      setQuestions((Array.isArray(data) ? data : []) as Question[])
    } catch {
      message.error('题库加载失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [domainFilter, typeFilter])

  useEffect(() => {
    void fetchQuestions()
  }, [fetchQuestions])

  const handleExport = async () => {
    setExporting(true)
    try {
      const { blob, filename } = await exportQuestionsCsv({
        domain: domainFilter,
        q_type: typeFilter,
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || 'mindguard_questions.csv'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch {
      message.error('导出失败，请稍后重试')
    } finally {
      setExporting(false)
    }
  }

  const openCreateModal = () => {
    setEditingQuestion(null)
    setOptionCount(4)
    form.resetFields()
    form.setFieldsValue({
      q_type: 'choice',
      difficulty: 0.5,
      is_active: true,
    })
    setModalOpen(true)
  }

  const openEditModal = (question: Question) => {
    setEditingQuestion(question)
    const nextOptionCount = Math.max(question.options?.length || 0, 4)
    setOptionCount(nextOptionCount)

    const initialValues: QuestionFormValues = {
      domain: question.domain,
      q_type: question.q_type,
      content: question.content,
      correct_answer: question.correct_answer,
      difficulty: question.difficulty,
      is_active: question.is_active ?? true,
    }

    for (let i = 0; i < nextOptionCount; i += 1) {
      initialValues[`option_${i}`] = question.options?.[i] || ''
    }

    form.setFieldsValue(initialValues)
    setModalOpen(true)
  }

  const buildChoiceOptions = (values: QuestionFormValues): string[] => {
    return Array.from({ length: optionCount }, (_, i) => values[`option_${i}`])
      .map((item) => (typeof item === 'string' ? item.trim() : ''))
      .filter(Boolean)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const isChoice = values.q_type === 'choice'
      const options = isChoice ? buildChoiceOptions(values) : undefined

      if (isChoice && (!options || options.length < 2)) {
        message.error('选择题至少需要 2 个选项')
        return
      }

      const payload: Record<string, unknown> = {
        domain: values.domain,
        q_type: values.q_type,
        content: values.content?.trim(),
        difficulty: values.difficulty ?? 0.5,
        is_active: values.is_active ?? true,
        options,
        correct_answer: isChoice ? values.correct_answer?.trim() : undefined,
      }

      if (editingQuestion) {
        await updateQuestion(editingQuestion.id, payload)
        message.success('题目更新成功')
      } else {
        await createQuestion({
          ...payload,
          irt_a: 1.0,
          irt_b: 0.0,
        })
        message.success('题目创建成功')
      }

      setModalOpen(false)
      setEditingQuestion(null)
      form.resetFields()
      void fetchQuestions()
    } catch {
      message.error('保存失败，请检查输入后重试')
    }
  }

  const handleDelete = (question: Question) => {
    Modal.confirm({
      title: '删除题目',
      icon: <ExclamationCircleOutlined />,
      content: `确认停用题目“${question.content.slice(0, 24)}${question.content.length > 24 ? '...' : ''}”吗？`,
      okText: '确认删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteQuestion(question.id)
          message.success('题目已停用')
          void fetchQuestions()
        } catch {
          message.error('删除失败，请稍后重试')
        }
      },
    })
  }

  const columns: ColumnsType<Question> = [
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (value: string) => (
        <Tooltip title={value}>
          <Text style={{ maxWidth: 380, display: 'block' }} ellipsis>
            {value}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '认知域',
      dataIndex: 'domain',
      key: 'domain',
      width: 110,
      align: 'center',
      render: (value: string) => {
        const label = DOMAIN_OPTIONS.find((item) => item.value === value)?.label || value
        return (
          <Tag color={DOMAIN_COLORS[value] || 'default'} style={{ borderRadius: 10 }}>
            {label}
          </Tag>
        )
      },
    },
    {
      title: '题型',
      dataIndex: 'q_type',
      key: 'q_type',
      width: 100,
      align: 'center',
      render: (value: string) => {
        const label = TYPE_OPTIONS.find((item) => item.value === value)?.label || value
        return (
          <Tag color={TYPE_COLORS[value] || 'default'} style={{ borderRadius: 10 }}>
            {label}
          </Tag>
        )
      },
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 90,
      align: 'center',
      render: (value: number) => (
        <Tag color={value >= 0.7 ? 'red' : value >= 0.4 ? 'orange' : 'green'} style={{ borderRadius: 10 }}>
          {value >= 0.7 ? '高' : value >= 0.4 ? '中' : '低'}
        </Tag>
      ),
    },
    {
      title: '启用',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      align: 'center',
      render: (value?: boolean) => <Switch checked={value ?? true} size="small" disabled />,
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      align: 'center',
      render: (_, record) => (
        <Space size={6}>
          {canManageQuestions && (
            <Tooltip title="编辑">
              <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} />
            </Tooltip>
          )}
          {canManageQuestions && (
            <Tooltip title="删除">
              <Button type="text" danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(record)} />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="mg-page">
      <div className="mg-page-header">
        <div>
          <Title level={4} className="mg-page-title">
            题库管理
          </Title>
          <Text className="mg-page-subtitle">
            {canManageQuestions ? '管理员可新增、编辑、停用题目，医生仅可查看。' : '当前角色仅可查看题库。'}
          </Text>
        </div>
      </div>

      <Card className="mg-panel-card" styles={{ body: { padding: '20px 24px' } }}>
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
              <Button icon={<DownloadOutlined />} loading={exporting} onClick={handleExport}>
                导出 CSV
              </Button>
              <Button icon={<ReloadOutlined />} onClick={() => void fetchQuestions()}>
                刷新
              </Button>
              {canManageQuestions && (
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
                  新增题目
                </Button>
              )}
            </Space>
          </Col>
        </Row>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={questions}
          loading={loading}
          pagination={{ pageSize: 15, showTotal: (total) => `共 ${total} 道题` }}
        />
      </Card>

      {canManageQuestions && (
        <Modal
          open={modalOpen}
          title={editingQuestion ? '编辑题目' : '新增题目'}
          okText={editingQuestion ? '保存' : '创建'}
          cancelText="取消"
          onOk={() => void handleSubmit()}
          onCancel={() => {
            setModalOpen(false)
            setEditingQuestion(null)
          }}
          width={680}
          destroyOnClose
        >
          <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
            <Row gutter={12}>
              <Col span={12}>
                <Form.Item name="domain" label="认知域" rules={[{ required: true, message: '请选择认知域' }]}>
                  <Select options={DOMAIN_OPTIONS} placeholder="请选择认知域" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="q_type" label="题型" rules={[{ required: true, message: '请选择题型' }]}>
                  <Select options={TYPE_OPTIONS} placeholder="请选择题型" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="content" label="题目内容" rules={[{ required: true, message: '请输入题目内容' }]}>
              <TextArea rows={3} placeholder="请输入题目文本" />
            </Form.Item>

            {qType === 'choice' && (
              <>
                <Form.Item label={`选项（${optionCount} 个）`}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {Array.from({ length: optionCount }, (_, i) => (
                      <Form.Item
                        key={i}
                        name={`option_${i}`}
                        rules={i < 2 ? [{ required: true, message: '前两个选项必填' }] : undefined}
                        style={{ marginBottom: 8 }}
                      >
                        <Input
                          prefix={<Text style={{ color: '#999' }}>{String.fromCharCode(65 + i)}.</Text>}
                          placeholder={`选项 ${String.fromCharCode(65 + i)}`}
                        />
                      </Form.Item>
                    ))}
                  </Space>
                  <Button
                    type="dashed"
                    size="small"
                    style={{ marginTop: 8 }}
                    onClick={() => setOptionCount((count) => Math.min(count + 1, 8))}
                  >
                    + 添加选项
                  </Button>
                </Form.Item>
                <Form.Item name="correct_answer" label="正确答案">
                  <Input placeholder="请输入正确答案文本（需与选项内容一致）" />
                </Form.Item>
              </>
            )}

            <Form.Item name="difficulty" label="难度系数">
              <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item name="is_active" label="是否启用" valuePropName="checked" initialValue={true}>
              <Switch />
            </Form.Item>
          </Form>
        </Modal>
      )}
    </div>
  )
}
