import { useState, useEffect } from 'react'
import { getVendors } from '../api/client'

const typeLabels = {
  chain: 'Chain',
  independent: 'Independent',
  specialty: 'Specialty',
  wholesale: 'Wholesale',
}

const typeDots = {
  chain: 'bg-blue-400 shadow-[0_0_6px_rgba(96,165,250,0.6)]',
  independent: 'bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.6)]',
  specialty: 'bg-burnt-orange shadow-[0_0_6px_rgba(200,71,26,0.6)]',
  wholesale: 'bg-purple-400 shadow-[0_0_6px_rgba(167,139,250,0.6)]',
}

export default function StoresPage() {
  const [vendors, setVendors] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getVendors()
      .then(setVendors)
      .catch(() => setVendors([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="px-4 py-4">
      <h1 className="font-display text-2xl text-cream uppercase mb-1 drop-shadow-sm">Stores</h1>
      <p className="text-cream/45 text-sm mb-5">All verified vendors in the Memphis area.</p>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 glass rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : vendors.length === 0 ? (
        <p className="text-cream/40 text-center py-8">No stores listed yet.</p>
      ) : (
        <div className="space-y-2">
          {vendors.map((v) => (
            <div
              key={v.id}
              className="glass-card px-4 py-3 flex items-center justify-between"
            >
              <div>
                <p className="font-medium text-cream text-sm">{v.name}</p>
                <p className="text-xs text-cream/40 mt-0.5">
                  {v.city}, {v.state}
                </p>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${typeDots[v.type] || 'bg-cream/40'}`} />
                <span className="text-xs text-cream/40">{typeLabels[v.type] || v.type}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
