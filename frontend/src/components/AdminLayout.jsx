import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const adminNav = [
  { to: '/admin/dashboard', label: 'Dashboard' },
  { to: '/admin/staging',   label: 'Staging' },
  { to: '/admin/deals',     label: 'Deals' },
  { to: '/admin/vendors',   label: 'Vendors' },
  { to: '/admin/cuts',      label: 'Cuts' },
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

        <header className="glass-light-surface sticky top-0 z-20">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-display text-ember text-lg uppercase tracking-wide flex items-center gap-1.5">
                <span>🔥</span> MMS Admin
              </span>
              <nav className="hidden sm:flex gap-1">
                {adminNav.map(({ to, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }) =>
                      `px-3 py-1 rounded-full text-sm font-semibold min-tap flex items-center transition-all duration-200 ${
                        isActive ? 'pill-active' : 'glass-pill'
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
              className="glass-pill text-sm px-4 py-1.5 rounded-full font-medium min-tap transition-all"
            >
              Sign out
            </button>
          </div>

          {/* Mobile nav */}
          <div className="sm:hidden flex border-t border-espresso/[0.07]">
            {adminNav.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex-1 text-center py-2 text-xs min-tap flex items-center justify-center font-semibold transition-all ${
                    isActive
                      ? 'text-ember border-b-2 border-ember'
                      : 'text-bark'
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
