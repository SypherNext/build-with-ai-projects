import { useState } from 'react'
import { Chat } from './components/Chat'
import { ConversationList } from './components/ConversationList'

export default function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  return (
    <div className="flex">
      <ConversationList selectedId={selectedId} onSelect={id => setSelectedId(id || null)} />
      <div className="flex-1">
        {selectedId ? (
          <Chat conversationId={selectedId} />
        ) : (
          <div className="flex items-center justify-center h-screen text-gray-400">
            Select or start a new chat
          </div>
        )}
      </div>
    </div>
  )
}
