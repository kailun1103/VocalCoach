import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import ChatComposer from '../components/chat/ChatComposer'
import ChatMessageList from '../components/chat/ChatMessageList'
import useLocalStorage from '../hooks/useLocalStorage'
import useWavRecorder from '../hooks/useWavRecorder'
import { useSettings } from '../modules/settings/SettingsContext'
import { chat, chatStream, grammarCheck, stt, tts } from '../services/api'
import { ChatMessage, GrammarCheckResponse } from '../types/api'
import { getMessageKey } from '../modules/chat/utils'

const SCROLL_THRESHOLD = 40

type GrammarState = {
  loading: boolean
  error?: string
  result?: GrammarCheckResponse
}

type GrammarStateMap = Record<string, GrammarState>

export default function ChatPage() {
  const { t } = useTranslation()
  const { streaming, setStreaming, language } = useSettings()
  const [messages, setMessages] = useLocalStorage<ChatMessage[]>('chat:messages', [])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isSpeakingBackend, setIsSpeakingBackend] = useState(false)
  const [isSpeakingLocal, setIsSpeakingLocal] = useState(false)
  const [grammarStates, setGrammarStates] = useState<GrammarStateMap>({})

  const scrollBoxRef = useRef<HTMLDivElement>(null)
  const bottomMarkerRef = useRef<HTMLDivElement>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const localUtterRef = useRef<SpeechSynthesisUtterance | null>(null)
  const [atBottom, setAtBottom] = useState(true)
  const recorder = useWavRecorder(60)
  const messagesRef = useRef<ChatMessage[]>(messages) // Track the latest messages for async callbacks.
  const scrollToBottom = useCallback(() => {
    bottomMarkerRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const updateMessages = useCallback(
    (value: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => {
      setMessages((prev) => {
        const next = typeof value === 'function' ? (value as (prev: ChatMessage[]) => ChatMessage[])(prev) : value
        messagesRef.current = next
        return next
      })
    },
    [setMessages],
  )

  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  // Kick off grammar checking for user messages as they appear in the transcript.
  const queueGrammarCheckWithContext = useCallback(
    async (messageId: string, text: string, messageIndex: number) => {
      const trimmed = text.trim()
      if (!trimmed) return
      setGrammarStates((prev) => ({ ...prev, [messageId]: { loading: true } }))
      try {
        // Get conversation context up to (but not including) the current message
        const context = messages.slice(0, messageIndex)
        const result = await grammarCheck({ 
          text: trimmed,
          context: context.length > 0 ? context : undefined
        })
        setGrammarStates((prev) => ({ ...prev, [messageId]: { loading: false, result } }))
      } catch (error: any) {
        setGrammarStates((prev) => ({
          ...prev,
          [messageId]: {
            loading: false,
            error: error?.message || String(error) || '文法檢查失敗，請稍後再試。',
          },
        }))
      }
    },
    [messages],
  )

  // Wrapper for manual grammar check (from UI button) - finds message index automatically
  const queueGrammarCheck = useCallback(
    (messageId: string, text: string) => {
      // Find the message index based on messageId pattern
      const match = messageId.match(/-msg-(\d+)$/)
      const index = match ? parseInt(match[1], 10) : messages.length
      queueGrammarCheckWithContext(messageId, text, index)
    },
    [messages.length, queueGrammarCheckWithContext],
  )

  useEffect(() => {
    messages.forEach((message, index) => {
      if (message.role !== 'user') return
      const messageId = `${getMessageKey(message)}-msg-${index}`
      if (grammarStates[messageId]) return
      queueGrammarCheckWithContext(messageId, message.content, index)
    })
  }, [messages, grammarStates, queueGrammarCheckWithContext])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Track whether the user has scrolled away from the bottom of the chat window.
  useEffect(() => {
    const element = scrollBoxRef.current
    if (!element) return
    const onScroll = () => {
      const distance = element.scrollHeight - element.scrollTop - element.clientHeight
      setAtBottom(distance < SCROLL_THRESHOLD)
    }
    element.addEventListener('scroll', onScroll)
    return () => element.removeEventListener('scroll', onScroll)
  }, [])

  // Stop any pending audio playback or speech synthesis when the component unmounts.
  useEffect(() => {
    return () => {
      const audio = audioRef.current
      if (audio) {
        try {
          audio.pause()
        } catch {
          // ignore best effort
        }
        if (audio?.src) URL.revokeObjectURL(audio.src)
        audioRef.current = null
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel()
        } catch {
          // ignore best effort
        }
      }
      localUtterRef.current = null
    }
  }, [])

  // Use the browser's speech synthesis as a lightweight fallback when TTS fails.
  const speakLocal = useCallback(
    (text: string) => {
      if (typeof window === 'undefined') return
      const synthesis = window.speechSynthesis
      if (!synthesis || !text.trim()) return
      try {
        synthesis.cancel()
      } catch {
        // ignore best effort
      }
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = language === 'zh' ? 'zh-TW' : 'en-US'
      utterance.onstart = () => setIsSpeakingLocal(true)
      utterance.onend = utterance.onerror = () => {
        setIsSpeakingLocal(false)
        if (localUtterRef.current === utterance) {
          localUtterRef.current = null
        }
      }
      localUtterRef.current = utterance
      synthesis.speak(utterance)
    },
    [language],
  )

  // Ask the backend to synthesise speech, falling back to the local engine when needed.
  const speak = useCallback(
    async (text: string) => {
      const content = text.trim()
      if (!content) return
      try {
        setIsSpeakingBackend(true)
        const response = await tts({ text: content })

        const binary = atob(response.audio_base64)
        const buffer = new Uint8Array(binary.length)
        for (let index = 0; index < binary.length; index++) {
          buffer[index] = binary.charCodeAt(index)
        }

        const blob = new Blob([buffer], { type: 'audio/wav' })
        const url = URL.createObjectURL(blob)

        if (!audioRef.current) {
          audioRef.current = new Audio()
        }
        const current = audioRef.current
        try {
          current.pause()
        } catch {
          // ignore best effort
        }
        current.src = url
        current.onended = () => {
          setIsSpeakingBackend(false)
          URL.revokeObjectURL(url)
        }
        current.onerror = () => {
          setIsSpeakingBackend(false)
          URL.revokeObjectURL(url)
        }
        current.play().catch(() => {
          setIsSpeakingBackend(false)
          URL.revokeObjectURL(url)
        })
      } catch (error) {
        console.error(error)
        setIsSpeakingBackend(false)
        speakLocal(content)
      }
    },
    [speakLocal],
  )

  // Append a user message, call the chat API, and append the resulting assistant reply.
  const sendContent = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = { role: 'user', content }
      const conversation: ChatMessage[] = [...messagesRef.current, userMessage]
      updateMessages(conversation)
      const messageKey = getMessageKey(userMessage)
      const messageId = `${messageKey}-msg-${conversation.length - 1}`
      setIsSending(true)

      let assistantReply = ''
      try {
        if (streaming) {
          let accumulator = ''
          updateMessages((prev) => [...prev, { role: 'assistant', content: '' }])
          for await (const token of chatStream({ messages: conversation })) {
            accumulator += token
            updateMessages((prev) => {
              const updated = [...prev]
              updated[updated.length - 1] = { role: 'assistant', content: accumulator }
              return updated
            })
          }
          assistantReply = accumulator
        } else {
          const response = await chat({ messages: conversation })
          assistantReply = response.content
          updateMessages((prev) => [...prev, { role: 'assistant', content: assistantReply }])
        }
      } catch (error: any) {
        updateMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `(${t('common.error')}: ${error?.message || error})` },
        ])
      } finally {
        setIsSending(false)
        if (assistantReply.trim()) {
          void speak(assistantReply)
        }
      }
    },
    [queueGrammarCheck, speak, streaming, t],
  )

  const handleSend = useCallback(async () => {
    const content = input.trim()
    if (!content || isSending) return
    setInput('')
    await sendContent(content)
  }, [input, isSending, sendContent])

  const handleClear = useCallback(() => {
    if (isSending) return
    if (window.confirm(t('chat.confirmClear') as string)) {
      updateMessages([])
      setGrammarStates({})
    }
  }, [isSending, t, updateMessages])

  const handleRegenerate = useCallback(async () => {
    if (isSending) return

    const currentMessages = messagesRef.current
    let lastUserIndex = -1
    for (let index = currentMessages.length - 1; index >= 0; index--) {
      if (currentMessages[index].role === 'user') {
        lastUserIndex = index
        break
      }
    }
    if (lastUserIndex < 0) return

    let baseConversation = currentMessages
    if (
      currentMessages.length > lastUserIndex + 1 &&
      currentMessages[currentMessages.length - 1].role === 'assistant'
    ) {
      baseConversation = currentMessages.slice(0, currentMessages.length - 1)
      updateMessages(baseConversation)
    }

    setIsSending(true)
    let assistantReply = ''
    try {
      if (streaming) {
        let accumulator = ''
        updateMessages((prev) => [...prev, { role: 'assistant', content: '' }])
        for await (const token of chatStream({ messages: baseConversation })) {
          accumulator += token
          updateMessages((prev) => {
            const updated = [...prev]
            updated[updated.length - 1] = { role: 'assistant', content: accumulator }
            return updated
          })
        }
        assistantReply = accumulator
      } else {
        const response = await chat({ messages: baseConversation })
        assistantReply = response.content
        updateMessages((prev) => [...prev, { role: 'assistant', content: assistantReply }])
      }
    } catch (error: any) {
      updateMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `(${t('common.error')}: ${error?.message || error})` },
      ])
    } finally {
      setIsSending(false)
      if (assistantReply.trim()) {
        void speak(assistantReply)
      }
    }
  }, [isSending, speak, streaming, t, updateMessages])

  const handleToggleRecord = useCallback(async () => {
    if (recorder.isRecording) {
      try {
        setIsTranscribing(true)
        const blob = await recorder.stop()
        const file = new File([blob], 'recording.wav', { type: 'audio/wav' })
        const result = await stt(file)
        await sendContent(result.text)
      } catch (error) {
        console.error(error)
        alert(t('common.error'))
      } finally {
        setIsTranscribing(false)
      }
    } else {
      try {
        await recorder.start()
      } catch (error) {
        console.error(error)
        alert(t('common.error'))
      }
    }
  }, [recorder, sendContent, t])

  const canRegenerate = useMemo(() => messages.some((message) => message.role === 'user'), [messages])
  const canClear = messages.length > 0 || input.trim().length > 0

  return (
    <div className="chat-page space-y-4">
      <h1 className="text-xl font-semibold text-gray-100">{t('chat.title')}</h1>
      <ChatMessageList
        className="chat-page__message-list"
        messages={messages}
        isSending={isSending}
        scrollBoxRef={scrollBoxRef}
        bottomMarkerRef={bottomMarkerRef}
        atBottom={atBottom}
        onScrollToBottom={scrollToBottom}
        grammarStates={grammarStates}
        onGrammarCheck={queueGrammarCheck}
      />
      <ChatComposer
        className="chat-page__composer"
        input={input}
        placeholder={t('chat.placeholder') as string}
        onInputChange={setInput}
        onSend={handleSend}
        onRegenerate={handleRegenerate}
        onClear={handleClear}
        isSending={isSending}
        sendLabel={t('chat.send') as string}
        regenerateLabel={t('chat.regenerate') as string}
        clearLabel={t('chat.clear') as string}
        streamingLabel={t('chat.streaming') as string}
        streaming={streaming}
        onStreamingChange={(value) => setStreaming(value)}
        recorder={recorder}
        onToggleRecord={handleToggleRecord}
        recordLabel={t('voice.record') as string}
        stopLabel={t('voice.stop') as string}
        recordingLabel={t('voice.recording') as string}
        transcribingLabel={t('voice.transcribing') as string}
        speakingLabel={t('voice.speaking') as string}
        isTranscribing={isTranscribing}
        isSpeakingLocal={isSpeakingLocal}
        isSpeakingBackend={isSpeakingBackend}
        canRegenerate={canRegenerate && messages.length > 0}
        canClear={canClear}
      />
    </div>
  )
}
