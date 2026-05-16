import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCuts, getCutPrices } from '../api/client'
import BestPriceBadge from '../components/BestPriceBadge'
import EmptyState from '../components/EmptyState'

const UNIT_LABELS = { per_lb: '/lb', per_unit: '/unit', per_pack: '/pack' }

function formatDate(str) {
  if (!str) return ''
  const [y, m, d] = str.split('-')
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `${months[parseInt(m, 10) - 1]} ${parseInt(d, 10)}`
}

export default function CutDetailPage() {
  const { id } = useParams()
  const [cut, setCut] = useState(null)
  const [prices, setPrices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getCuts(), getCutPrices(id)])
      .then(([cuts, priceData]) => {
        setCut(cuts.find((c) => c.id === id) || null)
        setPrices(priceData)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  const cutName = cut?.name || '…'

  return (
    <div className="px-4 py-4">
      <Link to="/cuts" className="text-burnt-orange text-sm flex items-center gap-1 mb-4">
        ← All cuts
      </Link>

      <h1 className="font-display text-2xl text-charcoal uppercase mb-1">{cutName}</h1>
      {cut && (
        <p className="text-ash text-sm capitalize mb-5">{cut.category}</p>
      )}

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 bg-white rounded-xl animate-pulse" />
          ))}
        </div>
      ) : prices.length === 0 ? (
        <EmptyState message={`No current verified prices for ${cutName}. Check back soon.`} />
      ) : (
        <div className="space-y-3">
          {prices.map((deal, idx) => (
            <div
              key={deal.id}
              className={`bg-white rounded-xl p-4 border shadow-sm ${
                idx === 0 ? 'border-gold ring-1 ring-gold/40' : 'border-cream/80'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-charcoal text-sm truncate">{deal.vendor_name}</p>
                  <p className="text-xs text-ash mt-0.5">✓ Verified {formatDate(deal.verified_date)}</p>
                  {deal.notes && (
                    <p className="text-xs text-ash italic mt-1">{deal.notes}</p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <p className="font-display text-2xl text-burnt-orange leading-tight">
                    ${Number(deal.price).toFixed(2)}
                    <span className="text-sm text-ash font-body font-normal">
                      {UNIT_LABELS[deal.price_unit] || ''}
                    </span>
                  </p>
                  {idx === 0 && (
                    <div className="mt-1 flex justify-end">
                      <BestPriceBadge />
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
