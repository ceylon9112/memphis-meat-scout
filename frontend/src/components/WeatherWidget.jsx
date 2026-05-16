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
    <div className="flex-1 text-center bg-smoke/50 rounded-lg py-3 px-2">
      <p className="text-gold font-display text-xs uppercase tracking-wider mb-2">{label}</p>
      <p className="text-cream text-2xl font-display leading-none">{high}°</p>
      <p className="text-cream/70 text-xs mt-2">🌧 {precip_pct}%</p>
      <p className="text-cream/70 text-xs mt-0.5">
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
    <div className="bg-charcoal rounded-xl p-4 mx-4 mt-4 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-display text-gold text-sm uppercase tracking-widest">
          🔥 Cookout Forecast
        </h2>
        <span className="text-cream/40 text-xs">Memphis, TN</span>
      </div>

      {loading && (
        <div className="flex gap-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex-1 bg-smoke/50 rounded-lg h-24 animate-pulse" />
          ))}
        </div>
      )}

      {error && !loading && (
        <p className="text-cream/50 text-sm text-center py-3">
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
