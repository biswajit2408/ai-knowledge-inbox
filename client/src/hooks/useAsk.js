import { useCallback, useRef, useState } from 'react'
import { api } from '@/api/client'

// Sends questions and keeps the latest answer. If a new question is asked
// before the previous answer arrives, the older (stale) response is ignored.
export function useAsk() {
  const [result, setResult] = useState(null)
  const [isAsking, setIsAsking] = useState(false)
  const [error, setError] = useState(null)
  const latestRequest = useRef(0)

  const ask = useCallback(async (question) => {
    const requestNumber = ++latestRequest.current
    const isLatest = () => requestNumber === latestRequest.current

    setIsAsking(true)
    setError(null)
    try {
      const data = await api.query(question)
      if (isLatest()) setResult({ id: requestNumber, question, ...data })
    } catch (err) {
      if (isLatest()) {
        setError(err)
        setResult(null)
      }
    } finally {
      if (isLatest()) setIsAsking(false)
    }
  }, [])

  return { result, isAsking, error, ask }
}
