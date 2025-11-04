import { KeyboardEventHandler } from 'react'

type RecorderSnapshot = {
  isRecording: boolean
  durationSec: number
}

type ChatComposerProps = {
  input: string
  placeholder: string
  onInputChange: (value: string) => void
  onSend: () => void
  onRegenerate: () => void
  onClear: () => void
  isSending: boolean
  sendLabel: string
  regenerateLabel: string
  clearLabel: string
  streamingLabel: string
  streaming: boolean
  onStreamingChange: (value: boolean) => void
  recorder: RecorderSnapshot
  onToggleRecord: () => void
  recordLabel: string
  stopLabel: string
  recordingLabel: string
  transcribingLabel: string
  speakingLabel: string
  isTranscribing: boolean
  isSpeakingLocal: boolean
  isSpeakingBackend: boolean
  canRegenerate: boolean
  canClear: boolean
  className?: string
}

/** Present the chat input area together with recording controls and status hints. */
export default function ChatComposer({
  input,
  placeholder,
  onInputChange,
  onSend,
  onRegenerate,
  onClear,
  isSending,
  sendLabel,
  regenerateLabel,
  clearLabel,
  streamingLabel,
  streaming,
  onStreamingChange,
  recorder,
  onToggleRecord,
  recordLabel,
  stopLabel,
  recordingLabel,
  transcribingLabel,
  speakingLabel,
  isTranscribing,
  isSpeakingLocal,
  isSpeakingBackend,
  canRegenerate,
  canClear,
  className = '',
}: ChatComposerProps) {
  const statusMessages: string[] = []
  if (recorder.isRecording) {
    statusMessages.push(
      `${recordingLabel}: ${Math.floor(recorder.durationSec / 60)}:${(recorder.durationSec % 60)
        .toString()
        .padStart(2, '0')}`,
    )
  }
  if (isTranscribing) {
    statusMessages.push(transcribingLabel)
  }
  if (isSpeakingLocal || isSpeakingBackend) {
    statusMessages.push(speakingLabel)
  }

  // Submit the message on Enter while still allowing Shift+Enter for new lines.
  const handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      onSend()
    }
  }

  return (
    <div className={`chat-composer card bg-gray-900/50 border-gray-800 anim-scale-in ${className}`}>
      <textarea
        className="chat-composer__input input h-28 bg-gray-800 text-gray-100 border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-600/40 transition"
        placeholder={placeholder}
        value={input}
        onChange={(event) => onInputChange(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <div className="chat-composer__controls mt-2 flex flex-wrap items-center justify-between gap-2">
        <label className="chat-composer__streaming-toggle flex items-center gap-2 text-sm text-gray-400">
          <input
            type="checkbox"
            checked={streaming}
            onChange={(event) => onStreamingChange(event.target.checked)}
          />{' '}
          {streamingLabel}
        </label>
        <div className="chat-composer__actions flex items-center gap-2">
          <button
            className={`chat-composer__record-button rounded-full w-10 h-10 flex items-center justify-center border text-sm ${
              recorder.isRecording
                ? 'border-red-500 text-red-500 pulse-red'
                : 'border-gray-700 text-gray-300 hover:bg-gray-800 active:scale-95 transition'
            }`}
            onClick={onToggleRecord}
            title={recorder.isRecording ? stopLabel : recordLabel}
          >
            {recorder.isRecording ? 'Stop' : 'Rec'}
          </button>
          <button
            className="chat-composer__regenerate-button px-4 py-2 text-sm rounded-md border border-gray-700 text-gray-200 hover:bg-gray-800 active:scale-95 transition disabled:opacity-50"
            onClick={onRegenerate}
            disabled={isSending || !canRegenerate}
          >
            {regenerateLabel}
          </button>
          <button
            className="chat-composer__clear-button px-4 py-2 text-sm rounded-md border border-gray-700 text-gray-200 hover:bg-gray-800 active:scale-95 transition disabled:opacity-60"
            onClick={onClear}
            disabled={!canClear}
          >
            {clearLabel}
          </button>
          <button
            className="chat-composer__send-button btn active:scale-95 transition"
            onClick={onSend}
            disabled={isSending || !input.trim()}
          >
            {isSending ? '...' : sendLabel}
          </button>
        </div>
      </div>
      {statusMessages.length > 0 && (
        <div className="chat-composer__status mt-2 text-xs text-gray-400 space-y-1">
          {statusMessages.map((line, index) => (
            <div key={index} className="chat-composer__status-line">
              {line}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
