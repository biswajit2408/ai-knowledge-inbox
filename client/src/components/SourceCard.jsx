import { useState } from 'react'

import { SourceBadge } from '@/components/SourceBadge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const COLLAPSED_LENGTH = 280

export function SourceCard({ source, isHighlighted }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const isLong = source.snippet.length > COLLAPSED_LENGTH
  const snippet =
    isLong && !isExpanded ? `${source.snippet.slice(0, COLLAPSED_LENGTH).trimEnd()}…` : source.snippet

  return (
    <li
      id={`source-${source.number}`}
      className={cn(
        'bg-card flex min-w-0 flex-col gap-2 rounded-lg border p-3 transition-colors',
        isHighlighted && 'border-primary ring-primary/20 ring-2',
      )}
    >
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <span className="font-semibold">[{source.number}]</span>
        <SourceBadge type={source.source_type} />
        {source.url ? (
          <a
            href={source.url}
            target="_blank"
            rel="noreferrer"
            title={source.title}
            className="min-w-0 truncate font-medium text-blue-700 hover:underline"
          >
            {source.title}
          </a>
        ) : (
          <span className="min-w-0 truncate font-medium" title={source.title}>
            {source.title}
          </span>
        )}
        <span
          className="text-muted-foreground ml-auto shrink-0 text-xs tabular-nums"
          title="Cosine similarity between this chunk and your question"
        >
          {source.score.toFixed(2)}
        </span>
      </div>
      <p className="text-muted-foreground text-sm break-words whitespace-pre-line">{snippet}</p>
      {isLong && (
        <Button variant="link" size="sm" className="h-auto self-start p-0" onClick={() => setIsExpanded((v) => !v)}>
          {isExpanded ? 'Show less' : 'Show full chunk'}
        </Button>
      )}
    </li>
  )
}
