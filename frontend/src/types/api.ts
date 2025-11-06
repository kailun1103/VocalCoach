/**
 * API 型別定義
 * 
 * 定義與後端 API 通訊時使用的所有資料結構。
 */

// ========== 聊天相關型別 ==========

/** 聊天訊息的角色類型 */
export type Role = 'system' | 'user' | 'assistant'

/** 聊天訊息結構 */
export interface ChatMessage {
  /** 訊息發送者的角色 */
  role: Role
  /** 訊息內容文字 */
  content: string
}

/** 聊天請求參數 */
export interface ChatRequest {
  /** 可選的模型名稱（若未指定則使用伺服器預設值） */
  model?: string | null
  /** 對話歷史訊息陣列 */
  messages: ChatMessage[]
  /** 可選的取樣溫度（控制回應的隨機性） */
  temperature?: number | null
  /** 可選的最大 token 數量 */
  max_tokens?: number | null
}

/** 聊天回應結構 */
export interface ChatResponse {
  /** 助手回覆的內容 */
  content: string
  /** 實際使用的模型名稱 */
  model?: string | null
  /** 生成結束的原因 */
  finish_reason?: string | null
  /** 提示使用的 token 數量 */
  prompt_tokens?: number | null
  /** 完成生成使用的 token 數量 */
  completion_tokens?: number | null
  /** 總 token 數量 */
  total_tokens?: number | null
}

// ========== 文法檢查相關型別 ==========

/** 文法檢查請求參數 */
export interface GrammarCheckRequest {
  /** 要檢查的文字內容 */
  text: string
  /** 可選的模型名稱 */
  model?: string | null
}

/** 文法檢查回應結構 */
export interface GrammarCheckResponse {
  /** 文法是否正確 */
  is_correct: boolean
  /** 文法回饋說明 */
  feedback: string
  /** 建議的修正文字 */
  suggestion?: string | null
  /** 實際使用的模型名稱 */
  model?: string | null
}

// ========== 字典查詢相關型別 ==========

/** 字典查詢請求參數 */
export interface DictionaryRequest {
  /** 要查詢的單字 */
  word: string
  /** 可選的模型名稱 */
  model?: string | null
}

/** 字典查詢回應結構 */
export interface DictionaryResponse {
  /** 標準化的詞條 */
  headword: string
  /** 詞性（名詞、動詞等） */
  part_of_speech?: string | null
  /** 定義說明 */
  definition: string
  /** 例句陣列 */
  examples: string[]
  /** 實際使用的模型名稱 */
  model?: string | null
}

// ========== 文字轉語音相關型別 ==========

/** 文字轉語音請求參數 */
export interface TTSRequest {
  /** 要轉換的文字內容 */
  text: string
  /** 可選的語音識別碼 */
  voice?: string | null
  /** 語速控制（>1 較慢，<1 較快） */
  length_scale?: number | null
  /** 語音能量變化控制 */
  noise_scale?: number | null
  /** 音素寬度變化控制 */
  noise_w?: number | null
}

/** 文字轉語音回應結構 */
export interface TTSResponse {
  /** Base64 編碼的音訊資料 */
  audio_base64: string
  /** 音訊取樣率（Hz） */
  sample_rate: number
  /** 生成音訊耗時（秒） */
  duration_seconds: number
  /** 使用的語音識別碼 */
  voice?: string | null
  /** 實際使用的語速控制值 */
  length_scale?: number | null
  /** 實際使用的語音能量控制值 */
  noise_scale?: number | null
  /** 實際使用的音素寬度控制值 */
  noise_w?: number | null
}

// ========== 語音轉文字相關型別 ==========

/** 語音轉文字回應結構 */
export interface STTResponse {
  /** 轉寫的文字內容 */
  text: string
  /** 處理耗時（毫秒） */
  duration_ms: number
}
