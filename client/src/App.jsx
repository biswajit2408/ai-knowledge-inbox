import { Inbox } from 'lucide-react'

import { AskPanel } from '@/components/AskPanel'
import { IngestForm } from '@/components/IngestForm'
import { ItemList } from '@/components/ItemList'
import { useItems } from '@/hooks/useItems'

export default function App() {
  const { items, isLoading, error, reload, addItem } = useItems()

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <header className="flex items-center gap-3">
        <Inbox className="size-7" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI Knowledge Inbox</h1>
          <p className="text-muted-foreground text-sm">Save notes and links, then ask questions about them.</p>
        </div>
      </header>

      {/* grid-cols-1 = minmax(0, 1fr): columns never grow wider than the screen, so long
          URLs/titles truncate instead of pushing the layout sideways. */}
      <main className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2">
        <div className="flex min-w-0 flex-col gap-6">
          <IngestForm onSubmit={addItem} />
          <ItemList items={items} isLoading={isLoading} error={error} onRetry={reload} />
        </div>
        <div className="min-w-0 lg:sticky lg:top-6">
          <AskPanel />
        </div>
      </main>
    </div>
  )
}
