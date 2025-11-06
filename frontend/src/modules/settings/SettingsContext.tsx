/**
 * 設定管理上下文模組
 * 
 * 提供全域應用程式設定的存取和持久化，
 * 包括 API 端點、串流模式和語言偏好。
 */

import React, { createContext, useContext, useMemo, useState, useEffect } from 'react'

/** 設定型別定義 */
type Settings = {
  /** API 基礎 URL */
  apiBaseUrl: string
  /** 是否啟用串流模式 */
  streaming: boolean
  /** 介面語言（英文或中文） */
  language: 'en' | 'zh'
  /** 設定 API 基礎 URL */
  setApiBaseUrl: (v: string) => void
  /** 設定串流模式 */
  setStreaming: (v: boolean) => void
  /** 設定介面語言 */
  setLanguage: (v: 'en' | 'zh') => void
}

// 建立設定上下文
const SettingsCtx = createContext<Settings | null>(null)

// 在本地開發時，允許透過 Vite 環境變數或 localStorage 覆寫後端端點
const defaultBase =
  import.meta.env.DEV ? ((import.meta.env.VITE_API_BASE_URL as string) || '/api') : ''

/**
 * 設定提供者組件
 * 
 * 將持久化的 UI 偏好和設定輔助函數提供給元件樹。
 * 所有設定會自動同步到 localStorage。
 */
export function SettingsProvider({ children }: { children: React.ReactNode }) {
  // API 基礎 URL 設定
  const [apiBaseUrl, setApiBaseUrl] = useState<string>(() => {
    if (import.meta.env.DEV) {
      return localStorage.getItem('settings:apiBaseUrl') || defaultBase
    }
    return defaultBase
  })
  
  // 串流模式設定
  const [streaming, setStreaming] = useState<boolean>(
    () => (localStorage.getItem('settings:streaming') ?? 'true') === 'true',
  )
  
  // 語言設定
  const [language, setLanguage] = useState<'en' | 'zh'>(
    () => (localStorage.getItem('settings:language') as 'en' | 'zh' | null) || 'zh',
  )

  // 持久化 API 基礎 URL（僅在開發模式）
  useEffect(() => {
    if (import.meta.env.DEV) {
      localStorage.setItem('settings:apiBaseUrl', apiBaseUrl)
    }
  }, [apiBaseUrl])

  // 持久化串流模式設定
  useEffect(() => {
    localStorage.setItem('settings:streaming', String(streaming))
  }, [streaming])

  // 持久化語言設定
  useEffect(() => {
    localStorage.setItem('settings:language', language)
  }, [language])

  // 建立設定物件
  const value = useMemo<Settings>(
    () => ({ apiBaseUrl, streaming, language, setApiBaseUrl, setStreaming, setLanguage }),
    [apiBaseUrl, streaming, language],
  )
  
  return <SettingsCtx.Provider value={value}>{children}</SettingsCtx.Provider>
}

/**
 * 設定 Hook
 * 
 * 便利的 Hook，確保提供者存在並返回設定物件。
 * 
 * @returns 設定物件
 * @throws 如果在提供者外使用則拋出錯誤
 */
export function useSettings() {
  const ctx = useContext(SettingsCtx)
  if (!ctx) {
    throw new Error('useSettings 必須在 SettingsProvider 內使用')
  }
  return ctx
}
