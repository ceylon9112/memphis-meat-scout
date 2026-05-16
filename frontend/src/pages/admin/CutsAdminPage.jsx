import { useState, useEffect, useCallback } from 'react'
import { adminGetCuts, adminCreateCut, adminUpdateCut, adminDeactivateCut } from '../../api/client'
import AdminModal from '../../components/AdminModal'

const CATEGORIES = ['beef', 'pork', 'poultry', 'seafood', 'other']

function CutForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState({ name: '', category: 'beef', active: true, ...initial })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const set = (k) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [k]: val }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name) { setError('Name is required.'); return }
    setSaving(true); setError('')
    try { await onSave(form) }
    catch (err) { setError(err?.response?.data?.detail || 'Save failed.') }
    finally { setSaving(false) }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-charcoal mb-1">Name *</label>
        <input value={form.name} onChange={set('name')} required
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange"
          placeholder="e.g. Brisket (flat)" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-charcoal mb-1">Category *</label>
          <select value={form.category} onChange={set('category')}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-burnt-orange capitalize">
            {CATEGORIES.map(c => <option key={c} value={c} className="capitalize">{c}</option>)}
          </select>
        </div>
        <div className="flex items-end pb-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.active} onChange={set('active')}
              className="w-4 h-4 accent-burnt-orange" />
            <span className="text-sm font-medium text-charcoal">Active</span>
          </label>
        </div>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div className="flex gap-3 pt-1">
        <button type="submit" disabled={saving}
          className="flex-1 min-tap bg-burnt-orange hover:bg-burnt-orange/90 disabled:opacity-50 text-cream font-display uppercase tracking-wide rounded-lg py-2.5 text-sm">
          {saving ? 'Saving…' : 'Save Cut'}
        </button>
        <button type="button" onClick={onCancel}
          className="min-tap px-4 border border-gray-200 rounded-lg text-ash hover:text-charcoal text-sm">
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function CutsAdminPage() {
  const [cuts, setCuts] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    adminGetCuts().then(setCuts).catch(() => {}).finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = async (data) => { await adminCreateCut(data); setModal(null); load() }
  const handleUpdate = async (data) => { await adminUpdateCut(modal.id, data); setModal(null); load() }
  const handleDeactivate = async (c) => {
    if (!confirm(`Deactivate "${c.name}"? It will be hidden from cut search.`)) return
    await adminDeactivateCut(c.id); load()
  }

  const grouped = CATEGORIES.reduce((acc, cat) => {
    const items = cuts.filter(c => c.category === cat)
    if (items.length) acc[cat] = items
    return acc
  }, {})

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h1 className="font-display text-2xl text-charcoal uppercase">Meat Cuts</h1>
        <button onClick={() => setModal('add')}
          className="min-tap bg-burnt-orange text-cream font-display uppercase text-sm tracking-wide px-4 py-2 rounded-lg hover:bg-burnt-orange/90">
          + Add Cut
        </button>
      </div>

      {loading ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-10 bg-gray-100 rounded-lg animate-pulse" />)}</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-100 shadow-sm">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase tracking-wide text-ash">
              <tr>
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Category</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 bg-white">
              {cuts.length === 0
                ? <tr><td colSpan={4} className="text-center py-8 text-ash">No cuts yet.</td></tr>
                : cuts.map(c => (
                  <tr key={c.id} className={`hover:bg-gray-50 ${!c.active ? 'opacity-50' : ''}`}>
                    <td className="px-4 py-3 font-medium text-charcoal">{c.name}</td>
                    <td className="px-4 py-3 capitalize text-ash">{c.category}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${c.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {c.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex gap-2 justify-end">
                        <button onClick={() => setModal(c)} className="text-xs text-blue-600 hover:underline min-tap px-1">Edit</button>
                        {c.active && <button onClick={() => handleDeactivate(c)} className="text-xs text-amber-600 hover:underline min-tap px-1">Deactivate</button>}
                      </div>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      )}

      {modal === 'add' && (
        <AdminModal title="Add Cut" onClose={() => setModal(null)}>
          <CutForm onSave={handleCreate} onCancel={() => setModal(null)} />
        </AdminModal>
      )}
      {modal && modal !== 'add' && (
        <AdminModal title="Edit Cut" onClose={() => setModal(null)}>
          <CutForm initial={modal} onSave={handleUpdate} onCancel={() => setModal(null)} />
        </AdminModal>
      )}
    </div>
  )
}
