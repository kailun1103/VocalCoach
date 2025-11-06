/**
 * WAV 音訊錄製 Hook
 * 
 * 使用麥克風錄製音訊並轉換為 WAV 格式的 Blob。
 * 使用記憶體內的環形緩衝區處理音訊資料。
 */

import { useCallback, useEffect, useRef, useState } from 'react'

/** 錄製狀態類型 */
type RecorderState = 'idle' | 'recording' | 'stopped'

/**
 * WAV 音訊錄製 Hook
 * 
 * @param maxDurationSec - 最大錄製時長（秒），預設 60 秒
 * @returns 錄製器狀態和控制函數
 * 
 * 說明:
 * 提供開始、停止和重置錄製器的輔助函數。
 * 自動處理音訊資料的收集和 WAV 格式編碼。
 */
export default function useWavRecorder(maxDurationSec: number = 60) {
  // 錄製狀態
  const [state, setState] = useState<RecorderState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [durationSec, setDurationSec] = useState(0)
  
  // 音訊相關引用
  const sampleRateRef = useRef<number>(44100)
  const chunksRef = useRef<Float32Array[]>([])
  const framesRef = useRef<number>(0)
  const streamRef = useRef<MediaStream | null>(null)
  const ctxRef = useRef<AudioContext | null>(null)
  const srcRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const procRef = useRef<ScriptProcessorNode | null>(null)
  const tickRef = useRef<number | null>(null)

  /**
   * 重置錄製器狀態
   * 清除所有錄製資料和錯誤訊息
   */
  const reset = useCallback(() => {
    setState('idle')
    setError(null)
    setDurationSec(0)
    chunksRef.current = []
    framesRef.current = 0
  }, [])

  /**
   * 清理音訊資源
   * 斷開所有音訊節點並釋放媒體串流
   */
  const cleanup = useCallback(() => {
    try {
      procRef.current?.disconnect()
    } catch {
      /* 盡力而為，忽略錯誤 */
    }
    try {
      srcRef.current?.disconnect()
    } catch {
      /* 盡力而為，忽略錯誤 */
    }
    try {
      ctxRef.current?.close()
    } catch {
      /* 盡力而為，忽略錯誤 */
    }
    
    // 停止所有媒體軌道
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
    }
    
    // 清除所有引用
    procRef.current = null
    srcRef.current = null
    ctxRef.current = null
    streamRef.current = null
    
    // 清除定時器
    if (tickRef.current) {
      clearInterval(tickRef.current)
      tickRef.current = null
    }
  }, [])

  /**
   * 停止錄製並返回 WAV 格式的音訊 Blob
   * 
   * @returns WAV 格式的音訊 Blob
   * @throws 如果不在錄製狀態則拋出錯誤
   */
  const stop = useCallback(async (): Promise<Blob> => {
    if (state !== 'recording') {
      throw new Error('目前不在錄製狀態')
    }
    
    setState('stopped')
    cleanup()

    // 合併所有音訊區塊
    const totalFrames = framesRef.current
    const sampleRate = sampleRateRef.current
    const buffer = new Float32Array(totalFrames)
    let offset = 0
    
    for (const chunk of chunksRef.current) {
      buffer.set(chunk, offset)
      offset += chunk.length
    }
    
    // 編碼為 WAV 格式
    const wav = encodeWAV(buffer, sampleRate)
    return wav
  }, [cleanup, state])

  /**
   * 開始錄製音訊
   * 
   * 請求麥克風權限並開始收集音訊資料。
   * 自動在達到最大時長時停止錄製。
   */
  const start = useCallback(async () => {
    try {
      reset()
      cleanup()
      
      // 請求麥克風存取權限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      
      // 建立音訊處理上下文
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
      ctxRef.current = ctx
      sampleRateRef.current = ctx.sampleRate
      
      // 建立音訊來源節點
      const source = ctx.createMediaStreamSource(stream)
      srcRef.current = source
      
      // 建立音訊處理器（用於收集音訊資料）
      const proc = ctx.createScriptProcessor(4096, 1, 1)
      procRef.current = proc
      
      proc.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0)
        // 複製到新緩衝區以避免重用 WebAudio 記憶體
        chunksRef.current.push(new Float32Array(input))
        framesRef.current += input.length
      }
      
      // 連接音訊節點
      source.connect(proc)
      proc.connect(ctx.destination)
      
      setState('recording')
      
      // 啟動計時器
      const startAt = Date.now()
      tickRef.current = window.setInterval(() => {
        const elapsed = (Date.now() - startAt) / 1000
        setDurationSec(Math.floor(elapsed))
        
        // 達到最大時長時自動停止
        if (elapsed >= maxDurationSec) {
          void stop()
        }
      }, 200) as unknown as number
      
    } catch (e: any) {
      setError(e?.message || String(e))
      cleanup()
      setState('idle')
    }
  }, [cleanup, maxDurationSec, reset, stop])

  // 組件卸載時清理資源
  useEffect(() => () => cleanup(), [cleanup])

  return {
    state,
    isRecording: state === 'recording',
    error,
    durationSec,
    start,
    stop,
    reset,
  }
}

/**
 * 將 Float32 音訊樣本編碼為 WAV 格式
 * 
 * @param samples - Float32 格式的音訊樣本（範圍 -1 到 1）
 * @param sampleRate - 音訊取樣率
 * @returns WAV 格式的 Blob
 */
function encodeWAV(samples: Float32Array, sampleRate: number): Blob {
  // 將 Float32 [-1,1] 轉換為 16-bit PCM
  const bytesPerSample = 2
  const blockAlign = 1 * bytesPerSample
  const byteRate = sampleRate * blockAlign
  const dataSize = samples.length * bytesPerSample
  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)

  // WAV 檔案標頭
  writeString(view, 0, 'RIFF')                          // RIFF 識別符
  view.setUint32(4, 36 + dataSize, true)               // RIFF 區塊長度
  writeString(view, 8, 'WAVE')                          // RIFF 類型
  writeString(view, 12, 'fmt ')                         // 格式區塊識別符
  view.setUint32(16, 16, true)                         // 格式區塊長度
  view.setUint16(20, 1, true)                          // 樣本格式（原始 PCM）
  view.setUint16(22, 1, true)                          // 聲道數量
  view.setUint32(24, sampleRate, true)                 // 取樣率
  view.setUint32(28, byteRate, true)                   // 位元組率
  view.setUint16(32, blockAlign, true)                 // 區塊對齊
  view.setUint16(34, 16, true)                         // 每樣本位元數
  writeString(view, 36, 'data')                         // 資料區塊識別符
  view.setUint32(40, dataSize, true)                   // 資料區塊長度
  
  // 寫入音訊資料
  floatTo16BitPCM(view, 44, samples)
  
  return new Blob([view], { type: 'audio/wav' })
}

/**
 * 將字串寫入 DataView
 * 
 * @param view - DataView 物件
 * @param offset - 寫入位置偏移
 * @param str - 要寫入的字串
 */
function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}

/**
 * 將 Float32 樣本轉換為 16-bit PCM 格式
 * 
 * @param view - DataView 物件
 * @param offset - 寫入位置偏移
 * @param input - Float32 格式的音訊樣本
 */
function floatTo16BitPCM(view: DataView, offset: number, input: Float32Array) {
  let pos = offset
  for (let i = 0; i < input.length; i++, pos += 2) {
    // 限制範圍在 -1 到 1 之間
    let s = Math.max(-1, Math.min(1, input[i]))
    // 轉換為 16-bit 整數
    view.setInt16(pos, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
}
