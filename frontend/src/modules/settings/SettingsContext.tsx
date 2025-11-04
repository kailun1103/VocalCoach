import React, { createContext, useContext, useMemo, useState, useEffect } from 'react'

type Settings = {
  apiBaseUrl: string
  streaming: boolean
  language: 'en' | 'zh'
  setApiBaseUrl: (v: string) => void
  setStreaming: (v: boolean) => void
  setLanguage: (v: 'en' | 'zh') => void
}

const SettingsCtx = createContext<Settings | null>(null)

// When developing locally we allow overriding the backend endpoint via Vite env or localStorage.
const defaultBase =
  import.meta.env.DEV ? ((import.meta.env.VITE_API_BASE_URL as string) || '/api') : ''

/** Provide persisted UI preferences and helper setters to the component tree. */
export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [apiBaseUrl, setApiBaseUrl] = useState<string>(() => {
    if (import.meta.env.DEV) {
      return localStorage.getItem('settings:apiBaseUrl') || defaultBase
    }
    return defaultBase
  })
  const [streaming, setStreaming] = useState<boolean>(
    () => (localStorage.getItem('settings:streaming') ?? 'true') === 'true',
  )
  const [language, setLanguage] = useState<'en' | 'zh'>(
    () => (localStorage.getItem('settings:language') as 'en' | 'zh' | null) || 'zh',
  )

  useEffect(() => {
    if (import.meta.env.DEV) {
      localStorage.setItem('settings:apiBaseUrl', apiBaseUrl)
    }
  }, [apiBaseUrl])

  useEffect(() => {
    localStorage.setItem('settings:streaming', String(streaming))
  }, [streaming])

  useEffect(() => {
    localStorage.setItem('settings:language', language)
  }, [language])

  const value = useMemo<Settings>(
    () => ({ apiBaseUrl, streaming, language, setApiBaseUrl, setStreaming, setLanguage }),
    [apiBaseUrl, streaming, language],
  )
  return <SettingsCtx.Provider value={value}>{children}</SettingsCtx.Provider>
}

/** Convenience hook that ensures the provider is present. */
export function useSettings() {
  const ctx = useContext(SettingsCtx)
  if (!ctx) throw new Error('SettingsContext missing provider')
  return ctx
}
