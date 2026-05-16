import { useState, useCallback } from 'react'

const STORAGE_KEY = 'mms_zip'
const DEFAULT_ZIP = ''

export function useZipPreference() {
  const [zip, setZipState] = useState(() => localStorage.getItem(STORAGE_KEY) || DEFAULT_ZIP)

  const setZip = useCallback((value) => {
    const trimmed = (value || '').trim()
    if (trimmed) {
      localStorage.setItem(STORAGE_KEY, trimmed)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
    setZipState(trimmed)
  }, [])

  return [zip, setZip]
}
