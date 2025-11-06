/**
 * 應用程式入口點
 * 
 * 此檔案負責初始化 React 應用程式，設置全域提供者（Provider）
 * 包括路由、設定管理和國際化支援。
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles/index.css'
import './modules/i18n'
import { SettingsProvider } from './modules/settings/SettingsContext'

// 建立 React 根節點並渲染應用程式
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* 路由管理 */}
    <BrowserRouter>
      {/* 設定管理（API 端點、串流模式、語言偏好） */}
      <SettingsProvider>
        <App />
      </SettingsProvider>
    </BrowserRouter>
  </React.StrictMode>
)

