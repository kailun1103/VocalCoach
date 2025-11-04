import { Route, Routes, NavLink } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import LanguageSwitcher from './components/LanguageSwitcher'
import { useTranslation } from 'react-i18next'

function Nav() {
  const { t } = useTranslation()
  const linkBase = 'px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800'
  const linkActive = 'bg-gray-200 dark:bg-gray-700'
  return (
    <nav className="border-b border-gray-200 dark:border-gray-800">
      <div className="container-max flex h-14 items-center justify-between">
        <div className="flex items-center gap-2 font-semibold">EnglishTalk</div>
        <div className="flex items-center gap-2">
          <NavLink to="/" end className={({ isActive }) => `${linkBase} ${isActive ? linkActive : ''}`}>{t('nav.chat')}</NavLink>
          <LanguageSwitcher />
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <div className="min-h-full">
      <Nav />
      <main className="container-max py-4">
        <Routes>
          <Route path="/" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  )
}
