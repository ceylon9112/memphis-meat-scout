import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getCuts } from '../api/client'

const CATEGORIES = ['beef', 'pork', 'poultry', 'seafood', 'other']

const categoryIcons = {
  beef: '🐄',
  pork: '🐷',
  poultry: '🐔',
  seafood: '🐟',
  other: '🍖',
}

export default function CutsPage() {
  const [cuts, setCuts] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCuts()
      .then(setCuts)
      .catch(() => setCuts([]))
      .finally(() => setLoading(false))
  }, [])

  const filtered = cuts.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase())
  )

  const grouped = CATEGORIES.reduce((acc, cat) => {
    const items = filtered.filter((c) => c.category === cat)
    if (items.length) acc[cat] = items
    return acc
  }, {})

  return (
    <div className="px-4 py-4">
      <h1 className="font-display text-2xl text-charcoal uppercase mb-4">Browse Cuts</h1>

      <input
        type="search"
        placeholder="Search cuts…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full bg-white border border-charcoal/20 rounded-lg px-4 py-2.5 text-sm mb-5 focus:outline-none focus:border-burnt-orange"
      />

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-12 bg-white rounded-lg animate-pulse" />
          ))}
        </div>
      ) : Object.keys(grouped).length === 0 ? (
        <p className="text-ash text-center py-8">No cuts found.</p>
      ) : (
        Object.entries(grouped).map(([cat, items]) => (
          <div key={cat} className="mb-5">
            <h2 className="font-display text-sm uppercase tracking-widest text-burnt-orange mb-2 flex items-center gap-2">
              <span>{categoryIcons[cat]}</span> {cat}
            </h2>
            <div className="space-y-1.5">
              {items.map((cut) => (
                <Link
                  key={cut.id}
                  to={`/cuts/${cut.id}`}
                  className="flex items-center justify-between bg-white rounded-lg px-4 py-3 border border-cream/80 hover:border-burnt-orange/50 hover:shadow-sm transition-all min-tap"
                >
                  <span className="text-sm font-medium text-charcoal">{cut.name}</span>
                  <span className="text-burnt-orange text-sm">→</span>
                </Link>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
