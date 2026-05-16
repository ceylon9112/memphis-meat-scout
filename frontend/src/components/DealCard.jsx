const UNIT_LABELS = {
  per_lb: '/lb',
  per_unit: '/unit',
  per_pack: '/pack',
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `${months[parseInt(m, 10) - 1]} ${parseInt(d, 10)}`
}

const categoryStyles = {
  beef:    { pill: 'bg-red-500/20 text-red-300 border border-red-500/25',    glow: 'rgba(239,68,68,0.15)' },
  pork:    { pill: 'bg-pink-500/20 text-pink-300 border border-pink-500/25',  glow: 'rgba(236,72,153,0.12)' },
  poultry: { pill: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/25', glow: 'rgba(234,179,8,0.12)' },
  seafood: { pill: 'bg-blue-500/20 text-blue-300 border border-blue-500/25',  glow: 'rgba(59,130,246,0.12)' },
  other:   { pill: 'bg-white/10 text-cream/60 border border-white/10',        glow: 'rgba(255,255,255,0.05)' },
}

export default function DealCard({ deal }) {
  const { vendor_name, cut_name, price, price_unit, verified_date, notes, category } = deal
  const styles = categoryStyles[category] || categoryStyles.other

  return (
    <div
      className="glass-card overflow-hidden"
      style={{ boxShadow: `0 4px 24px rgba(0,0,0,0.35), 0 0 40px ${styles.glow}, inset 0 1px 0 rgba(255,255,255,0.1)` }}
    >
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-display text-lg leading-tight text-cream truncate drop-shadow-sm">
              {cut_name}
            </h3>
            <p className="text-sm text-cream/50 mt-0.5 truncate">{vendor_name}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="font-display text-2xl text-burnt-orange leading-tight drop-shadow-[0_0_8px_rgba(200,71,26,0.5)]">
              ${Number(price).toFixed(2)}
              <span className="text-sm text-cream/40 font-body font-normal">
                {UNIT_LABELS[price_unit] || ''}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full capitalize ${styles.pill}`}>
            {category}
          </span>
          <span className="text-xs text-cream/35">
            ✓ Verified {formatDate(verified_date)}
          </span>
        </div>

        {notes && (
          <p className="mt-2.5 text-xs text-cream/45 italic border-t border-white/[0.08] pt-2.5 leading-relaxed">
            {notes}
          </p>
        )}
      </div>
    </div>
  )
}
