import { useState, useEffect } from 'react'
import { getVendors } from '../api/client'

const typeLabels = {
  chain:       'Chain',
  independent: 'Independent',
  specialty:   'Specialty',
  wholesale:   'Wholesale',
}

/* Outdoor lifestyle palette — dots and badges */
const typeBadge = {
  chain:       'bg-sky/15 text-sky border border-sky/30',
  independent: 'bg-forest/15 text-forest border border-forest/30',
  specialty:   'bg-ember/15 text-ember border border-ember/30',
  wholesale:   'bg-amber/15 text-amber border border-amber/30',
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
    <div className="px-4 py-5">
      <h1 className="font-display text-2xl text-espresso uppercase mb-1 tracking-wide">Stores</h1>
      <p className="text-bark text-sm mb-5">All verified vendors in the Memphis area.</p>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 glass rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : vendors.length === 0 ? (
        <p className="text-driftwood text-center py-10">No stores listed yet.</p>
      ) : (
        <div className="space-y-2">
          {vendors.map((v) => (
            <div key={v.id} className="glass-card px-4 py-3 flex items-center justify-between">
              <div>
                <p className="font-semibold text-espresso text-sm">{v.name}</p>
                <p className="text-xs text-driftwood mt-0.5">
                  {v.city}, {v.state}
                </p>
              </div>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${typeBadge[v.type] || 'bg-driftwood/10 text-driftwood border border-driftwood/20'}`}>
                {typeLabels[v.type] || v.type}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
