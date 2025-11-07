import { KeyboardEvent, MouseEvent, RefObject, useCallback, useEffect, useRef, useState } from 'react'

import { ChatMessage, DictionaryResponse, GrammarCheckResponse } from '../../types/api'
import { getMessageKey } from '../../modules/chat/utils'
import { dictionaryLookup } from '../../services/api'
import './ChatMessageList.css'

/**
 * 文法檢查狀態
 */
type GrammarState = {
  loading: boolean                    // 載入中
  error?: string                      // 錯誤訊息
  result?: GrammarCheckResponse       // 檢查結果
}

/**
 * 文法狀態映射表（訊息 ID -> 文法狀態）
 */
type GrammarStateMap = Record<string, GrammarState>

/**
 * 單字彈出視窗狀態
 */
type WordPopoverState = {
  id: string                          // 單字唯一識別碼
  word: string                        // 單字文字
  sentence: string                    // 單字所在的句子
  loading: boolean                    // 字典查詢載入中
  error?: string                      // 查詢錯誤訊息
  entry?: DictionaryResponse          // 字典查詢結果
  position: { top: number; left: number }  // 彈出視窗位置
}

/**
 * 操作選單狀態
 */
type ActionMenuState = {
  id: string                          // 訊息唯一識別碼
  align: 'left' | 'right'            // 選單對齊方向
  content: string                     // 訊息內容
  showGrammar: boolean                // 是否顯示文法檢查選項
  position: { top: number; left: number }  // 選單位置
}

/**
 * 聊天訊息列表元件屬性
 */
type ChatMessageListProps = {
  messages: ChatMessage[]             // 聊天訊息陣列
  isSending: boolean                  // 是否正在傳送訊息
  scrollBoxRef: RefObject<HTMLDivElement>      // 捲動容器參照
  bottomMarkerRef: RefObject<HTMLDivElement>   // 底部標記參照
  atBottom: boolean                   // 是否已捲動到底部
  onScrollToBottom: () => void        // 捲動到底部的回呼函數
  className?: string                  // 自訂 CSS 類別
  grammarStates: GrammarStateMap      // 文法檢查狀態映射表
  onGrammarCheck: (messageId: string, text: string) => void  // 文法檢查回呼函數
}

/**
 * 聊天訊息列表元件
 * 
 * 渲染聊天訊息，支援單字點擊查詢字典、文法檢查等互動功能。
 * 每個單字都可以點擊彈出字典解釋，使用者訊息可進行文法檢查。
 */
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
  // 單字彈出視窗狀態
  const [popover, setPopover] = useState<WordPopoverState | null>(null)
  // 操作選單狀態
  const [actionMenu, setActionMenu] = useState<ActionMenuState | null>(null)

  // 字典查詢快取（避免重複查詢相同單字）
  const dictionaryCacheRef = useRef<Map<string, DictionaryResponse>>(new Map())
  // 當前點擊的單字元素參照
  const activeWordRef = useRef<HTMLElement | null>(null)
  // 操作按鈕元素參照
  const actionAnchorRef = useRef<HTMLElement | null>(null)

  /**
   * 計算單字彈出視窗的顯示位置
   * 
   * 根據單字元素相對於捲動容器的位置，計算彈出視窗應該出現的座標。
   * 彈出視窗會顯示在單字下方 10px 處，並智能調整水平位置以避免超出邊界。
   * - 若單字在右側，彈出視窗往左展開
   * - 若單字在左側，彈出視窗往右展開
   */
  const computeWordPosition = useCallback(
    (element: HTMLElement) => {
      const container = scrollBoxRef.current
      if (!container) return { top: 0, left: 0 }

      const wordRect = element.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()

      // 計算垂直位置（單字底部 + 10px 間距）
      const top = wordRect.bottom - containerRect.top + container.scrollTop + 10
      
      // 字典彈出視窗的固定寬度（與 CSS width 一致）
      const popoverWidth = 400
      const padding = 20 // 左右邊界留白
      
      // 計算單字在容器中的相對水平位置
      const wordLeftInContainer = wordRect.left - containerRect.left
      const wordRightInContainer = wordRect.right - containerRect.left
      const containerWidth = containerRect.width
      
      // 計算如果往右展開會不會超出邊界
      const spaceOnRight = containerWidth - wordLeftInContainer
      const spaceOnLeft = wordRightInContainer
      
      let left: number
      
      // 優先判斷：如果右邊空間不足以容納彈出視窗，就往左展開
      if (spaceOnRight < popoverWidth + padding) {
        // 右邊空間不足，彈出視窗往左展開（對齊單字右側）
        left = wordRect.right - containerRect.left + container.scrollLeft - popoverWidth
        // 確保不會超出左邊界
        left = Math.max(left, container.scrollLeft + padding)
      } else if (spaceOnLeft > popoverWidth + padding) {
        // 左邊也有足夠空間，判斷單字更靠近哪一邊
        if (wordLeftInContainer > containerWidth / 2) {
          // 單字在右半部，往左展開
          left = wordRect.right - containerRect.left + container.scrollLeft - popoverWidth
        } else {
          // 單字在左半部，往右展開
          left = wordRect.left - containerRect.left + container.scrollLeft
        }
      } else {
        // 右邊有足夠空間，往右展開
        left = wordRect.left - containerRect.left + container.scrollLeft
        // 確保不會超出右邊界
        const maxLeft = container.scrollLeft + containerWidth - popoverWidth - padding
        left = Math.min(left, maxLeft)
      }

      return { top, left }
    },
    [scrollBoxRef],
  )

  /**
   * 計算操作選單的顯示位置
   * 
   * 讓選單顯示在訊息泡泡下方，確保不會超出視窗範圍。
   * 根據訊息對齊方向（左/右）調整選單的水平位置。
   */
  const computeActionMenuPosition = useCallback(
    (element: HTMLElement, align: 'left' | 'right') => {
      const container = scrollBoxRef.current
      if (!container) return { top: 0, left: 0 }

      // 找到訊息泡泡元素（操作按鈕的上一個兄弟元素）
      const messageRow = element.closest('.message-row')
      const messageBubble = messageRow?.querySelector('.message-bubble')
      
      if (!messageBubble) return { top: 0, left: 0 }

      const bubbleRect = messageBubble.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()

      // 計算垂直位置：泡泡底部 + 8px 間距
      const top = bubbleRect.bottom - containerRect.top + container.scrollTop + 8

      // 計算水平位置
      let left: number
      if (align === 'left') {
        // 使用者訊息：從泡泡左側開始
        left = bubbleRect.left - containerRect.left + container.scrollLeft
      } else {
        // 系統訊息：從泡泡右側向左對齊
        left = bubbleRect.right - containerRect.left + container.scrollLeft - 450 // 選單寬度
      }

      // 確保選單不會超出左右邊界
      const minLeft = container.scrollLeft + 20
      const maxLeft = container.scrollLeft + containerRect.width - 470 // 選單寬度 + 邊距
      left = Math.min(Math.max(left, minLeft), maxLeft)

      return { top, left }
    },
    [scrollBoxRef],
  )

  /**
   * 監聽視窗大小改變和捲動事件，動態更新單字彈出視窗位置
   * 確保彈出視窗始終跟隨單字元素移動
   */
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

  /**
   * 監聽視窗大小改變和捲動事件，動態更新操作選單位置
   * 確保選單始終跟隨操作按鈕移動
   */
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

  /**
   * 處理背景點擊事件，關閉所有彈出視窗和選單
   */
  const handleBackdropClick = useCallback(() => {
    setPopover(null)
    setActionMenu(null)
    activeWordRef.current = null
    actionAnchorRef.current = null
  }, [])

  /**
   * 處理單字點擊事件，開啟字典彈出視窗
   * 
   * 實作功能：
   * 1. 若點擊同一個單字，則關閉彈出視窗
   * 2. 使用快取避免重複查詢相同單字
   * 3. 異步查詢字典 API 並更新結果
   * 4. 處理查詢錯誤並顯示友善訊息
   */
  const handleWordClick = useCallback(
    async (event: MouseEvent<HTMLElement>, token: string, id: string, sentence: string) => {
      event.stopPropagation()

      // 若點擊同一個單字，關閉彈出視窗
      if (popover?.id === id) {
        setPopover(null)
        activeWordRef.current = null
        return
      }

      const element = event.currentTarget
      activeWordRef.current = element

      // 檢查快取中是否已有查詢結果（只根據單字快取）
      const cacheKey = token.toLowerCase()
      const cached = dictionaryCacheRef.current.get(cacheKey)

      // 立即顯示彈出視窗（使用快取資料或顯示載入狀態）
      setPopover({
        id,
        word: token,
        sentence,
        loading: !cached,
        error: undefined,
        entry: cached,
        position: computeWordPosition(element),
      })

      // 自動播放單字發音
      try {
        const utterance = new SpeechSynthesisUtterance(token)
        utterance.lang = 'en-US'
        utterance.rate = 0.8
        window.speechSynthesis.speak(utterance)
      } catch (error) {
        // 忽略語音播放錯誤，不影響字典查詢功能
        console.warn('Speech synthesis failed:', error)
      }

      // 若有快取，直接返回
      if (cached) return

      // 查詢字典 API
      try {
        const response = await dictionaryLookup({ word: token })
        dictionaryCacheRef.current.set(cacheKey, response)
        
        // 更新彈出視窗內容
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
        // 處理查詢錯誤
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

  /**
   * 處理單字鍵盤事件，提供鍵盤無障礙操作
   * 
   * 支援的鍵盤操作：
   * - Enter / Space: 開啟字典彈出視窗（等同於滑鼠點擊）
   * - Escape: 關閉彈出視窗
   */
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

  /**
   * 處理操作按鈕點擊事件，顯示或關閉操作選單
   * 
   * 使用者訊息（左側）顯示文法檢查選項
   * 系統訊息（右側）顯示提示訊息
   */
  const handleActionButtonClick = useCallback(
    (event: MouseEvent<HTMLButtonElement>, message: ChatMessage, messageId: string, isUser: boolean) => {
      event.stopPropagation()

      // 若點擊同一個按鈕，關閉選單
      if (actionMenu?.id === messageId) {
        setActionMenu(null)
        actionAnchorRef.current = null
        return
      }

      const element = event.currentTarget
      actionAnchorRef.current = element

      // 開啟操作選單
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

  /**
   * 取得指定訊息的文法檢查狀態
   */
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

        // 組合訊息氣泡樣式類別
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

        // 根據訊息角色和文法檢查結果設定樣式
        if (isUser) {
          bubbleClasses.push('bubble-user')
          if (grammarState.result) {
            // 根據文法檢查結果添加對應樣式
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
              {/* 訊息氣泡 */}
              <div className={bubbleClasses.join(' ')}>
                {message.content ? (
                  <>
                    <span className="message-content chat-message__content">
                      {/* 將訊息內容分割為單字，每個單字可點擊查詢字典 */}
                      {message.content.split(/(\s+)/).map((token, tokenIndex) => {
                        // 跳過空白符號
                        if (!token.trim()) {
                          return token
                        }
                        
                        // 分離單字和標點符號
                        const match = token.match(/^([a-zA-Z'-]+)(.*)$/)
                        
                        if (!match || !match[1]) {
                          // 如果沒有字母（純標點符號），直接返回不可點擊
                          return <span key={`${key}-punct-${tokenIndex}`}>{token}</span>
                        }
                        
                        const word = match[1]  // 單字部分
                        const punctuation = match[2]  // 標點符號部分
                        const wordId = `${key}-word-${tokenIndex}`
                        const isActive = popover?.id === wordId
                        
                        return (
                          <span key={wordId}>
                            <span
                              className={`message-word${isActive ? ' message-word--active' : ''}`}
                              role="button"
                              tabIndex={0}
                              aria-haspopup="dialog"
                              aria-expanded={isActive}
                              onClick={(event) => handleWordClick(event, word, wordId, message.content)}
                              onKeyDown={(event) => handleWordKeyDown(event, word, wordId, message.content)}
                            >
                              {word}
                            </span>
                            {punctuation && <span className="message-punctuation">{punctuation}</span>}
                          </span>
                        )
                      })}
                    </span>
                    {/* 最後一則訊息傳送中時顯示游標 */}
                    {isSending && idx === messages.length - 1 ? <span className="caret" /> : null}
                  </>
                ) : isSending && idx === messages.length - 1 ? (
                  // 傳送中動畫（三個點）
                  <span className="typing">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </span>
                ) : null}
              </div>
              
              {/* 操作按鈕（⋯） */}
              <button
                type="button"
                className={`message-action-btn chat-message__action-btn ${isUser ? 'message-action-btn--user' : 'message-action-btn--assistant'}`}
                aria-label={isUser ? '訊息選項' : '回覆選項'}
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
      
      {/* 底部標記（用於自動捲動偵測） */}
      <div ref={bottomMarkerRef} />
      
      {/* 操作選單彈出視窗 */}
      {actionMenu ? (
        <div
          className={`message-action-menu chat-message__menu message-action-menu--${actionMenu.align} anim-scale-in`}
          style={{ top: actionMenu.position.top, left: actionMenu.position.left }}
          role="menu"
          aria-label="訊息操作"
          onClick={(event) => event.stopPropagation()}
        >
          {/* 關閉按鈕 */}
          <button
            type="button"
            className="message-action-menu__close"
            onClick={handleBackdropClick}
            aria-label="關閉"
          >
            ×
          </button>
          {actionMenu.showGrammar ? (
            <>
              {/* 文法檢查按鈕 */}
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
              
              {/* 文法檢查錯誤訊息 */}
              {grammarStateFor(actionMenu.id).error ? (
                <div className="message-menu-error">{grammarStateFor(actionMenu.id).error}</div>
              ) : null}
              
              {/* 文法檢查結果 */}
              {grammarStateFor(actionMenu.id).result ? (
                <div className="message-menu-result message-menu-result--grammar">
                  {/* 文法檢查狀態 */}
                  <div
                    className={`message-menu-grammar-status ${
                      grammarStateFor(actionMenu.id).result?.is_correct
                        ? 'message-menu-grammar-status--ok'
                        : 'message-menu-grammar-status--issue'
                    }`}
                  >
                    {grammarStateFor(actionMenu.id).result?.is_correct
                      ? '表達得很好！'
                      : '發現可改進之處。'}
                  </div>
                  
                  {/* 建議修正（總是顯示） */}
                  {grammarStateFor(actionMenu.id).result?.suggestion ? (
                    <div className="message-menu-grammar-suggestion">
                      {'建議句子：'}
                      <span className="message-menu-grammar-suggestion__text">
                        {grammarStateFor(actionMenu.id).result?.suggestion}
                      </span>
                    </div>
                  ) : null}
                  
                  {/* 文法回饋說明 */}
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
      {/* 字典彈出視窗 */}
      {popover ? (
        <div
          className="dictionary-popover word-popover chat-word-popover anim-scale-in"
          style={{ top: popover.position.top, left: popover.position.left }}
          role="dialog"
          aria-live="polite"
          onClick={(event) => event.stopPropagation()}
        >
          {/* 彈出視窗標題 */}
          <div className="dictionary-popover__header word-popover__header chat-word-popover__header">
            <div className="dictionary-popover__title">
              <span className="dictionary-popover__headword">{popover.entry?.headword || popover.word}</span>
              {popover.entry?.part_of_speech ? (
                <span className="dictionary-popover__pos">{popover.entry.part_of_speech}</span>
              ) : null}
            </div>
            <div className="dictionary-popover__actions">
              <button 
                type="button" 
                className="dictionary-popover__speak" 
                onClick={(event) => {
                  event.stopPropagation()
                  const utterance = new SpeechSynthesisUtterance(popover.entry?.headword || popover.word)
                  utterance.lang = 'en-US'
                  utterance.rate = 0.8
                  window.speechSynthesis.speak(utterance)
                }}
                aria-label="朗讀單字"
                title="朗讀單字"
              >
                🔊
              </button>
              <button 
                type="button" 
                className="dictionary-popover__close word-popover__close chat-word-popover__close" 
                onClick={handleBackdropClick} 
                aria-label="關閉"
              >
                ×
              </button>
            </div>
          </div>
          
          {/* 彈出視窗內容 */}
          <div className="dictionary-popover__body word-popover__body chat-word-popover__body">
            {popover.loading ? (
              // 載入中狀態
              <div className="dictionary-popover__loading">
                <span className="dictionary-popover__spinner"></span>
                查詢中...
              </div>
            ) : popover.error ? (
              // 錯誤狀態
              <div className="dictionary-popover__error">
                {popover.error}
              </div>
            ) : popover.entry ? (
              // 字典資料
              <div className="dictionary-entry">
                {/* 定義區塊 */}
                <div className="dictionary-definition-section">
                  <div className="dictionary-section__title">定義</div>
                  <div className="dictionary-definition">
                    {popover.entry.definition.split(/\n+/).map((line, index) => (
                      <p key={index}>{line}</p>
                    ))}
                  </div>
                </div>
                
                {/* 例句區塊 */}
                {popover.entry.examples && popover.entry.examples.length ? (
                  <div className="dictionary-examples-section">
                    <div className="dictionary-section__title">例句</div>
                    <ul className="dictionary-examples">
                      {popover.entry.examples.map((example, index) => {
                        // 分割英文和中文（以換行符號分隔）
                        const parts = example.split('\n')
                        const englishPart = parts[0] || example
                        const chinesePart = parts[1] || ''
                        
                        return (
                          <li key={index} className="dictionary-examples__item">
                            <span className="dictionary-examples__bullet">•</span>
                            <div className="dictionary-examples__text">
                              <div className="dictionary-examples__english">{englishPart}</div>
                              {chinesePart && (
                                <div className="dictionary-examples__chinese">{chinesePart}</div>
                              )}
                            </div>
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : (
              // 無資料狀態
              <div className="dictionary-popover__no-data">查無資料</div>
            )}
          </div>
        </div>
      ) : null}
      {/* 捲動到底部按鈕（當未在底部時顯示） */}
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
