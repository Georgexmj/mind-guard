import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Badge,
  Button,
  Card,
  Empty,
  List,
  Segmented,
  Space,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  BellOutlined,
  CheckOutlined,
  EyeOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'

import {
  getNotificationUnreadCount,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../services/api'
import type { NotificationItem } from '../types'

const { Title, Text } = Typography

type FilterType = 'all' | 'unread' | 'high_risk_alert' | 'assessment_completed'

const typeLabel: Record<NotificationItem['notification_type'], string> = {
  assessment_completed: '评估完成',
  high_risk_alert: '高危预警',
  system_message: '系统消息',
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [items, setItems] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [filter, setFilter] = useState<FilterType>('all')

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [list, unread] = await Promise.all([
        getNotifications(
          filter === 'all'
            ? {}
            : filter === 'unread'
              ? { unread_only: true }
              : { type: filter },
        ),
        getNotificationUnreadCount(),
      ])
      setItems(list)
      setUnreadCount(unread)
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => {
    void fetchData()
  }, [fetchData])

  const highRiskCount = useMemo(
    () => items.filter((item) => item.notification_type === 'high_risk_alert').length,
    [items],
  )

  const handleMarkRead = async (item: NotificationItem) => {
    if (item.is_read) return
    await markNotificationRead(item.id)
    message.success('已标记为已读')
    void fetchData()
  }

  const handleMarkAllRead = async () => {
    const count = await markAllNotificationsRead()
    message.success(`已标记 ${count} 条通知为已读`)
    void fetchData()
  }

  return (
    <div className="mg-page">
      <div className="mg-page-header">
        <div>
          <Title level={4} className="mg-page-title">
            通知中心
          </Title>
          <Text className="mg-page-subtitle">查看评估完成与高危预警通知，支持一键已读处理</Text>
        </div>
      </div>

      <Card className="mg-panel-card" bodyStyle={{ padding: '14px 18px' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} wrap>
          <Space>
            <Badge count={unreadCount} overflowCount={99}>
              <Tag color="blue" style={{ borderRadius: 12, padding: '2px 10px' }}>
                未读通知
              </Tag>
            </Badge>
            <Tag color="red" style={{ borderRadius: 12, padding: '2px 10px' }}>
              高危预警 {highRiskCount}
            </Tag>
          </Space>
          <Space>
            <Segmented
              value={filter}
              onChange={(value) => setFilter(value as FilterType)}
              options={[
                { label: '全部', value: 'all' },
                { label: '未读', value: 'unread' },
                { label: '高危预警', value: 'high_risk_alert' },
                { label: '评估完成', value: 'assessment_completed' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={() => void fetchData()}>
              刷新
            </Button>
            <Button type="primary" icon={<CheckOutlined />} onClick={handleMarkAllRead}>
              全部已读
            </Button>
          </Space>
        </Space>
      </Card>

      <Card className="mg-panel-card">
        <List
          loading={loading}
          dataSource={items}
          locale={{ emptyText: <Empty description="暂无通知" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  key="read"
                  size="small"
                  disabled={item.is_read}
                  icon={<EyeOutlined />}
                  onClick={() => void handleMarkRead(item)}
                >
                  {item.is_read ? '已读' : '标记已读'}
                </Button>,
                item.session_id ? (
                  <Button
                    key="detail"
                    size="small"
                    type="link"
                    onClick={() => navigate(`/assessments/${item.session_id}`)}
                  >
                    查看评估
                  </Button>
                ) : null,
              ]}
            >
              <List.Item.Meta
                avatar={
                  item.notification_type === 'high_risk_alert' ? (
                    <WarningOutlined style={{ color: '#dc2626', fontSize: 18 }} />
                  ) : (
                    <BellOutlined style={{ color: '#0f766e', fontSize: 18 }} />
                  )
                }
                title={(
                  <Space>
                    <Text strong style={{ color: item.is_read ? '#8ca0ae' : '#163143' }}>
                      {item.title}
                    </Text>
                    <Tag color={item.notification_type === 'high_risk_alert' ? 'red' : 'blue'}>
                      {typeLabel[item.notification_type]}
                    </Tag>
                    {!item.is_read && <Badge status="processing" text="未读" />}
                  </Space>
                )}
                description={(
                  <div>
                    <Text type={item.is_read ? 'secondary' : undefined}>{item.content}</Text>
                    <div style={{ marginTop: 6 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}
                      </Text>
                    </div>
                  </div>
                )}
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  )
}
