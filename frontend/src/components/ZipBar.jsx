import { useState } from 'react'

export default function ZipBar({ zip, onZip }) {
  const [input, setInput] = useState(zip || '')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (trimmed && !/^\d{5}$/.test(trimmed)) {
      setError('Enter a valid 5-digit zip code')
      return
    }
    setError('')
    onZip(trimmed)
  }

  const handleClear = () => {
    setInput('')
    setError('')
    onZip('')
  }

  return (
    <div className="glass-light-surface border-b border-espresso/[0.06] px-4 py-2.5">
      <form onSubmit={handleSubmit} className="flex items-center gap-2 max-w-sm">
        {/* pin icon */}
        <svg className="w-4 h-4 text-ember shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>

        <div className="flex-1 relative">
          <input
            type="text"
            inputMode="numeric"
            maxLength={5}
            placeholder="Enter zip code…"
            value={input}
            onChange={(e) => { setInput(e.target.value); setError('') }}
            className="w-full glass-input rounded-lg px-3 py-1.5 text-sm placeholder-driftwood/60 focus:outline-none"
          />
          {zip && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-driftwood/60 hover:text-ember transition-colors text-xs"
              aria-label="Clear zip"
            >
              ✕
            </button>
          )}
        </div>

        <button
          type="submit"
          className="shrink-0 min-tap px-3 py-1.5 rounded-lg text-sm font-semibold pill-active"
        >
          {zip ? 'Update' : 'Search'}
        </button>
      </form>

      {error && <p className="text-red-500 text-xs mt-1 ml-6">{error}</p>}

      {zip && !error && (
        <p className="text-driftwood text-xs mt-0.5 ml-6">
          Showing deals &amp; stores within 50 mi of <span className="font-semibold text-bark">{zip}</span>
        </p>
      )}
    </div>
  )
}
