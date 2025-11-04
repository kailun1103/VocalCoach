export type Role = 'system' | 'user' | 'assistant'

export interface ChatMessage {
  role: Role
  content: string
}

export interface ChatRequest {
  model?: string | null
  messages: ChatMessage[]
  temperature?: number | null
  max_tokens?: number | null
}

export interface ChatResponse {
  content: string
  model?: string | null
  finish_reason?: string | null
  prompt_tokens?: number | null
  completion_tokens?: number | null
  total_tokens?: number | null
}

export interface GrammarCheckRequest {
  text: string
  model?: string | null
}

export interface GrammarCheckResponse {
  is_correct: boolean
  feedback: string
  suggestion?: string | null
  model?: string | null
}

export interface DictionaryRequest {
  word: string
  sentence: string
  model?: string | null
}

export interface DictionaryResponse {
  headword: string
  part_of_speech?: string | null
  phonetics?: string[] | null
  definition: string
  examples: string[]
  notes?: string | null
  model?: string | null
}

export interface TTSRequest {
  text: string
  voice?: string | null
  length_scale?: number | null
  noise_scale?: number | null
  noise_w?: number | null
}

export interface TTSResponse {
  audio_base64: string
  sample_rate: number
  duration_seconds: number
  voice?: string | null
  length_scale?: number | null
  noise_scale?: number | null
  noise_w?: number | null
}

export interface STTResponse {
  text: string
  duration_ms: number
}
