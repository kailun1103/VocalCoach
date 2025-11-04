import { KeyboardEvent, MouseEvent, RefObject, useCallback, useEffect, useRef, useState } from 'react'

import { ChatMessage, DictionaryResponse, GrammarCheckResponse } from '../../types/api'
import { getMessageKey } from '../../modules/chat/utils'
import { dictionaryLookup } from '../../services/api'

type GrammarState = {
  loading: boolean
  error?: string
  result?: GrammarCheckResponse
}

type GrammarStateMap = Record<string, GrammarState>

type WordPopoverState = {
  id: string
  word: string
  sentence: string
  loading: boolean
  error?: string
  entry?: DictionaryResponse
  position: { top: number; left: number }
}

type ActionMenuState = {
  id: string
  align: 'left' | 'right'
  content: string
  showGrammar: boolean
  position: { top: number; left: number }
}

type ChatMessageListProps = {
  messages: ChatMessage[]
  isSending: boolean
  scrollBoxRef: RefObject<HTMLDivElement>
  bottomMarkerRef: RefObject<HTMLDivElement>
  atBottom: boolean
  onScrollToBottom: () => void
  className?: string
  grammarStates: GrammarStateMap
  onGrammarCheck: (messageId: string, text: string) => void
}

/** Render chat messages with per-word dictionary lookups and grammar feedback. */
export default function ChatMessageList({
  messages,
  isSending,
  scrollBoxRef,
  bottomMarkerRef,
  atBottom,
  onScrollToBottom,
  className = '',
  grammarStates,
  onGrammarCheck,
}: ChatMessageListProps) {
  const [popover, setPopover] = useState<WordPopoverState | null>(null)
  const [actionMenu, setActionMenu] = useState<ActionMenuState | null>(null)

  const dictionaryCacheRef = useRef<Map<string, DictionaryResponse>>(new Map())
  const activeWordRef = useRef<HTMLElement | null>(null)
  const actionAnchorRef = useRef<HTMLElement | null>(null)

  /** Determine where a word-level popover should appear relative to the scroll container. */
  const computeWordPosition = useCallback(
    (element: HTMLElement) => {
      const container = scrollBoxRef.current
      if (!container) return { top: 0, left: 0 }

      const wordRect = element.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()

      const top = wordRect.bottom - containerRect.top + container.scrollTop + 10
      const left = wordRect.left - containerRect.left + container.scrollLeft + wordRect.width / 2

      return { top, left }
    },
    [scrollBoxRef],
  )

  /** Keep the action menu within the viewport even when the user scrolls. */
  const computeActionMenuPosition = useCallback(
    (element: HTMLElement, align: 'left' | 'right') => {
      const container = scrollBoxRef.current
      if (!container) return { top: 0, left: 0 }

      const buttonRect = element.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()

      const rawTop = buttonRect.bottom - containerRect.top + container.scrollTop + 12
      const minTop = container.scrollTop + 20
      const top = Math.max(rawTop, minTop)

      let left = buttonRect.left - containerRect.left + container.scrollLeft
      if (align === 'right') {
        left += buttonRect.width
      }

      const minLeft = container.scrollLeft + 12
      const maxLeft = container.scrollLeft + containerRect.width - 12
      left = Math.min(Math.max(left, minLeft), maxLeft)

      return { top, left }
    },
    [scrollBoxRef],
  )

  useEffect(() => {
    if (!popover) return

    const anchor = activeWordRef.current
    if (!anchor) return

    const handlePosition = () => {
      setPopover((current) => (current ? { ...current, position: computeWordPosition(anchor) } : current))
    }

    handlePosition()
    window.addEventListener('resize', handlePosition)
    scrollBoxRef.current?.addEventListener('scroll', handlePosition, { passive: true })

    return () => {
      window.removeEventListener('resize', handlePosition)
      scrollBoxRef.current?.removeEventListener('scroll', handlePosition)
    }
  }, [popover, computeWordPosition, scrollBoxRef])

  useEffect(() => {
    if (!actionMenu) return

    const anchor = actionAnchorRef.current
    if (!anchor) return

    const handlePosition = () => {
      setActionMenu((current) =>
        current ? { ...current, position: computeActionMenuPosition(anchor, current.align) } : current,
      )
    }

    handlePosition()
    window.addEventListener('resize', handlePosition)
    scrollBoxRef.current?.addEventListener('scroll', handlePosition, { passive: true })

    return () => {
      window.removeEventListener('resize', handlePosition)
      scrollBoxRef.current?.removeEventListener('scroll', handlePosition)
    }
  }, [actionMenu, computeActionMenuPosition, scrollBoxRef])

  const handleBackdropClick = useCallback(() => {
    setPopover(null)
    setActionMenu(null)
    activeWordRef.current = null
    actionAnchorRef.current = null
  }, [])

  /** Open the dictionary popover for the selected word, caching previous lookups. */
  const handleWordClick = useCallback(
    async (event: MouseEvent<HTMLElement>, token: string, id: string, sentence: string) => {
      event.stopPropagation()

      if (popover?.id === id) {
        setPopover(null)
        activeWordRef.current = null
        return
      }

      const element = event.currentTarget
      activeWordRef.current = element

      const cacheKey = `${token.toLowerCase()}|${sentence}`
      const cached = dictionaryCacheRef.current.get(cacheKey)

      setPopover({
        id,
        word: token,
        sentence,
        loading: !cached,
        error: undefined,
        entry: cached,
        position: computeWordPosition(element),
      })

      if (cached) return

      try {
        const response = await dictionaryLookup({ word: token, sentence })
        dictionaryCacheRef.current.set(cacheKey, response)
        setPopover((current) =>
          current && current.id === id
            ? {
                ...current,
                entry: response,
                loading: false,
                error: undefined,
                position: computeWordPosition(element),
              }
            : current,
        )
      } catch (error: any) {
        setPopover((current) =>
          current && current.id === id
            ? {
                ...current,
                loading: false,
                error: error?.message || String(error) || '查詢失敗，請稍後再試。',
              }
            : current,
        )
      }
    },
    [popover, computeWordPosition],
  )

  /** Mirror the click behaviour for keyboard users. */
  const handleWordKeyDown = useCallback(
    (event: KeyboardEvent<HTMLElement>, token: string, id: string, sentence: string) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        event.stopPropagation()
        handleWordClick(event as unknown as MouseEvent<HTMLElement>, token, id, sentence)
      }
      if (event.key === 'Escape') {
        handleBackdropClick()
      }
    },
    [handleBackdropClick, handleWordClick],
  )

  const handleActionButtonClick = useCallback(
    (event: MouseEvent<HTMLButtonElement>, message: ChatMessage, messageId: string, isUser: boolean) => {
      event.stopPropagation()

      if (actionMenu?.id === messageId) {
        setActionMenu(null)
        actionAnchorRef.current = null
        return
      }

      const element = event.currentTarget
      actionAnchorRef.current = element

      setActionMenu({
        id: messageId,
        align: isUser ? 'left' : 'right',
        content: message.content,
        showGrammar: isUser,
        position: computeActionMenuPosition(element, isUser ? 'left' : 'right'),
      })
    },
    [actionMenu, computeActionMenuPosition],
  )

  const grammarStateFor = useCallback(
    (messageId: string): GrammarState => grammarStates[messageId] || { loading: false },
    [grammarStates],
  )

  return (
    <div
      ref={scrollBoxRef}
      className={`chat-message-list chat-scroll card relative h-[65vh] overflow-y-auto space-y-3 bg-gray-900/50 dark:bg-gray-900/50 border-gray-800 anim-scale-in ${className}`}
      onClick={handleBackdropClick}
    >
      {messages.map((message, idx) => {
        const key = getMessageKey(message)
        const isUser = message.role === 'user'
        const messageId = `${key}-msg-${idx}`
        const grammarState = grammarStateFor(messageId)

        const bubbleClasses = [
          'chat-message__bubble',
          'message-bubble',
          'max-w-[70vw]',
          'whitespace-pre-wrap',
          'rounded-2xl',
          'px-4',
          'py-2',
          'leading-relaxed',
          'shadow-sm',
        ]

        if (isUser) {
          bubbleClasses.push('bubble-user')
          if (grammarState.result) {
            bubbleClasses.push(
              grammarState.result.is_correct
                ? 'chat-message__bubble--grammar-ok'
                : 'chat-message__bubble--grammar-issue',
            )
          } else {
            bubbleClasses.push('bg-blue-600', 'text-white')
          }
        } else {
          bubbleClasses.push('bg-gray-800', 'text-gray-100', 'bubble-assistant')
        }

        return (
          <div
            key={messageId}
            className={`chat-message flex flex-col gap-2 ${isUser ? 'items-end chat-message--user' : 'items-start chat-message--assistant'} anim-fade-in-up`}
          >
            <div className={`message-row chat-message__row ${isUser ? 'flex-row-reverse chat-message__row--user' : 'chat-message__row--assistant'}`}>
              <div className={bubbleClasses.join(' ')}>
                {message.content ? (
                  <>
                    <span className="message-content chat-message__content">
                      {message.content.split(/(\s+)/).map((token, tokenIndex) => {
                        if (!token.trim()) {
                          return token
                        }
                        const wordId = `${key}-word-${tokenIndex}`
                        const isActive = popover?.id === wordId
                        return (
                          <span
                            key={wordId}
                            className={`message-word${isActive ? ' message-word--active' : ''}`}
                            role="button"
                            tabIndex={0}
                            aria-haspopup="dialog"
                            aria-expanded={isActive}
                            onClick={(event) => handleWordClick(event, token, wordId, message.content)}
                            onKeyDown={(event) => handleWordKeyDown(event, token, wordId, message.content)}
                          >
                            {token}
                          </span>
                        )
                      })}
                    </span>
                    {isSending && idx === messages.length - 1 ? <span className="caret" /> : null}
                  </>
                ) : isSending && idx === messages.length - 1 ? (
                  <span className="typing">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </span>
                ) : null}
              </div>
              <button
                type="button"
                className={`message-action-btn chat-message__action-btn ${isUser ? 'message-action-btn--user' : 'message-action-btn--assistant'}`}
                aria-label={isUser ? 'Message options' : 'Reply options'}
                aria-haspopup="menu"
                aria-expanded={actionMenu?.id === messageId}
                onClick={(event) => handleActionButtonClick(event, message, messageId, isUser)}
              >
                ⋯
              </button>
            </div>
          </div>
        )
      })}
      <div ref={bottomMarkerRef} />
      {actionMenu ? (
        <div
          className={`message-action-menu chat-message__menu message-action-menu--${actionMenu.align} anim-scale-in`}
          style={{ top: actionMenu.position.top, left: actionMenu.position.left }}
          role="menu"
          aria-label="Message actions"
          onClick={(event) => event.stopPropagation()}
        >
          {actionMenu.showGrammar ? (
            <>
              <button
                type="button"
                className="message-menu-item"
                onClick={(event) => {
                  event.stopPropagation()
                  onGrammarCheck(actionMenu.id, actionMenu.content)
                }}
                disabled={grammarStateFor(actionMenu.id).loading}
              >
                {grammarStateFor(actionMenu.id).loading ? '文法檢查中...' : '文法檢查'}
              </button>
              {grammarStateFor(actionMenu.id).error ? (
                <div className="message-menu-error">{grammarStateFor(actionMenu.id).error}</div>
              ) : null}
              {grammarStateFor(actionMenu.id).result ? (
                <div className="message-menu-result message-menu-result--grammar">
                  <div
                    className={`message-menu-grammar-status ${
                      grammarStateFor(actionMenu.id).result?.is_correct
                        ? 'message-menu-grammar-status--ok'
                        : 'message-menu-grammar-status--issue'
                    }`}
                  >
                    {grammarStateFor(actionMenu.id).result?.is_correct
                      ? '文法看起來很完美！'
                      : '發現文法需要調整。'}
                  </div>
                  {grammarStateFor(actionMenu.id).result?.suggestion ? (
                    <div className="message-menu-grammar-suggestion">
                      {'建議詞句：'}
                      <span className="message-menu-grammar-suggestion__text">
                        {grammarStateFor(actionMenu.id).result?.suggestion}
                      </span>
                    </div>
                  ) : null}
                  <div className="message-menu-grammar-feedback">
                    {grammarStateFor(actionMenu.id).result?.feedback}
                  </div>
                </div>
              ) : null}
            </>
          ) : (
            <div className="message-menu-result text-xs text-gray-400">系統回覆不提供文法檢查。</div>
          )}
        </div>
      ) : null}
      {popover ? (
        <div
          className="word-popover chat-word-popover anim-scale-in"
          style={{ top: popover.position.top, left: popover.position.left }}
          role="dialog"
          aria-live="polite"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="word-popover__header chat-word-popover__header">
            <span className="dictionary-headword">{popover.entry?.headword || popover.word}</span>
            {popover.entry?.part_of_speech ? (
              <span className="dictionary-pos">{popover.entry.part_of_speech}</span>
            ) : null}
            <button type="button" className="word-popover__close chat-word-popover__close" onClick={handleBackdropClick} aria-label="Close">
              ×
            </button>
          </div>
          <div className="word-popover__body chat-word-popover__body">
            {popover.loading ? (
              <span className="word-popover__status chat-word-popover__status">查詢中...</span>
            ) : popover.error ? (
              <span className="word-popover__status word-popover__status--error chat-word-popover__status chat-word-popover__status--error">
                {popover.error}
              </span>
            ) : popover.entry ? (
              <div className="dictionary-entry">
                {popover.entry.phonetics && popover.entry.phonetics.length ? (
                  <div className="dictionary-phonetics">
                    {popover.entry.phonetics.map((item, index) => (
                      <span key={index}>{item}</span>
                    ))}
                  </div>
                ) : null}
                <div className="dictionary-definition">
                  {popover.entry.definition.split(/\n+/).map((line, index) => (
                    <p key={index}>{line}</p>
                  ))}
                </div>
                {popover.entry.examples && popover.entry.examples.length ? (
                  <ul className="dictionary-examples">
                    {popover.entry.examples.map((example, index) => (
                      <li key={index}>{example}</li>
                    ))}
                  </ul>
                ) : null}
                {popover.entry.notes ? <p className="dictionary-notes">{popover.entry.notes}</p> : null}
              </div>
            ) : (
              <span className="word-popover__status chat-word-popover__status">查無資料</span>
            )}
          </div>
        </div>
      ) : null}
      {!atBottom && (
        <div className="sticky bottom-2 flex justify-center">
          <button
            onClick={(event) => {
              event.stopPropagation()
              onScrollToBottom()
            }}
            className="chat-message__scroll-button rounded-full bg-gray-700/80 px-3 py-1 text-xs text-gray-100 hover:bg-gray-600 transition transform active:scale-95"
          >
            {'↓'}
          </button>
        </div>
      )}
    </div>
  )
}
