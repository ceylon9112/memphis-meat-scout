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
    <div className="min-h-dvh bg-gray-50">
      <header className="bg-charcoal text-cream shadow-lg">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="font-display text-burnt-orange text-lg uppercase tracking-wide">
              🔥 MMS Admin
            </span>
            <nav className="hidden sm:flex gap-1">
              {adminNav.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `px-3 py-1 rounded text-sm min-tap flex items-center transition-colors ${
                      isActive
                        ? 'bg-burnt-orange text-cream'
                        : 'text-cream/70 hover:text-cream hover:bg-white/10'
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
            className="text-cream/70 hover:text-cream text-sm px-3 py-1 min-tap"
          >
            Sign out
          </button>
        </div>
        {/* Mobile nav */}
        <div className="sm:hidden flex border-t border-white/10">
          {adminNav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex-1 text-center py-2 text-xs min-tap flex items-center justify-center transition-colors ${
                  isActive ? 'text-gold border-b-2 border-gold' : 'text-cream/60'
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
  )
}
