import { Tag } from 'antd'
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons'

interface RiskBadgeProps {
  riskLevel: 'normal' | 'mild_risk' | 'moderate_risk' | 'high_risk'
  size?: 'default' | 'large'
}

const riskConfig = {
  normal: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    text: '正常',
    hexColor: '#16a34a',
  },
  mild_risk: {
    color: 'warning',
    icon: <WarningOutlined />,
    text: '轻度风险',
    hexColor: '#d97706',
  },
  moderate_risk: {
    color: 'warning',
    icon: <WarningOutlined />,
    text: '中度风险',
    hexColor: '#ea580c',
  },
  high_risk: {
    color: 'error',
    icon: <CloseCircleOutlined />,
    text: '高风险',
    hexColor: '#dc2626',
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
          background: `${config.hexColor}14`,
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
      style={{ fontWeight: 600, borderRadius: 12, padding: '2px 10px' }}
    >
      {config.text}
    </Tag>
  )
}
