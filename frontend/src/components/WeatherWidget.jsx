import { useEffect, useState } from 'react'
import { getWeather } from '../api/client'

function WindIcon() {
  return (
    <svg className="w-3 h-3 inline mr-0.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
    </svg>
  )
}

function DayCard({ label, high, precip_pct, wind_mph }) {
  return (
    <div className="flex-1 text-center rounded-xl py-3 px-2" style={{
      background: 'rgba(255,255,255,0.55)',
      border: '1px solid rgba(255,255,255,0.85)',
    }}>
      <p className="text-sky font-display text-xs uppercase tracking-wider mb-2 font-bold">{label}</p>
      <p className="text-espresso text-2xl font-display leading-none">{high}°</p>
      <p className="text-bark text-xs mt-2">🌧 {precip_pct}%</p>
      <p className="text-bark text-xs mt-0.5">
        <WindIcon />{wind_mph} mph
      </p>
    </div>
  )
}

export default function WeatherWidget() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getWeather()
      .then((d) => {
        if (d?.days) setData(d.days)
        else setError(true)
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  return (
    /*
      Sky-to-sage gradient panel — like looking up through the trees.
      Frosted glass over the outdoor background.
    */
    <div
      className="rounded-2xl p-4 mx-4 mt-4"
      style={{
        background: 'linear-gradient(135deg, rgba(91,143,168,0.18) 0%, rgba(74,124,89,0.12) 60%, rgba(255,253,250,0.55) 100%)',
        backdropFilter: 'blur(20px) saturate(160%)',
        WebkitBackdropFilter: 'blur(20px) saturate(160%)',
        border: '1px solid rgba(255,255,255,0.75)',
        boxShadow: '0 4px 24px rgba(44,31,16,0.10), inset 0 1px 0 rgba(255,255,255,0.90)',
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-display text-espresso text-sm uppercase tracking-widest flex items-center gap-1.5">
          <span>🔥</span>
          <span>Cookout Forecast</span>
        </h2>
        <span className="text-bark text-xs font-medium">Memphis, TN</span>
      </div>

      {loading && (
        <div className="flex gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex-1 rounded-xl h-24 animate-pulse bg-white/50" />
          ))}
        </div>
      )}

      {error && !loading && (
        <p className="text-bark text-sm text-center py-3">
          Forecast temporarily unavailable.
        </p>
      )}

      {data && !loading && (
        <div className="flex gap-2">
          {data.map((day) => (
            <DayCard key={day.label} {...day} />
          ))}
        </div>
      )}
    </div>
  )
}
