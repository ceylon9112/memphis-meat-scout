import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const adminNav = [
  { to: '/admin/dashboard', label: 'Dashboard' },
  { to: '/admin/staging', label: 'Staging' },
  { to: '/admin/deals', label: 'Deals' },
  { to: '/admin/vendors', label: 'Vendors' },
  { to: '/admin/cuts', label: 'Cuts' },
]

export default function AdminLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/admin/login')
  }

  return (
    <div className="relative min-h-dvh">
      <div className="relative z-10 min-h-dvh">
        <header className="glass-dark sticky top-0 z-20">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-display text-burnt-orange text-lg uppercase tracking-wide drop-shadow-[0_0_8px_rgba(200,71,26,0.6)]">
                🔥 MMS Admin
              </span>
              <nav className="hidden sm:flex gap-1">
                {adminNav.map(({ to, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }) =>
                      `px-3 py-1 rounded text-sm min-tap flex items-center transition-all duration-200 ${
                        isActive
                          ? 'bg-burnt-orange/85 text-cream shadow-[0_0_10px_rgba(200,71,26,0.4)]'
                          : 'text-cream/75 hover:text-cream glass-pill'
                      }`
                    }
                  >
                    {label}
                  </NavLink>
                ))}
              </nav>
            </div>
            <button
              onClick={handleLogout}
              className="text-cream/50 hover:text-cream text-sm px-3 py-1 min-tap glass-pill rounded-full transition-all"
            >
              Sign out
            </button>
          </div>
          {/* Mobile nav */}
          <div className="sm:hidden flex border-t border-white/[0.07]">
            {adminNav.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex-1 text-center py-2 text-xs min-tap flex items-center justify-center transition-all ${
                    isActive ? 'text-gold border-b-2 border-gold drop-shadow-[0_0_4px_rgba(232,197,71,0.5)]' : 'text-cream/65'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
