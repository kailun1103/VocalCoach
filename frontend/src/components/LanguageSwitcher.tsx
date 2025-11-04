import { useTranslation } from 'react-i18next'
import { useSettings } from '../modules/settings/SettingsContext'

/** Toggle the interface language between English and Traditional Chinese. */
export default function LanguageSwitcher() {
  const { i18n } = useTranslation()
  const { language, setLanguage } = useSettings()

  const toggle = () => {
    const next = language === 'zh' ? 'en' : 'zh'
    setLanguage(next)
    i18n.changeLanguage(next)
    document.documentElement.lang = next
  }

  return (
    <button className="px-2 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-700" onClick={toggle}>
      {language === 'zh' ? '中文' : 'EN'}
    </button>
  )
}

