import { useState, useEffect } from 'react'
import { getDashboard } from '../../api/client'

function StatCard({ label, value, color, note }) {
  return (
    <div className={`bg-white rounded-xl p-4 border-l-4 ${color} shadow-sm`}>
      <p className="text-3xl font-display text-charcoal">{value ?? '—'}</p>
      <p className="text-sm font-medium text-charcoal mt-1">{label}</p>
      {note && <p className="text-xs text-ash mt-0.5">{note}</p>}
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    getDashboard()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-2xl text-charcoal uppercase">Dashboard</h1>
        <button
          onClick={load}
          className="text-sm text-ash hover:text-burnt-orange min-tap px-3 flex items-center gap-1"
        >
          ↺ Refresh
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {(stats?.expiring_soon > 0 || stats?.stale_deals > 0) && (
            <div className="mb-5 bg-amber-50 border border-amber-200 rounded-xl p-4 flex flex-col gap-1">
              <p className="font-display text-amber-800 uppercase text-sm tracking-wide">⚠ Attention needed</p>
              {stats.expiring_soon > 0 && (
                <p className="text-sm text-amber-700">
                  {stats.expiring_soon} deal{stats.expiring_soon !== 1 ? 's' : ''} expiring in the next 2 days
                </p>
              )}
              {stats.stale_deals > 0 && (
                <p className="text-sm text-amber-700">
                  {stats.stale_deals} stale deal{stats.stale_deals !== 1 ? 's' : ''} still in the system
                </p>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard
              label="Active Deals"
              value={stats?.active_deals}
              color="border-green-500"
              note="Verified within 7 days"
            />
            <StatCard
              label="Expiring Soon"
              value={stats?.expiring_soon}
              color="border-amber-400"
              note="Verified 5–7 days ago"
            />
            <StatCard
              label="Stale Deals"
              value={stats?.stale_deals}
              color="border-red-500"
              note="Older than 7 days"
            />
            <StatCard
              label="Active Vendors"
              value={stats?.active_vendors}
              color="border-burnt-orange"
            />
          </div>
        </>
      )}
    </div>
  )
}
