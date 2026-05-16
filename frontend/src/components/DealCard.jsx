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

export default function DealCard({ deal }) {
  const { vendor_name, cut_name, price, price_unit, verified_date, notes, category } = deal

  const categoryColors = {
    beef: 'bg-red-100 text-red-800',
    pork: 'bg-pink-100 text-pink-800',
    poultry: 'bg-yellow-100 text-yellow-800',
    seafood: 'bg-blue-100 text-blue-800',
    other: 'bg-gray-100 text-gray-700',
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-cream/80 overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-display text-lg leading-tight text-charcoal truncate">
              {cut_name}
            </h3>
            <p className="text-sm text-ash mt-0.5 truncate">{vendor_name}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="font-display text-2xl text-burnt-orange leading-tight">
              ${Number(price).toFixed(2)}
              <span className="text-sm text-ash font-body font-normal">
                {UNIT_LABELS[price_unit] || ''}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${categoryColors[category] || categoryColors.other}`}>
            {category}
          </span>
          <span className="text-xs text-ash">
            ✓ Verified {formatDate(verified_date)}
          </span>
        </div>

        {notes && (
          <p className="mt-2 text-xs text-ash italic border-t border-cream pt-2 leading-relaxed">
            {notes}
          </p>
        )}
      </div>
    </div>
  )
}
