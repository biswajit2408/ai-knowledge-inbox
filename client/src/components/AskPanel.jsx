import { Loader2, Send } from 'lucide-react'
import { useState } from 'react'

import { AnswerView } from '@/components/AnswerView'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { useAsk } from '@/hooks/useAsk'

export function AskPanel() {
  const { result, isAsking, error, ask } = useAsk()
  const [question, setQuestion] = useState('')

  function submit() {
    const trimmed = question.trim()
    if (trimmed && !isAsking) ask(trimmed)
  }

  function handleSubmit(event) {
    event.preventDefault()
    submit()
  }

  // Enter asks; Shift+Enter adds a new line.
  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask your inbox</CardTitle>
        <CardDescription>Answers use only what you have saved, with numbered citations.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <Textarea
            rows={2}
            className="max-h-40 min-w-0 flex-1"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. What did I save about RAG?"
            maxLength={1000}
            aria-label="Question"
          />
          <Button type="submit" className="self-end" disabled={isAsking || !question.trim()}>
            {isAsking ? <Loader2 className="animate-spin" /> : <Send />}
            Ask
          </Button>
        </form>

        <ErrorMessage error={error} />
        {isAsking && <p className="text-muted-foreground text-sm">Searching your saved content and writing an answer…</p>}
        {!isAsking && result && <AnswerView key={result.id} result={result} />}
      </CardContent>
    </Card>
  )
}
