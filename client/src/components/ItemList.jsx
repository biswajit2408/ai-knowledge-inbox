import { ErrorMessage } from '@/components/ErrorMessage'
import { SourceBadge } from '@/components/SourceBadge'
import { Badge } from '@/components/ui/badge'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { pluralize } from '@/lib/format'

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export function ItemList({ items, isLoading, error, onRetry }) {
  const isEmpty = !isLoading && !error && items.length === 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Saved items</CardTitle>
        <CardAction>
          <Badge variant="secondary">{items.length}</Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <ErrorMessage error={error} onRetry={onRetry} />
        {isLoading && items.length === 0 && <p className="text-muted-foreground text-sm">Loading…</p>}
        {isEmpty && <p className="text-muted-foreground text-sm">Nothing saved yet. Add a note or a URL above.</p>}

        <ul className="divide-y">
          {items.map((item) => (
            <ItemRow key={item.id} item={item} />
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

function ItemRow({ item }) {
  return (
    <li className="flex min-w-0 flex-col gap-1.5 py-3 first:pt-0 last:pb-0">
      <div className="flex min-w-0 items-center gap-2">
        <SourceBadge type={item.source_type} />
        <span className="min-w-0 truncate font-medium" title={item.title}>
          {item.title}
        </span>
      </div>
      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="min-w-0 truncate text-sm text-blue-700 hover:underline"
        >
          {item.url}
        </a>
      )}
      <p className="text-muted-foreground line-clamp-2 text-sm">{item.content_preview}</p>
      <p className="text-muted-foreground text-xs">
        {dateFormat.format(new Date(item.created_at))} · {pluralize(item.chunk_count, 'chunk')} ·{' '}
        {item.content_length.toLocaleString()} characters
      </p>
    </li>
  )
}
