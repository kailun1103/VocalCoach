import { useEffect, useState } from 'react'

/**
 * 將狀態同步到 localStorage，維持 React 狀態鉤子的使用方式。
 * 若存取 localStorage 失敗，會回傳初始預設值。
 */
export default function useLocalStorage<T>(key: string, initial: T) {
  const [state, setState] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key)
      return raw ? (JSON.parse(raw) as T) : initial
    } catch {
      return initial
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(state))
    } catch {}
  }, [key, state])

  return [state, setState] as const
}
