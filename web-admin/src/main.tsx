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
          colorPrimary: '#f08c2e',
          colorSuccess: '#20a36b',
          colorWarning: '#ea8c2b',
          colorError: '#dc3a2f',
          colorTextBase: '#172033',
          colorBgBase: '#f4f6fb',
          borderRadius: 10,
          fontFamily: "'Outfit', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
        components: {
          Layout: {
            bodyBg: 'transparent',
            headerBg: 'transparent',
            siderBg: 'transparent',
          },
          Card: {
            borderRadiusLG: 14,
          },
          Button: {
            borderRadius: 10,
            controlHeight: 40,
            fontWeight: 600,
          },
          Menu: {
            itemBorderRadius: 10,
            itemHeight: 42,
            itemSelectedBg: '#fff4e8',
            itemSelectedColor: '#de7b1d',
            itemColor: '#47536a',
          },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
)
