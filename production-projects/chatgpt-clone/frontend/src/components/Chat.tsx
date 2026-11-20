// From the Build lesson's Step 5, with one fix: `max-w-3/4` is not a
// Tailwind core utility (fraction values are only generated for
// width/height, not max-width) so the lesson's code silently had no
// effect; replaced with `max-w-[75%]`.
import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function Chat({ conversationId }: { conversationId: string }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamContent, setStreamContent] = useState('')
  const chatRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch(`/api/conversations/${conversationId}/messages`)
      .then(r => r.json())
      .then(data => setMessages(data.map((m: any) => ({ role: m.role, content: m.content }))))
  }, [conversationId])

  useEffect(() => {
    chatRef.current?.scrollTo(0, chatRef.current.scrollHeight)
  }, [messages, streamContent])

  async function sendMessage() {
    if (!input.trim() || streaming) return

    const userMsg: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setStreaming(true)
    setStreamContent('')

    const response = await fetch(`/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: conversationId, message: input })
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    while (reader) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.token) {
              setStreamContent(prev => prev + data.token)
            }
            if (data.full) {
              setMessages(prev => [...prev, { role: 'assistant', content: data.full }])
              setStreamContent('')
              setStreaming(false)
            }
          } catch {}
        }
      }
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <div ref={chatRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] p-3 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-800'
            }`}>
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '')
                    return !inline && match ? (
                      <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div">
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>{children}</code>
                    )
                  }
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {streaming && streamContent && (
          <div className="flex justify-start">
            <div className="max-w-[75%] p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
              <ReactMarkdown>{streamContent}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            className="flex-1 p-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Type a message..."
            disabled={streaming}
          />
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
            onClick={sendMessage}
            disabled={streaming || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
