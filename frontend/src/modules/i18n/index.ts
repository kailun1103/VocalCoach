/**
 * 國際化（i18n）配置模組
 * 
 * 使用 i18next 提供多語言支援，
 * 目前支援英文（en）和繁體中文（zh）。
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import zh from './locales/zh.json'

// 從 localStorage 讀取已儲存的語言設定
const saved = localStorage.getItem('settings:language') as 'en' | 'zh' | null

// 如果沒有儲存的設定，根據瀏覽器語言自動選擇
const lng = saved || (navigator.language.startsWith('zh') ? 'zh' : 'en')

/**
 * 初始化 i18next
 * 
 * 配置支援的語言和翻譯資源。
 * 設定預設語言和回退語言。
 */
i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },  // 英文翻譯
      zh: { translation: zh },  // 繁體中文翻譯
    },
    lng,                        // 目前語言
    fallbackLng: 'en',          // 回退語言（當翻譯缺失時使用）
    interpolation: {
      escapeValue: false,       // React 已經自動處理 XSS 防護
    },
  })

export default i18n
