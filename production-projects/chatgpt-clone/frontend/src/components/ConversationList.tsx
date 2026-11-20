// Glue code not shown in the lesson: the Build lesson's Step 2 gives the
// conversation CRUD endpoints and Step 5 gives the `Chat` component, but
// never wires a `conversationId` into it. This is the minimal sidebar that
// does that -- list, create, select, delete.
import { useEffect, useState } from 'react'

interface Conversation {
  id: string
  title: string
  model: string
  created_at: string
  updated_at: string
}

export function ConversationList({
  selectedId,
  onSelect,
}: {
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const [conversations, setConversations] = useState<Conversation[]>([])

  async function refresh() {
    const res = await fetch('/api/conversations')
    setConversations(await res.json())
  }

  useEffect(() => {
    refresh()
  }, [])

  async function createConversation() {
    const res = await fetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    const data = await res.json()
    await refresh()
    onSelect(data.id)
  }

  async function deleteConversation(id: string) {
    await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
    await refresh()
    if (selectedId === id) onSelect('')
  }

  return (
    <div className="w-64 border-r dark:border-gray-700 flex flex-col h-screen">
      <div className="p-3 border-b dark:border-gray-700">
        <button
          className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg"
          onClick={createConversation}
        >
          + New Chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {conversations.map(c => (
          <div
            key={c.id}
            className={`flex items-center justify-between px-3 py-2 cursor-pointer ${
              c.id === selectedId ? 'bg-gray-100 dark:bg-gray-800' : ''
            }`}
            onClick={() => onSelect(c.id)}
          >
            <span className="truncate">{c.title}</span>
            <button
              className="text-gray-400 hover:text-red-500 px-1"
              onClick={e => {
                e.stopPropagation()
                deleteConversation(c.id)
              }}
            >
              x
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
