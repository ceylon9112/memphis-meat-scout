import { useState, useEffect } from 'react'
import { getVendors } from '../api/client'
import { useZipPreference } from '../hooks/useZipPreference'
import ZipBar from '../components/ZipBar'

const typeLabels = {
  chain:       'Chain',
  independent: 'Independent',
  specialty:   'Specialty',
  wholesale:   'Wholesale',
}

const typeBadge = {
  chain:       'bg-sky/15 text-sky border border-sky/30',
  independent: 'bg-forest/15 text-forest border border-forest/30',
  specialty:   'bg-ember/15 text-ember border border-ember/30',
  wholesale:   'bg-amber/15 text-amber border border-amber/30',
}

export default function StoresPage() {
  const [vendors, setVendors] = useState([])
  const [loading, setLoading] = useState(true)
  const [zip, setZip] = useZipPreference()

  useEffect(() => {
    setLoading(true)
    const params = zip ? { zip } : {}
    getVendors(params)
      .then(setVendors)
      .catch(() => setVendors([]))
      .finally(() => setLoading(false))
  }, [zip])

  const handleZipChange = (newZip) => setZip(newZip)

  return (
    <div>
      <ZipBar zip={zip} onZip={handleZipChange} />

      <div className="px-4 py-5">
        <h1 className="font-display text-2xl text-espresso uppercase mb-1 tracking-wide">Stores</h1>
        <p className="text-bark text-sm mb-5">
          {zip
            ? `Verified vendors within 50 miles of ${zip}, sorted by distance.`
            : 'All verified vendors — enter a zip code above to filter by location.'}
        </p>

        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 glass rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : vendors.length === 0 ? (
          <p className="text-driftwood text-center py-10">
            {zip ? `No stores found within 50 miles of ${zip}.` : 'No stores listed yet.'}
          </p>
        ) : (
          <div className="space-y-2">
            {vendors.map((v) => (
              <div
                key={v.id}
                className={`glass-card px-4 py-3 flex items-center justify-between ${v.featured ? 'ring-1 ring-ember/30' : ''}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    {v.featured && (
                      <span className="text-ember text-xs" title="Featured Partner">★</span>
                    )}
                    <p className="font-semibold text-espresso text-sm truncate">{v.name}</p>
                  </div>
                  <p className="text-xs text-driftwood mt-0.5">
                    {v.address ? `${v.address}, ` : ''}{v.city}, {v.state}
                    {v.zip_code ? ` ${v.zip_code}` : ''}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-2 shrink-0">
                  {v.distance_miles != null && (
                    <span className="text-xs text-driftwood whitespace-nowrap">
                      {v.distance_miles} mi
                    </span>
                  )}
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${typeBadge[v.type] || 'bg-driftwood/10 text-driftwood border border-driftwood/20'}`}>
                    {typeLabels[v.type] || v.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
