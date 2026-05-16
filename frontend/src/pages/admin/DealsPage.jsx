import { useState, useEffect, useCallback } from 'react'
import {
  adminGetDeals, adminGetVendors, adminGetCuts,
  adminCreateDeal, adminUpdateDeal, adminExpireDeal, adminDeleteDeal,
} from '../../api/client'
import AdminModal from '../../components/AdminModal'

const UNIT_LABELS = { per_lb: '/lb', per_unit: '/unit', per_pack: '/pack' }
const today = () => new Date().toISOString().split('T')[0]

function DealForm({ vendors, cuts, initial, onSave, onCancel }) {
  const [form, setForm] = useState({
    vendor_id: '',
    cut_id: '',
    price: '',
    price_unit: 'per_lb',
    verified_date: today(),
    sale_end_date: '',
    notes: '',
    active: true,
    ...initial,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.vendor_id || !form.cut_id || !form.price) {
      setError('Vendor, cut, and price are required.')
      return
    }
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...form,
        price: parseFloat(form.price),
        sale_end_date: form.sale_end_date || null,
        notes: form.notes || null,
      }
      await onSave(payload)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Save failed.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Vendor *</label>
          <select value={form.vendor_id} onChange={set('vendor_id')} required
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange">
            <option value="">Select vendor…</option>
            {vendors.filter(v => v.active).map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Cut *</label>
          <select value={form.cut_id} onChange={set('cut_id')} required
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange">
            <option value="">Select cut…</option>
            {cuts.filter(c => c.active).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Price *</label>
          <input type="number" step="0.01" min="0" value={form.price} onChange={set('price')} required
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange"
            placeholder="e.g. 4.99" />
        </div>
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Unit *</label>
          <select value={form.price_unit} onChange={set('price_unit')}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange">
            <option value="per_lb">Per lb</option>
            <option value="per_unit">Per unit</option>
            <option value="per_pack">Per pack</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Verified Date *</label>
          <input type="date" value={form.verified_date} onChange={set('verified_date')} required
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange" />
        </div>
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Sale End Date</label>
          <input type="date" value={form.sale_end_date} onChange={set('sale_end_date')}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-charcoal mb-1">Notes</label>
        <textarea value={form.notes} onChange={set('notes')} rows={2}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange resize-none"
          placeholder="Optional admin notes…" />
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div className="flex gap-3 pt-1">
        <button type="submit" disabled={saving}
          className="flex-1 min-tap bg-burnt-orange hover:bg-burnt-orange/90 disabled:opacity-50 text-cream font-display uppercase tracking-wide rounded-lg py-2.5 text-sm">
          {saving ? 'Saving…' : 'Save Deal'}
        </button>
        <button type="button" onClick={onCancel}
          className="min-tap px-4 border border-gray-200 rounded-lg text-ash hover:text-charcoal text-sm">
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function DealsPage() {
  const [deals, setDeals] = useState([])
  const [vendors, setVendors] = useState([])
  const [cuts, setCuts] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null) // null | 'add' | deal (for edit)
  const [sortBy, setSortBy] = useState('verified_date')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [d, v, c] = await Promise.all([adminGetDeals({ sort_by: sortBy }), adminGetVendors(), adminGetCuts()])
      setDeals(d)
      setVendors(v)
      setCuts(c)
    } catch {}
    setLoading(false)
  }, [sortBy])

  useEffect(() => { load() }, [load])

  const handleCreate = async (payload) => {
    await adminCreateDeal(payload)
    setModal(null)
    load()
  }

  const handleUpdate = async (payload) => {
    await adminUpdateDeal(modal.id, payload)
    setModal(null)
    load()
  }

  const handleExpire = async (deal) => {
    if (!confirm(`Expire "${deal.cut_name}" at ${deal.vendor_name}?`)) return
    await adminExpireDeal(deal.id)
    load()
  }

  const handleDelete = async (deal) => {
    if (!confirm(`Permanently delete "${deal.cut_name}" at ${deal.vendor_name}? This cannot be undone.`)) return
    await adminDeleteDeal(deal.id)
    load()
  }

  const formatDate = (str) => str ? str.replace(/-/g, '/').slice(5) + '/' + str.slice(0, 4) : '—'

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h1 className="font-display text-2xl text-charcoal uppercase">Deals</h1>
        <button
          onClick={() => setModal('add')}
          className="min-tap bg-burnt-orange text-cream font-display uppercase text-sm tracking-wide px-4 py-2 rounded-lg hover:bg-burnt-orange/90"
        >
          + Add Deal
        </button>
      </div>

      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-ash">Sort:</span>
        {[['verified_date', 'Date'], ['store', 'Store'], ['cut', 'Cut']].map(([val, lbl]) => (
          <button key={val} onClick={() => setSortBy(val)}
            className={`text-sm min-tap px-3 py-1 rounded-full border transition-colors ${
              sortBy === val ? 'bg-burnt-orange text-cream border-burnt-orange' : 'border-gray-200 text-ash hover:border-burnt-orange'
            }`}>
            {lbl}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-100 shadow-sm">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase tracking-wide text-ash">
              <tr>
                <th className="px-4 py-3 text-left">Cut</th>
                <th className="px-4 py-3 text-left">Store</th>
                <th className="px-4 py-3 text-left">Price</th>
                <th className="px-4 py-3 text-left">Verified</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 bg-white">
              {deals.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-8 text-ash">No deals found.</td></tr>
              ) : deals.map((deal) => (
                <tr key={deal.id} className={`hover:bg-gray-50 ${!deal.active ? 'opacity-50' : ''}`}>
                  <td className="px-4 py-3 font-medium text-charcoal">{deal.cut_name}</td>
                  <td className="px-4 py-3 text-ash">{deal.vendor_name}</td>
                  <td className="px-4 py-3 text-burnt-orange font-medium">
                    ${Number(deal.price).toFixed(2)}{UNIT_LABELS[deal.price_unit]}
                  </td>
                  <td className="px-4 py-3 text-ash">{formatDate(deal.verified_date)}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      deal.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {deal.active ? 'Active' : 'Expired'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-2 justify-end">
                      <button onClick={() => setModal(deal)}
                        className="text-xs text-blue-600 hover:underline min-tap px-1">Edit</button>
                      {deal.active && (
                        <button onClick={() => handleExpire(deal)}
                          className="text-xs text-amber-600 hover:underline min-tap px-1">Expire</button>
                      )}
                      <button onClick={() => handleDelete(deal)}
                        className="text-xs text-red-600 hover:underline min-tap px-1">Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal === 'add' && (
        <AdminModal title="Add Deal" onClose={() => setModal(null)}>
          <DealForm vendors={vendors} cuts={cuts} onSave={handleCreate} onCancel={() => setModal(null)} />
        </AdminModal>
      )}

      {modal && modal !== 'add' && (
        <AdminModal title="Edit Deal" onClose={() => setModal(null)}>
          <DealForm
            vendors={vendors}
            cuts={cuts}
            initial={modal}
            onSave={handleUpdate}
            onCancel={() => setModal(null)}
          />
        </AdminModal>
      )}
    </div>
  )
}
