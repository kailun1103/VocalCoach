/**
 * 主應用程式組件
 * 
 * 提供應用程式的主要結構，包括導覽列和路由配置。
 */

import { Route, Routes, NavLink } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import LanguageSwitcher from './components/LanguageSwitcher'
import { useTranslation } from 'react-i18next'

/**
 * 導覽列組件
 * 
 * 顯示應用程式標題、導覽連結和語言切換器。
 */
function Nav() {
  const { t } = useTranslation()
  
  // 導覽連結的基本樣式
  const linkBase = 'px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800'
  // 啟用狀態的樣式
  const linkActive = 'bg-gray-200 dark:bg-gray-700'
  
  return (
    <nav className="border-b border-gray-200 dark:border-gray-800">
      <div className="container-max flex h-14 items-center justify-between">
        {/* 應用程式標題 */}
        <div className="flex items-center gap-2 font-semibold">EnglishTalk</div>
        
        {/* 導覽連結和工具 */}
        <div className="flex items-center gap-2">
          <NavLink 
            to="/" 
            end 
            className={({ isActive }) => `${linkBase} ${isActive ? linkActive : ''}`}
          >
            {t('nav.chat')}
          </NavLink>
          <LanguageSwitcher />
        </div>
      </div>
    </nav>
  )
}

/**
 * 主應用程式組件
 * 
 * 設置應用程式的整體佈局和路由結構。
 */
export default function App() {
  return (
    <div className="min-h-full">
      {/* 導覽列 */}
      <Nav />
      
      {/* 主要內容區域 */}
      <main className="container-max py-4">
        <Routes>
          {/* 聊天頁面路由 */}
          <Route path="/" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  )
}
