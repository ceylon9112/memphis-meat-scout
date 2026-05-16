import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/admin/dashboard')
    } catch {
      setError('Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-dvh bg-charcoal flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <p className="text-5xl mb-3">🔥</p>
          <h1 className="font-display text-3xl text-cream uppercase tracking-wide">Memphis</h1>
          <h2 className="font-display text-gold text-xl uppercase tracking-widest">Meat Scout</h2>
          <p className="text-cream/50 text-sm mt-1">Admin Panel</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-smoke rounded-2xl p-6 space-y-4">
          <div>
            <label className="block text-cream/70 text-sm mb-1.5">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              className="w-full bg-charcoal border border-white/10 rounded-lg px-4 py-3 text-cream text-sm focus:outline-none focus:border-burnt-orange placeholder-cream/30"
            />
          </div>
          <div>
            <label className="block text-cream/70 text-sm mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full bg-charcoal border border-white/10 rounded-lg px-4 py-3 text-cream text-sm focus:outline-none focus:border-burnt-orange"
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full min-tap bg-burnt-orange hover:bg-burnt-orange/90 disabled:opacity-50 text-cream font-display uppercase tracking-wide rounded-lg py-3 transition-colors"
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}
