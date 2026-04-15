import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App'
import './styles/global.css'

dayjs.locale('zh-cn')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#0f766e',
          colorSuccess: '#16a34a',
          colorWarning: '#d97706',
          colorError: '#dc2626',
          colorTextBase: '#112231',
          colorBgBase: '#f4f8fb',
          borderRadius: 14,
          fontFamily: "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
        components: {
          Layout: {
            bodyBg: 'transparent',
            headerBg: 'transparent',
            siderBg: 'transparent',
          },
          Card: {
            borderRadiusLG: 20,
          },
          Button: {
            borderRadius: 12,
            controlHeight: 42,
            fontWeight: 600,
          },
          Menu: {
            itemBorderRadius: 12,
            itemHeight: 46,
            itemSelectedBg: 'rgba(15, 118, 110, 0.16)',
            itemSelectedColor: '#c8f6ee',
            itemColor: '#d5e1ee',
            darkItemBg: 'transparent',
            darkItemColor: '#d5e1ee',
            darkItemHoverBg: 'rgba(255,255,255,0.09)',
          },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
)
