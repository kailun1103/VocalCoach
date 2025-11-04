import { useCallback, useEffect, useRef, useState } from 'react'

type RecorderState = 'idle' | 'recording' | 'stopped'

/**
 * Record microphone input into a WAV Blob with a small in-memory ring buffer.
 * Returns helpers for starting, stopping, and resetting the recorder.
 */
export default function useWavRecorder(maxDurationSec: number = 60) {
  const [state, setState] = useState<RecorderState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [durationSec, setDurationSec] = useState(0)
  const sampleRateRef = useRef<number>(44100)
  const chunksRef = useRef<Float32Array[]>([])
  const framesRef = useRef<number>(0)
  const streamRef = useRef<MediaStream | null>(null)
  const ctxRef = useRef<AudioContext | null>(null)
  const srcRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const procRef = useRef<ScriptProcessorNode | null>(null)
  const tickRef = useRef<number | null>(null)

  const reset = useCallback(() => {
    setState('idle')
    setError(null)
    setDurationSec(0)
    chunksRef.current = []
    framesRef.current = 0
  }, [])

  const cleanup = useCallback(() => {
    try {
      procRef.current?.disconnect()
    } catch {
      /* ignore best effort */
    }
    try {
      srcRef.current?.disconnect()
    } catch {
      /* ignore best effort */
    }
    try {
      ctxRef.current?.close()
    } catch {
      /* ignore best effort */
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
    }
    procRef.current = null
    srcRef.current = null
    ctxRef.current = null
    streamRef.current = null
    if (tickRef.current) {
      clearInterval(tickRef.current)
      tickRef.current = null
    }
  }, [])

  const stop = useCallback(async (): Promise<Blob> => {
    if (state !== 'recording') throw new Error('not recording')
    setState('stopped')
    cleanup()

    const totalFrames = framesRef.current
    const sampleRate = sampleRateRef.current
    const buffer = new Float32Array(totalFrames)
    let offset = 0
    for (const chunk of chunksRef.current) {
      buffer.set(chunk, offset)
      offset += chunk.length
    }
    const wav = encodeWAV(buffer, sampleRate)
    return wav
  }, [cleanup, state])

  const start = useCallback(async () => {
    try {
      reset()
      cleanup()
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
      ctxRef.current = ctx
      sampleRateRef.current = ctx.sampleRate
      const source = ctx.createMediaStreamSource(stream)
      srcRef.current = source
      const proc = ctx.createScriptProcessor(4096, 1, 1)
      procRef.current = proc
      proc.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0)
        // Copy into a new buffer to avoid reusing WebAudio memory.
        chunksRef.current.push(new Float32Array(input))
        framesRef.current += input.length
      }
      source.connect(proc)
      proc.connect(ctx.destination)
      setState('recording')
      const startAt = Date.now()
      tickRef.current = window.setInterval(() => {
        const elapsed = (Date.now() - startAt) / 1000
        setDurationSec(Math.floor(elapsed))
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

function encodeWAV(samples: Float32Array, sampleRate: number): Blob {
  // Convert Float32 [-1,1] to 16-bit PCM
  const bytesPerSample = 2
  const blockAlign = 1 * bytesPerSample
  const byteRate = sampleRate * blockAlign
  const dataSize = samples.length * bytesPerSample
  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)

  /* RIFF identifier */ writeString(view, 0, 'RIFF')
  /* RIFF chunk length */ view.setUint32(4, 36 + dataSize, true)
  /* RIFF type */ writeString(view, 8, 'WAVE')
  /* format chunk identifier */ writeString(view, 12, 'fmt ')
  /* format chunk length */ view.setUint32(16, 16, true)
  /* sample format (raw) */ view.setUint16(20, 1, true)
  /* channel count */ view.setUint16(22, 1, true)
  /* sample rate */ view.setUint32(24, sampleRate, true)
  /* byte rate (sample rate * block align) */ view.setUint32(28, byteRate, true)
  /* block align (channel count * bytes per sample) */ view.setUint16(32, blockAlign, true)
  /* bits per sample */ view.setUint16(34, 16, true)
  /* data chunk identifier */ writeString(view, 36, 'data')
  /* data chunk length */ view.setUint32(40, dataSize, true)
  floatTo16BitPCM(view, 44, samples)
  return new Blob([view], { type: 'audio/wav' })
}

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}

function floatTo16BitPCM(view: DataView, offset: number, input: Float32Array) {
  let pos = offset
  for (let i = 0; i < input.length; i++, pos += 2) {
    let s = Math.max(-1, Math.min(1, input[i]))
    view.setInt16(pos, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
}
