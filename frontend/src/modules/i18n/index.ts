import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import zh from './locales/zh.json'

const saved = localStorage.getItem('settings:language') as 'en' | 'zh' | null
const lng = saved || (navigator.language.startsWith('zh') ? 'zh' : 'en')

// Initialise i18next once, feeding translations for both supported languages.
i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zh: { translation: zh },
    },
    lng,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  })

export default i18n
