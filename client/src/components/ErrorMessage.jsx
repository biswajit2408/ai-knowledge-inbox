import { AlertCircle } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

export function ErrorMessage({ error, onRetry }) {
  if (!error) return null

  return (
    <Alert variant="destructive">
      <AlertCircle />
      <AlertTitle>{error.message}</AlertTitle>
      {(error.requestId || onRetry) && (
        <AlertDescription className="flex flex-wrap items-center gap-2">
          {error.requestId && (
            <span title="Search the server logs for this ID">Request ID: {error.requestId.slice(0, 8)}</span>
          )}
          {onRetry && (
            <Button variant="link" size="sm" className="h-auto p-0" onClick={onRetry}>
              Retry
            </Button>
          )}
        </AlertDescription>
      )}
    </Alert>
  )
}
