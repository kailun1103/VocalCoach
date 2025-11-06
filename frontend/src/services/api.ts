/**
 * API 服務模組
 * 
 * 提供與後端 FastAPI 伺服器通訊的所有功能，
 * 包括聊天、語音處理、文法檢查和字典查詢。
 */

import {
  ChatRequest,
  ChatResponse,
  DictionaryRequest,
  DictionaryResponse,
  GrammarCheckRequest,
  GrammarCheckResponse,
  STTResponse,
  TTSRequest,
  TTSResponse,
} from '../types/api'

/**
 * 解析後端 API 的基礎 URL
 * 
 * @returns API 基礎 URL 字串
 * 
 * 說明:
 * - 在生產環境中，使用相對路徑（空字串）
 * - 在開發環境中，優先使用 localStorage 中儲存的設定
 * - 最後才使用環境變數 VITE_API_BASE_URL
 */
export function getApiBase(): string {
  if (!import.meta.env.DEV) {
    return ''
  }
  const saved = localStorage.getItem('settings:apiBaseUrl')
  return saved || ((import.meta.env.VITE_API_BASE_URL as string) || '/api')
}

/**
 * 執行標準聊天對話請求
 * 
 * @param req - 聊天請求參數
 * @param base - 可選的 API 基礎 URL
 * @returns 聊天回應內容
 * @throws 當請求失敗時拋出錯誤
 */
export async function chat(req: ChatRequest, base?: string): Promise<ChatResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/chat`
  
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  
  if (!res.ok) {
    throw new Error(`聊天請求失敗: ${res.status}`)
  }
  
  return res.json()
}

/**
 * 串流式聊天對話請求
 * 
 * @param req - 聊天請求參數
 * @param base - 可選的 API 基礎 URL
 * @yields 逐步產生的文字片段
 * @throws 當請求失敗時拋出錯誤
 * 
 * 說明:
 * 使用 Server-Sent Events (SSE) 串流接收聊天回應，
 * 逐步產生文字片段。當資料不是有效的 JSON 時，
 * 會回退為直接發送原始資料區塊。
 */
export async function* chatStream(
  req: ChatRequest, 
  base?: string
): AsyncGenerator<string, void, unknown> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/chat/stream`
  
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  
  if (!res.ok || !res.body) {
    throw new Error(`串流請求失敗: ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    
    if (done) {
      buffer += decoder.decode()
      break
    }
    
    buffer += decoder.decode(value, { stream: true })
    let idx
    
    // 處理完整的 SSE 事件（以 \n\n 分隔）
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const line = chunk.trim()
      
      if (!line) continue
      
      if (line.startsWith('data:')) {
        const data = line.slice(5).trim()
        
        // 串流結束標記
        if (data === '[DONE]') return
        
        try {
          const parsed = JSON.parse(data)
          
          // 檢查錯誤
          if (parsed?.error) {
            throw new Error(parsed.error)
          }
          
          // 提取文字內容
          const text = parsed?.choices?.[0]?.delta?.content ?? parsed?.content ?? ''
          if (text) yield text
          
        } catch (err) {
          // 如果不是 JSON 格式，直接產生原始資料
          if (data.startsWith('{') || data.startsWith('[')) {
            throw err
          } else {
            yield data
          }
        }
      }
    }
  }
}

/**
 * 文字轉語音請求
 * 
 * @param req - 文字轉語音請求參數
 * @param base - 可選的 API 基礎 URL
 * @returns 包含音訊資料的回應
 * @throws 當請求失敗時拋出錯誤
 */
export async function tts(req: TTSRequest, base?: string): Promise<TTSResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/tts`
  
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  
  if (!res.ok) {
    throw new Error(`文字轉語音失敗: ${res.status}`)
  }
  
  return res.json()
}

/**
 * 語音轉文字請求
 * 
 * @param file - 要轉寫的音訊檔案
 * @param base - 可選的 API 基礎 URL
 * @returns 轉寫後的文字內容
 * @throws 當請求失敗時拋出錯誤
 */
export async function stt(file: File, base?: string): Promise<STTResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/stt`
  
  // 使用 FormData 上傳檔案
  const fd = new FormData()
  fd.append('file', file)
  
  const res = await fetch(url, {
    method: 'POST',
    body: fd,
  })
  
  if (!res.ok) {
    throw new Error(`語音轉文字失敗: ${res.status}`)
  }
  
  return res.json()
}

/**
 * 文法檢查請求
 * 
 * @param req - 文法檢查請求參數
 * @param base - 可選的 API 基礎 URL
 * @returns 文法檢查結果
 * @throws 當請求失敗時拋出錯誤
 */
export async function grammarCheck(
  req: GrammarCheckRequest, 
  base?: string
): Promise<GrammarCheckResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/grammar`
  
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  
  if (!res.ok) {
    throw new Error(`文法檢查失敗: ${res.status}`)
  }
  
  return res.json()
}

/**
 * 字典查詢請求
 * 
 * @param req - 字典查詢請求參數
 * @param base - 可選的 API 基礎 URL
 * @returns 字典查詢結果
 * @throws 當請求失敗時拋出錯誤
 */
export async function dictionaryLookup(
  req: DictionaryRequest, 
  base?: string
): Promise<DictionaryResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/dictionary`
  
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  
  if (!res.ok) {
    throw new Error(`字典查詢失敗: ${res.status}`)
  }
  
  return res.json()
}
