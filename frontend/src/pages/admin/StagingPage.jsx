import { useState, useEffect, useCallback } from 'react'
import {
  getStagingStatus, getStagedDeals, runDiscovery,
  approveStaged, dismissStaged, bulkDismiss, clearDismissed, autoApprove,
  getNewStores, activateVendorStub, dismissVendorStub,
  adminGetVendors, adminGetCuts,
} from '../../api/client'
import AdminModal from '../../components/AdminModal'

const UNIT_OPTIONS = [
  { value: 'per_lb',   label: 'Per lb' },
  { value: 'per_unit', label: 'Per unit' },
  { value: 'per_pack', label: 'Per pack' },
]

const SOURCE_COLORS = {
  kroger:     'bg-blue-100 text-blue-800',
  walmart:    'bg-yellow-100 text-yellow-800',
  flipp:      'bg-purple-100 text-purple-800',
  ramons:     'bg-red-100 text-red-800',
  traderjoes: 'bg-teal-100 text-teal-800',
  wholefoods: 'bg-green-100 text-green-800',
  freshmarket:'bg-orange-100 text-orange-800',
}

const CONF_COLOR = (c) => c >= 0.8 ? 'text-green-600' : c >= 0.5 ? 'text-amber-600' : 'text-red-500'
const CONF_BAND  = (c) => c >= 0.8 ? 'High'           : c >= 0.5 ? 'Medium'         : 'Low'

const today = () => new Date().toISOString().split('T')[0]

const US_STATES = ['AL','AR','FL','GA','KY','LA','MO','MS','NC','OK','SC','TN','TX','VA']
const VTYPES    = ['chain','independent','specialty','wholesale']

// ─── Approve modal ────────────────────────────────────────────────────────────

function ApproveModal({ staged, vendors, cuts, onApprove, onClose }) {
  // Pre-select vendor by store_name match
  const guessVendor = useCallback(() => {
    if (!staged.store_name) return ''
    const sn = staged.store_name.toLowerCase()
    const match = vendors.find(v => v.active && sn.includes(v.name.toLowerCase()))
    return match?.id || ''
  }, [staged, vendors])

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

  useEffect(() => {
    const vId = guessVendor()
    if (staged.cut_name_matched && staged.match_confidence >= 0.5) {
      const matchedCut = cuts.find(c => c.name === staged.cut_name_matched && c.active)
      setForm(f => ({ ...f, vendor_id: vId, cut_id: matchedCut?.id || '' }))
    } else {
      setForm(f => ({ ...f, vendor_id: vId }))
    }
  }, [staged, cuts, guessVendor])

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
      <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm">
        <p className="font-medium text-charcoal">{staged.cut_name_raw}</p>
        <p className="text-ash mt-0.5">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full mr-2 ${SOURCE_COLORS[staged.source] || 'bg-gray-100 text-gray-700'}`}>
            {staged.source}
          </span>
          {staged.store_name} · Found {staged.found_date}
          {staged.sale_end_date && ` · Sale ends ${staged.sale_end_date}`}
        </p>
        {staged.cut_name_matched && (
          <p className={`text-xs mt-1 ${CONF_COLOR(staged.match_confidence)}`}>
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
              <option key={v.id} value={v.id}>{v.name} — {v.city}, {v.state}</option>
            ))}
          </select>
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

// ─── Staged deal row ──────────────────────────────────────────────────────────

function StagedRow({ item, onApprove, onDismiss }) {
  return (
    <tr className="hover:bg-gray-50 border-b border-gray-50">
      <td className="px-3 py-3">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${SOURCE_COLORS[item.source] || 'bg-gray-100 text-gray-700'}`}>
          {item.source}
        </span>
      </td>
      <td className="px-3 py-3 text-sm text-ash">
        <span>{item.store_name}</span>
        {item.source_zip && <span className="ml-1 text-xs text-gray-400">{item.source_zip}</span>}
      </td>
      <td className="px-3 py-3">
        <p className="text-sm font-medium text-charcoal leading-tight">{item.cut_name_raw}</p>
        {item.cut_name_matched ? (
          <p className={`text-xs mt-0.5 ${CONF_COLOR(item.match_confidence)}`}>
            → {item.cut_name_matched} ({Math.round(item.match_confidence * 100)}% · {CONF_BAND(item.match_confidence)})
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
      <td className="px-3 py-3 text-xs text-ash whitespace-nowrap">
        {item.found_date}
        {item.sale_end_date && <span className="block text-gray-400">ends {item.sale_end_date}</span>}
      </td>
      <td className="px-3 py-3">
        {onApprove && onDismiss && (
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
        )}
      </td>
    </tr>
  )
}

// ─── New store card ───────────────────────────────────────────────────────────

function NewStoreCard({ stub, onActivate, onDismiss }) {
  const [form, setForm] = useState({
    name:     stub.name,
    city:     stub.city,
    state:    stub.state,
    type:     stub.type || 'chain',
    zip_code: stub.zip_code || '',
  })
  const [saving, setSaving] = useState(false)
  const [dismissing, setDismissing] = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleActivate = async () => {
    setSaving(true)
    try { await onActivate({ stub_id: stub.id, ...form }) }
    finally { setSaving(false) }
  }

  const handleDismiss = async () => {
    if (!confirm(`Dismiss "${stub.name}" and its ${stub.deal_count} deal(s)?`)) return
    setDismissing(true)
    try { await onDismiss(stub.id) }
    finally { setDismissing(false) }
  }

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm space-y-3">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-charcoal">{stub.name}</p>
          <p className="text-xs text-ash mt-0.5">
            Auto-discovered · <strong className="text-burnt-orange">{stub.deal_count}</strong> deal{stub.deal_count !== 1 ? 's' : ''} waiting
          </p>
        </div>
        <span className="text-xs bg-amber-50 text-amber-700 border border-amber-200 rounded-full px-2 py-0.5 shrink-0">
          New Store
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <label className="block text-xs text-ash mb-1">Store Name</label>
          <input value={form.name} onChange={set('name')}
            className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-burnt-orange" />
        </div>
        <div>
          <label className="block text-xs text-ash mb-1">City</label>
          <input value={form.city} onChange={set('city')}
            className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-burnt-orange" />
        </div>
        <div>
          <label className="block text-xs text-ash mb-1">State</label>
          <select value={form.state} onChange={set('state')}
            className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-burnt-orange">
            {US_STATES.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-ash mb-1">Type</label>
          <select value={form.type} onChange={set('type')}
            className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm capitalize focus:outline-none focus:border-burnt-orange">
            {VTYPES.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
          </select>
        </div>
      </div>

      <div className="flex gap-2 pt-1">
        <button onClick={handleActivate} disabled={saving}
          className="flex-1 min-tap bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg py-2">
          {saving ? 'Activating…' : `✓ Activate & Import ${stub.deal_count} Deal${stub.deal_count !== 1 ? 's' : ''}`}
        </button>
        <button onClick={handleDismiss} disabled={dismissing}
          className="min-tap px-3 border border-gray-200 text-gray-500 hover:text-red-500 text-sm rounded-lg py-2">
          Dismiss
        </button>
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function StagingPage() {
  const [items, setItems] = useState([])
  const [newStores, setNewStores] = useState([])
  const [status, setStatus] = useState(null)
  const [vendors, setVendors] = useState([])
  const [cuts, setCuts] = useState([])
  const [loading, setLoading] = useState(true)
  const [approveTarget, setApproveTarget] = useState(null)
  const [running, setRunning] = useState(false)
  const [tab, setTab] = useState('pending')
  const [confFilter, setConfFilter] = useState('all')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [stat, v, c, ns] = await Promise.all([
        getStagingStatus(), adminGetVendors(), adminGetCuts(), getNewStores(),
      ])
      setStatus(stat); setVendors(v); setCuts(c); setNewStores(ns)
      const staged = await getStagedDeals(tab)
      setItems(staged)
    } catch {}
    setLoading(false)
  }, [tab])

  useEffect(() => { load() }, [load])

  const handleRun = async () => {
    setRunning(true)
    try { await runDiscovery() } catch {}
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

  const handleBulkDismiss = async (maxConf) => {
    const band = maxConf < 0.5 ? 'Low (<50%)' : 'Medium (50–79%)'
    const affected = items.filter(i => i.match_confidence <= maxConf && i.status === 'pending').length
    if (!affected) return
    if (!confirm(`Dismiss all ${affected} ${band} confidence pending items?`)) return
    await bulkDismiss({ max_confidence: maxConf })
    load()
  }

  const handleClearDismissed = async () => {
    if (!confirm('Permanently delete all dismissed items?')) return
    await clearDismissed(); load()
  }

  const handleActivateVendor = async (data) => {
    await activateVendorStub(data); load()
  }

  const handleDismissStub = async (id) => {
    await dismissVendorStub(id); load()
  }

  const isRunning = running || status?.running

  // Confidence filter applied client-side for snappy UX
  const filteredItems = items.filter(i => {
    if (confFilter === 'high')   return i.match_confidence >= 0.8
    if (confFilter === 'medium') return i.match_confidence >= 0.5 && i.match_confidence < 0.8
    if (confFilter === 'low')    return i.match_confidence < 0.5
    return true
  })

  const tabs = [
    { key: 'pending',   label: 'Pending',    count: status?.pending },
    { key: 'new-stores',label: 'New Stores', count: status?.new_stores },
    { key: 'approved',  label: 'Approved',   count: null },
    { key: 'dismissed', label: 'Dismissed',  count: null },
  ]

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-5 gap-4">
        <div>
          <h1 className="font-display text-2xl text-charcoal uppercase">Deal Discovery</h1>
          <p className="text-sm text-ash mt-0.5">
            Daily discovery across {status?.markets_scanned || 8} markets · auto-approves ≥70% confidence
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          {tab === 'pending' && (status?.pending || 0) > 0 && (
            <button onClick={() => { autoApprove().then(load) }}
              className="min-tap bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-3 py-2 rounded-lg">
              Re-run Auto-Approve
            </button>
          )}
          <button onClick={handleRun} disabled={isRunning}
            className="min-tap bg-burnt-orange hover:bg-burnt-orange/90 disabled:opacity-50 text-cream font-display uppercase text-sm tracking-wide px-4 py-2 rounded-lg flex items-center gap-2">
            {isRunning ? <><span className="animate-spin">↺</span> Running…</> : <>↺ Run Now</>}
          </button>
        </div>
      </div>

      {/* Status strip */}
      {status && (
        <div className="bg-gray-50 rounded-xl px-4 py-3 mb-5 flex flex-wrap gap-4 text-sm">
          <span><strong className="text-burnt-orange">{status.pending}</strong> pending review</span>
          {status.new_stores > 0 && (
            <span className="text-amber-700 font-medium">⚑ {status.new_stores} new store{status.new_stores > 1 ? 's' : ''} discovered</span>
          )}
          {status.last_run
            ? <span className="text-ash">Last run: {new Date(status.last_run).toLocaleString()}</span>
            : <span className="text-ash">Not yet run — click "Run Now" to start.</span>}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-4 border-b border-gray-100 pb-2 flex-wrap">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`text-sm capitalize min-tap px-3 py-1 rounded-full transition-colors flex items-center gap-1.5 ${
              tab === t.key ? 'bg-burnt-orange text-cream' : 'text-ash hover:text-charcoal'
            }`}>
            {t.label}
            {t.count != null && t.count > 0 && (
              <span className={`text-xs rounded-full px-1.5 py-0.5 font-bold ${
                tab === t.key ? 'bg-white/20' : 'bg-gray-200 text-charcoal'
              }`}>{t.count}</span>
            )}
          </button>
        ))}
        {tab === 'dismissed' && items.length > 0 && (
          <button onClick={handleClearDismissed}
            className="ml-auto text-xs text-red-500 hover:underline min-tap px-2">
            Clear all
          </button>
        )}
      </div>

      {/* Confidence filter + bulk actions (only on pending tab) */}
      {tab === 'pending' && items.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-xs text-ash mr-1">Filter:</span>
          {['all','high','medium','low'].map(band => (
            <button key={band} onClick={() => setConfFilter(band)}
              className={`text-xs capitalize px-3 py-1 rounded-full transition-colors ${
                confFilter === band
                  ? band === 'high'   ? 'bg-green-100 text-green-800 font-semibold'
                  : band === 'medium' ? 'bg-amber-100 text-amber-800 font-semibold'
                  : band === 'low'    ? 'bg-red-100 text-red-700 font-semibold'
                  :                    'bg-charcoal text-cream font-semibold'
                  : 'bg-gray-100 text-ash hover:text-charcoal'
              }`}>
              {band === 'all' ? 'All' : band === 'high' ? 'High ≥80%' : band === 'medium' ? 'Medium 50–79%' : 'Low <50%'}
            </button>
          ))}
          <div className="ml-auto flex gap-2">
            <button onClick={() => handleBulkDismiss(0.499)}
              className="text-xs text-red-500 hover:underline px-2 min-tap">
              Dismiss all Low
            </button>
            <button onClick={() => handleBulkDismiss(0.799)}
              className="text-xs text-amber-600 hover:underline px-2 min-tap">
              Dismiss all Medium
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>

      ) : tab === 'new-stores' ? (
        newStores.length === 0
          ? (
            <div className="text-center py-16 text-ash">
              <p className="text-4xl mb-3">🏪</p>
              <p>No unknown stores detected. All discovered deals matched existing vendors.</p>
            </div>
          )
          : (
            <div className="grid gap-4 sm:grid-cols-2">
              {newStores.map(stub => (
                <NewStoreCard
                  key={stub.id}
                  stub={stub}
                  onActivate={handleActivateVendor}
                  onDismiss={handleDismissStub}
                />
              ))}
            </div>
          )

      ) : filteredItems.length === 0 ? (
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
                <th className="px-3 py-3 text-left">Found / Ends</th>
                <th className="px-3 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map(item => (
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
