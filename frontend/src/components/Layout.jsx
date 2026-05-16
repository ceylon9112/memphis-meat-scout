import { Outlet, NavLink } from 'react-router-dom'

const navLinks = [
  { to: '/', label: 'Deals', icon: '🥩' },
  { to: '/cuts', label: 'Cuts', icon: '🔪' },
  { to: '/stores', label: 'Stores', icon: '📍' },
]

export default function Layout() {
  return (
    <div className="flex flex-col min-h-dvh bg-cream">
      {/* Top header */}
      <header className="bg-charcoal text-cream sticky top-0 z-20 shadow-md">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="text-burnt-orange text-2xl">🔥</span>
            <span className="font-display text-lg tracking-wide uppercase leading-none">
              Memphis<br />
              <span className="text-gold text-sm">Meat Scout</span>
            </span>
          </NavLink>
          <nav className="flex gap-1">
            {navLinks.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `min-tap px-3 py-1 rounded-full text-sm font-medium transition-colors flex items-center ${
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
      </header>

      {/* Page content */}
      <main className="flex-1 max-w-2xl mx-auto w-full pb-6">
        <Outlet />
      </main>

      <footer className="bg-charcoal/5 border-t border-charcoal/10 text-center py-3 text-xs text-ash">
        Memphis Meat Scout · Deals verified by our team
      </footer>
    </div>
  )
}
