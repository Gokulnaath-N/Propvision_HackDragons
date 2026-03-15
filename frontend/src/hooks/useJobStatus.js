import { useState, useEffect, useRef } from 'react'
import { getJobStatus } from '../services/api'

export function useJobStatus(jobId) {
  const [status,   setStatus]   = useState(null)
  const [progress, setProgress] = useState(0)
  const [stage,    setStage]    = useState('')
  const [results,  setResults]  = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    intervalRef.current = setInterval(async () => {
      try {
        const data = await getJobStatus(jobId)
        setStatus(data.status)
        setProgress(data.progress || 0)
        setStage(data.current_stage || '')

        if (data.status === 'complete') {
          setResults(data.results)
          clearInterval(intervalRef.current)
        }
        if (data.status === 'failed') {
          clearInterval(intervalRef.current)
        }
      } catch (e) {
        console.error('Status poll failed:', e)
      }
    }, 2000)

    return () => clearInterval(intervalRef.current)
  }, [jobId])

  return { status, progress, stage, results }
}
