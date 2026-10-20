import { useCallback, useEffect, useState } from 'react'

import { api } from '@/api/client'

// Owns the list of saved items: initial load, reload, and adding new ones.
export function useItems() {
  const [items, setItems] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await api.listItems()
      setItems(data.items)
      setError(null)
    } catch (err) {
      setError(err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  // Errors are re-thrown so the form that called this can show them.
  const addItem = useCallback(async (payload) => {
    const item = await api.ingest(payload)
    setItems((current) => [item, ...current])
    return item
  }, [])

  return { items, isLoading, error, reload, addItem }
}
