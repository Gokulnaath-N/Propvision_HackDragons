import { useState, useCallback } from 'react'
import { searchListings } from '../services/api'

export function useSearch() {
  const [results,    setResults]    = useState([])
  const [intent,     setIntent]     = useState(null)
  const [filters,    setFilters]    = useState({})
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState(null)
  const [modelMeta,  setModelMeta]  = useState(null)
  const [isFirstSearch, setIsFirstSearch] = useState(true)

  const search = useCallback(async (query, extraFilters = {}) => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
  
    try {
      const data = await searchListings(query, extraFilters, isFirstSearch)
      
      setResults(data.results || [])
      setIntent(data.extracted_intent || {})
      setFilters(data.dynamic_filters || {})
      setModelMeta(data.meta || data.extracted_intent?._meta || null)
      setIsFirstSearch(false)

    } catch (err) {
      setError('Search failed. Check if backend is running.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [isFirstSearch])

  const resetSearch = useCallback(() => {
    setResults([])
    setIntent(null)
    setFilters({})
    setModelMeta(null)
    setIsFirstSearch(true)
  }, [])

  return { results, intent, filters, loading,
           error, modelMeta, search, resetSearch }
}
