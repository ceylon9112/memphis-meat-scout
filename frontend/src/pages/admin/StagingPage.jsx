import { useState, useEffect, useCallback } from 'react'
import {
  getStagingStatus, getStagedDeals, runDiscovery,
  approveStaged, dismissStaged, clearDismissed,
  adminGetVendors, adminGetCuts,
} from '../../api/client'
import AdminModal from '../../components/AdminModal'

const UNIT_OPTIONS = [
  { value: 'per_lb', label: 'Per lb' },
  { value: 'per_unit', label: 'Per unit' },
  { value: 'per_pack', label: 'Per pack' },
]

const SOURCE_COLORS = {
  kroger:     'bg-blue-100 text-blue-800',
  walmart:    'bg-yellow-100 text-yellow-800',
  flipp:      'bg-purple-100 text-purple-800',
  ramons:     'bg-red-100 text-red-800',
  traderjoes: 'bg-teal-100 text-teal-800',
  wholefoods:   'bg-green-100 text-green-800',
  freshmarket:  'bg-orange-100 text-orange-800',
}

const CONFIDENCE_COLOR = (c) => {
  if (c >= 0.8) return 'text-green-600'
  if (c >= 0.5) return 'text-amber-600'
  return 'text-red-500'
}

const today = () => new Date().toISOString().split('T')[0]

function ApproveModal({ staged, vendors, cuts, onApprove, onClose }) {
  const [form, setForm] = useState({
    vendor_id: '',
    cut_id: '',
    price: staged.price,
    price_unit: staged.price_unit,
    verified_date: staged.found_date || today(),
    notes: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // Pre-select matched cut if confidence is good
  useEffect(() => {
    if (staged.cut_name_matched && staged.match_confidence >= 0.5) {
      const matched = cuts.find(c => c.name === staged.cut_name_matched && c.active)
      if (matched) setForm(f => ({ ...f, cut_id: matched.id }))
    }
  }, [staged, cuts])

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.vendor_id || !form.cut_id) { setError('Select a vendor and cut.'); return }
    setSaving(true); setError('')
    try { await onApprove(form) }
    catch (err) { setError(err?.response?.data?.detail || 'Approval failed.') }
    finally { setSaving(false) }
  }

  return (
    <AdminModal title="Approve Deal" onClose={onClose}>
      {/* Source info */}
      <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm">
        <p className="font-medium text-charcoal">{staged.cut_name_raw}</p>
        <p className="text-ash mt-0.5">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full mr-2 ${SOURCE_COLORS[staged.source] || 'bg-gray-100 text-gray-700'}`}>
            {staged.source}
          </span>
          {staged.store_name} · Found {staged.found_date}
        </p>
        {staged.cut_name_matched && (
          <p className={`text-xs mt-1 ${CONFIDENCE_COLOR(staged.match_confidence)}`}>
            Auto-matched: <strong>{staged.cut_name_matched}</strong> ({Math.round(staged.match_confidence * 100)}% confidence)
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Vendor *</label>
          <select value={form.vendor_id} onChange={set('vendor_id')} required
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange">
            <option value="">Select vendor…</option>
            {vendors.filter(v => v.active).map(v => (
              <option key={v.id} value={v.id}>{v.name}</option>
            ))}
          </select>
          <p className="text-xs text-ash mt-1">
            If this store isn't in your vendor list, add it first via the Vendors tab.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Cut *</label>
          <select value={form.cut_id} onChange={set('cut_id')} required
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange">
            <option value="">Select cut…</option>
            {cuts.filter(c => c.active).map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-charcoal mb-1">Price</label>
            <input type="number" step="0.01" min="0" value={form.price} onChange={set('price')} required
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange" />
          </div>
          <div>
            <label className="block text-sm font-medium text-charcoal mb-1">Unit</label>
            <select value={form.price_unit} onChange={set('price_unit')}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange">
              {UNIT_OPTIONS.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}
            </select>
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium text-charcoal mb-1">Verified Date</label>
            <input type="date" value={form.verified_date} onChange={set('verified_date')}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Notes</label>
          <textarea value={form.notes} onChange={set('notes')} rows={2}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange resize-none"
            placeholder="Optional notes…" />
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <div className="flex gap-3 pt-1">
          <button type="submit" disabled={saving}
            className="flex-1 min-tap bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-display uppercase tracking-wide rounded-lg py-2.5 text-sm">
            {saving ? 'Approving…' : '✓ Approve & Publish'}
          </button>
          <button type="button" onClick={onClose}
            className="min-tap px-4 border border-gray-200 rounded-lg text-ash hover:text-charcoal text-sm">
            Cancel
          </button>
        </div>
      </form>
    </AdminModal>
  )
}

function StagedRow({ item, onApprove, onDismiss }) {
  return (
    <tr className="hover:bg-gray-50 border-b border-gray-50">
      <td className="px-3 py-3">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${SOURCE_COLORS[item.source] || 'bg-gray-100 text-gray-700'}`}>
          {item.source}
        </span>
      </td>
      <td className="px-3 py-3 text-sm text-ash">{item.store_name}</td>
      <td className="px-3 py-3">
        <p className="text-sm font-medium text-charcoal leading-tight">{item.cut_name_raw}</p>
        {item.cut_name_matched ? (
          <p className={`text-xs mt-0.5 ${CONFIDENCE_COLOR(item.match_confidence)}`}>
            → {item.cut_name_matched} ({Math.round(item.match_confidence * 100)}%)
          </p>
        ) : (
          <p className="text-xs text-red-500 mt-0.5">No match — select manually</p>
        )}
      </td>
      <td className="px-3 py-3 text-sm font-medium text-burnt-orange whitespace-nowrap">
        ${item.price.toFixed(2)}<span className="text-ash font-normal text-xs">
          {item.price_unit === 'per_lb' ? '/lb' : item.price_unit === 'per_unit' ? '/unit' : '/pack'}
        </span>
      </td>
      <td className="px-3 py-3 text-xs text-ash">{item.found_date}</td>
      <td className="px-3 py-3">
        <div className="flex gap-2 justify-end">
          <button onClick={() => onApprove(item)}
            className="text-xs bg-green-50 text-green-700 hover:bg-green-100 px-2 py-1 rounded min-tap">
            Approve
          </button>
          <button onClick={() => onDismiss(item)}
            className="text-xs bg-gray-50 text-gray-500 hover:bg-gray-100 px-2 py-1 rounded min-tap">
            Dismiss
          </button>
        </div>
      </td>
    </tr>
  )
}

export default function StagingPage() {
  const [items, setItems] = useState([])
  const [status, setStatus] = useState(null)
  const [vendors, setVendors] = useState([])
  const [cuts, setCuts] = useState([])
  const [loading, setLoading] = useState(true)
  const [approveTarget, setApproveTarget] = useState(null)
  const [running, setRunning] = useState(false)
  const [tab, setTab] = useState('pending')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [staged, stat, v, c] = await Promise.all([
        getStagedDeals(tab),
        getStagingStatus(),
        adminGetVendors(),
        adminGetCuts(),
      ])
      setItems(staged)
      setStatus(stat)
      setVendors(v)
      setCuts(c)
    } catch {}
    setLoading(false)
  }, [tab])

  useEffect(() => { load() }, [load])

  const handleRun = async () => {
    setRunning(true)
    try {
      await runDiscovery()
    } catch {}
    setRunning(false)
    await load()
  }

  const handleApprove = async (data) => {
    await approveStaged(approveTarget.id, data)
    setApproveTarget(null)
    load()
  }

  const handleDismiss = async (item) => {
    if (!confirm(`Dismiss "${item.cut_name_raw}"?`)) return
    await dismissStaged(item.id)
    load()
  }

  const handleClearDismissed = async () => {
    if (!confirm('Clear all dismissed items?')) return
    await clearDismissed()
    load()
  }

  const isRunning = running || status?.running

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h1 className="font-display text-2xl text-charcoal uppercase">Deal Discovery</h1>
          <p className="text-sm text-ash mt-0.5">
            Auto-discovered prices from weekly grocery ads (Kroger, ALDI, Walmart, Superlo, Sprouts, Costco & more), Ramon's Meat Market live pricing, Trader Joe's everyday pricing, Whole Foods Market weekly sales, and The Fresh Market weekly specials — review before publishing.
          </p>
        </div>
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="min-tap bg-burnt-orange hover:bg-burnt-orange/90 disabled:opacity-50 text-cream font-display uppercase text-sm tracking-wide px-4 py-2 rounded-lg flex items-center gap-2"
        >
          {isRunning ? (
            <><span className="animate-spin">↺</span> Running…</>
          ) : (
            <>↺ Run Now</>
          )}
        </button>
      </div>

      {/* Status strip */}
      {status && (
        <div className="bg-gray-50 rounded-xl px-4 py-3 mb-5 flex flex-wrap gap-4 text-sm">
          <span><strong className="text-burnt-orange">{status.pending}</strong> pending review</span>
          {status.last_run && (
            <span className="text-ash">
              Last run: {new Date(status.last_run).toLocaleString()}
            </span>
          )}
          {!status.last_run && (
            <span className="text-ash">Not yet run — click "Run Now" to start.</span>
          )}
          <span className="text-ash text-xs self-center">Scheduled daily at 6 AM</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-4 border-b border-gray-100 pb-2">
        {['pending', 'approved', 'dismissed'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`text-sm capitalize min-tap px-3 py-1 rounded-full transition-colors ${
              tab === t ? 'bg-burnt-orange text-cream' : 'text-ash hover:text-charcoal'
            }`}>
            {t}
          </button>
        ))}
        {tab === 'dismissed' && items.length > 0 && (
          <button onClick={handleClearDismissed}
            className="ml-auto text-xs text-red-500 hover:underline min-tap px-2">
            Clear all
          </button>
        )}
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-ash">
          <p className="text-4xl mb-3">🔍</p>
          <p>
            {tab === 'pending'
              ? 'No pending items. Run discovery to find new deals.'
              : `No ${tab} items.`}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-100 shadow-sm">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase tracking-wide text-ash">
              <tr>
                <th className="px-3 py-3 text-left">Source</th>
                <th className="px-3 py-3 text-left">Store</th>
                <th className="px-3 py-3 text-left">Product → Matched Cut</th>
                <th className="px-3 py-3 text-left">Price</th>
                <th className="px-3 py-3 text-left">Found</th>
                <th className="px-3 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <StagedRow
                  key={item.id}
                  item={item}
                  onApprove={tab === 'pending' ? setApproveTarget : undefined}
                  onDismiss={tab === 'pending' ? handleDismiss : undefined}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {approveTarget && (
        <ApproveModal
          staged={approveTarget}
          vendors={vendors}
          cuts={cuts}
          onApprove={handleApprove}
          onClose={() => setApproveTarget(null)}
        />
      )}
    </div>
  )
}
