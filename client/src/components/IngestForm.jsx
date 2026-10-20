import { CheckCircle2, Loader2 } from 'lucide-react'
import { useState } from 'react'

import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'

export function IngestForm({ onSubmit }) {
  const [mode, setMode] = useState('note')
  const [content, setContent] = useState('')
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(null)
  const [savedMessage, setSavedMessage] = useState(null)

  const hasInput = mode === 'note' ? content.trim() !== '' : url.trim() !== ''

  function switchMode(nextMode) {
    setMode(nextMode)
    setError(null)
    setSavedMessage(null)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSaving(true)
    setError(null)
    setSavedMessage(null)

    const payload = mode === 'note' ? { source_type: 'note', content } : { source_type: 'url', url: url.trim() }
    if (title.trim()) payload.title = title.trim()

    try {
      const item = await onSubmit(payload)
      const chunks = `${item.chunk_count} chunk${item.chunk_count === 1 ? '' : 's'}`
      setSavedMessage(`Saved "${item.title}" (${chunks}).`)
      setContent('')
      setUrl('')
      setTitle('')
    } catch (err) {
      setError(err)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add to inbox</CardTitle>
        <CardDescription>Save a note, or a link whose page text is fetched for you.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Tabs value={mode} onValueChange={switchMode}>
            <TabsList>
              <TabsTrigger value="note">Note</TabsTrigger>
              <TabsTrigger value="url">URL</TabsTrigger>
            </TabsList>

            <TabsContent value="note" className="flex flex-col gap-2 pt-2">
              <Label htmlFor="note-content">Note</Label>
              <Textarea
                id="note-content"
                rows={5}
                className="max-h-64"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write or paste something worth remembering…"
                maxLength={50000}
              />
            </TabsContent>

            <TabsContent value="url" className="flex flex-col gap-2 pt-2">
              <Label htmlFor="url-input">URL</Label>
              <Input
                id="url-input"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/article"
              />
            </TabsContent>
          </Tabs>

          <div className="flex flex-col gap-2">
            <Label htmlFor="item-title">
              Title <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Input
              id="item-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={mode === 'note' ? 'Defaults to the first line' : 'Defaults to the page title'}
              maxLength={200}
            />
          </div>

          <Button type="submit" className="self-start" disabled={isSaving || !hasInput}>
            {isSaving && <Loader2 className="animate-spin" />}
            {isSaving ? (mode === 'url' ? 'Fetching and indexing…' : 'Saving…') : 'Save'}
          </Button>

          <ErrorMessage error={error} />
          {savedMessage && (
            <p className="flex items-center gap-2 text-sm text-emerald-700">
              <CheckCircle2 className="size-4" />
              {savedMessage}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
