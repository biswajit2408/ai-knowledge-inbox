import { useState } from 'react'

import { AnswerText } from '@/components/AnswerText'
import { SourceCard } from '@/components/SourceCard'
import { pluralize } from '@/lib/format'

export function AnswerView({ result }) {
  const [highlighted, setHighlighted] = useState(null)

  const citedSources = result.sources.filter((s) => s.cited)
  const otherSources = result.sources.filter((s) => !s.cited)
  const citableNumbers = new Set(citedSources.map((s) => s.number))

  function showSource(number) {
    setHighlighted(number)
    document.getElementById(`source-${number}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-muted-foreground text-sm">Q: {result.question}</p>
      <AnswerText text={result.answer} citableNumbers={citableNumbers} onCite={showSource} />

      {citedSources.length > 0 && (
        <section className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Sources</h3>
          <ol className="flex flex-col gap-2">
            {citedSources.map((source) => (
              <SourceCard key={source.number} source={source} isHighlighted={highlighted === source.number} />
            ))}
          </ol>
        </section>
      )}

      {otherSources.length > 0 && (
        <details className="group">
          <summary className="text-muted-foreground hover:text-foreground cursor-pointer text-sm">
            {pluralize(otherSources.length, 'other retrieved chunk')} (not cited)
          </summary>
          <ol className="mt-2 flex flex-col gap-2">
            {otherSources.map((source) => (
              <SourceCard key={source.number} source={source} isHighlighted={false} />
            ))}
          </ol>
        </details>
      )}
    </div>
  )
}
