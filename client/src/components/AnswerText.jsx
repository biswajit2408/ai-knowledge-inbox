// Renders the LLM's plain-text answer: "- " lines become a list, and [n]
// citation markers become buttons that jump to source n.

const CITATION_SPLIT = /(\[\d+\])/
const CITATION = /^\[(\d+)\]$/
const LIST_ITEM = /^[-*•]\s+/

export function AnswerText({ text, citableNumbers, onCite }) {
  const blocks = toBlocks(text.replace(/\*\*/g, ''))

  const renderInline = (line) =>
    line.split(CITATION_SPLIT).map((part, index) => {
      const number = Number(part.match(CITATION)?.[1])
      if (!citableNumbers.has(number)) return part
      return (
        <button
          key={index}
          type="button"
          onClick={() => onCite(number)}
          title={`Show source ${number}`}
          className="bg-primary text-primary-foreground hover:bg-primary/80 mx-0.5 inline-flex size-5 -translate-y-px items-center justify-center rounded text-[11px] font-semibold align-middle"
        >
          {number}
        </button>
      )
    })

  return (
    <div className="flex flex-col gap-2 leading-relaxed break-words">
      {blocks.map((block, index) =>
        block.type === 'list' ? (
          <ul key={index} className="ml-5 list-disc space-y-1">
            {block.items.map((item, i) => (
              <li key={i}>{renderInline(item)}</li>
            ))}
          </ul>
        ) : (
          <p key={index}>{renderInline(block.text)}</p>
        ),
      )}
    </div>
  )
}

// Groups lines into paragraphs and lists.
function toBlocks(text) {
  const blocks = []
  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim()
    if (!line) continue
    if (LIST_ITEM.test(line)) {
      const last = blocks.at(-1)
      const item = line.replace(LIST_ITEM, '')
      if (last?.type === 'list') last.items.push(item)
      else blocks.push({ type: 'list', items: [item] })
    } else {
      blocks.push({ type: 'paragraph', text: line })
    }
  }
  return blocks
}
