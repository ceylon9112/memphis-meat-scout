import { useState } from 'react'
import { flagDeal } from '../api/client'

const UNIT_LABELS = {
  per_lb:   '/lb',
  per_unit: '/unit',
  per_pack: '/pack',
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const [, m, d] = dateStr.split('-')
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `${months[parseInt(m, 10) - 1]} ${parseInt(d, 10)}`
}

const categoryStyles = {
  beef:    { pill: 'bg-ember/12 text-ember border border-ember/30 font-semibold',         accent: '#C8471A' },
  pork:    { pill: 'bg-rose-500/12 text-rose-700 border border-rose-400/30 font-semibold', accent: 'rgba(244,63,94,0.08)' },
  poultry: { pill: 'bg-amber/12 text-amber border border-amber/30 font-semibold',         accent: 'rgba(196,132,26,0.08)' },
  seafood: { pill: 'bg-sky/12 text-sky border border-sky/30 font-semibold',               accent: 'rgba(91,143,168,0.08)' },
  other:   { pill: 'bg-forest/12 text-forest border border-forest/30 font-semibold',      accent: 'rgba(74,124,89,0.06)' },
}

const FLAG_KEY = 'mms_flagged'

function hasFlagged(id) {
  try { return JSON.parse(localStorage.getItem(FLAG_KEY) || '[]').includes(id) } catch { return false }
}
function markFlagged(id) {
  try {
    const list = JSON.parse(localStorage.getItem(FLAG_KEY) || '[]')
    if (!list.includes(id)) localStorage.setItem(FLAG_KEY, JSON.stringify([...list, id]))
  } catch {}
}

export default function DealCard({ deal }) {
  const { id, vendor_name, cut_name, price, price_unit, verified_date, notes, category } = deal
  const styles = categoryStyles[category] || categoryStyles.other

  const [flagState, setFlagState] = useState(hasFlagged(id) ? 'done' : 'idle')

  const handleFlag = async (e) => {
    e.stopPropagation()
    if (flagState !== 'idle') return
    setFlagState('sending')
    try {
      await flagDeal(id)
      markFlagged(id)
      setFlagState('done')
    } catch {
      setFlagState('idle')
    }
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">

          <div className="flex-1 min-w-0">
            <h3 className="font-display text-lg leading-tight text-espresso truncate">
              {cut_name}
            </h3>
            <p className="text-sm text-bark mt-0.5 truncate">{vendor_name}</p>
          </div>

          <div className="text-right shrink-0">
            <p className="font-display text-2xl text-ember leading-tight">
              ${Number(price).toFixed(2)}
              <span className="text-sm text-driftwood font-body font-normal ml-0.5">
                {UNIT_LABELS[price_unit] || ''}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <span className={`text-xs px-2.5 py-0.5 rounded-full capitalize ${styles.pill}`}>
            {category}
          </span>
          <div className="flex items-center gap-3">
            <span className="text-xs text-driftwood flex items-center gap-1">
              <span className="text-forest">✓</span> Verified {formatDate(verified_date)}
            </span>
            {/* Community flag — non-intrusive, tucked next to date */}
            <button
              onClick={handleFlag}
              disabled={flagState !== 'idle'}
              title={flagState === 'done' ? 'Thanks for the feedback!' : 'Report incorrect info'}
              className={`text-xs transition-colors ${
                flagState === 'done'
                  ? 'text-driftwood/40 cursor-default'
                  : 'text-driftwood/40 hover:text-amber active:scale-90'
              }`}
              aria-label="Report deal"
            >
              {flagState === 'sending' ? '…' : flagState === 'done' ? '⚑' : '⚐'}
            </button>
          </div>
        </div>

        {notes && (
          <p className="mt-2.5 text-xs text-bark/80 italic border-t border-espresso/[0.07] pt-2.5 leading-relaxed">
            {notes}
          </p>
        )}
      </div>
    </div>
  )
}
