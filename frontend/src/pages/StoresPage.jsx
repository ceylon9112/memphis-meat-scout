import { useState, useEffect } from 'react'
import { getVendors } from '../api/client'

const typeLabels = {
  chain: 'Chain',
  independent: 'Independent',
  specialty: 'Specialty',
  wholesale: 'Wholesale',
}

const typeDots = {
  chain: 'bg-blue-400',
  independent: 'bg-green-500',
  specialty: 'bg-burnt-orange',
  wholesale: 'bg-purple-500',
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
      <h1 className="font-display text-2xl text-charcoal uppercase mb-1">Stores</h1>
      <p className="text-ash text-sm mb-5">All verified vendors in the Memphis area.</p>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 bg-white rounded-xl animate-pulse" />
          ))}
        </div>
      ) : vendors.length === 0 ? (
        <p className="text-ash text-center py-8">No stores listed yet.</p>
      ) : (
        <div className="space-y-2">
          {vendors.map((v) => (
            <div
              key={v.id}
              className="bg-white rounded-xl px-4 py-3 border border-cream/80 flex items-center justify-between"
            >
              <div>
                <p className="font-medium text-charcoal text-sm">{v.name}</p>
                <p className="text-xs text-ash mt-0.5">
                  {v.city}, {v.state}
                </p>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${typeDots[v.type] || 'bg-gray-400'}`} />
                <span className="text-xs text-ash">{typeLabels[v.type] || v.type}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
