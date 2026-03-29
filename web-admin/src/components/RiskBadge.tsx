import { Tag } from 'antd'
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons'

interface RiskBadgeProps {
  riskLevel: 'normal' | 'mild_risk' | 'high_risk'
  size?: 'default' | 'large'
}

const riskConfig = {
  normal: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    text: '正常',
    hexColor: '#52c41a',
  },
  mild_risk: {
    color: 'warning',
    icon: <WarningOutlined />,
    text: '轻度风险',
    hexColor: '#faad14',
  },
  high_risk: {
    color: 'error',
    icon: <CloseCircleOutlined />,
    text: '高风险',
    hexColor: '#ff4d4f',
  },
}

export default function RiskBadge({ riskLevel, size = 'default' }: RiskBadgeProps) {
  const config = riskConfig[riskLevel] || riskConfig.normal

  if (size === 'large') {
    return (
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 20px',
          borderRadius: 24,
          background: `${config.hexColor}18`,
          border: `2px solid ${config.hexColor}`,
          color: config.hexColor,
          fontWeight: 700,
          fontSize: 18,
        }}
      >
        {config.icon}
        <span>{config.text}</span>
      </div>
    )
  }

  return (
    <Tag
      color={config.color}
      icon={config.icon}
      style={{ fontWeight: 500, borderRadius: 12, padding: '0 10px' }}
    >
      {config.text}
    </Tag>
  )
}
