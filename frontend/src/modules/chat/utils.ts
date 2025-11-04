import { ChatMessage } from '../../types/api'

/** Derive a stable key for rendering chat messages in lists. */
export function getMessageKey(message: ChatMessage): string {
  return `${message.role}:${message.content}`
}
