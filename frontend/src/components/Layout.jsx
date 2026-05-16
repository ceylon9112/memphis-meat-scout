import { Outlet, NavLink } from 'react-router-dom'

const navLinks = [
  { to: '/', label: 'Deals', icon: '🥩' },
  { to: '/cuts', label: 'Cuts', icon: '🔪' },
  { to: '/stores', label: 'Stores', icon: '📍' },
]

export default function Layout() {
  return (
    <div className="relative flex flex-col min-h-dvh">
      {/* z-index layer above body pseudo-elements */}
      <div className="relative z-10 flex flex-col min-h-dvh">

        {/* Glass header */}
        <header className="glass-dark sticky top-0 z-20">
          <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
            <NavLink to="/" className="flex items-center gap-2.5">
              <span className="text-burnt-orange text-2xl drop-shadow-[0_0_8px_rgba(200,71,26,0.7)]">🔥</span>
              <span className="font-display text-lg tracking-wide uppercase leading-none">
                Memphis<br />
                <span className="text-gold text-sm drop-shadow-[0_0_6px_rgba(232,197,71,0.5)]">Meat Scout</span>
              </span>
            </NavLink>
            <nav className="flex gap-1">
              {navLinks.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `min-tap px-3 py-1 rounded-full text-sm font-medium transition-all duration-200 flex items-center ${
                      isActive
                        ? 'bg-burnt-orange/85 text-cream shadow-[0_0_12px_rgba(200,71,26,0.45)]'
                        : 'text-cream/75 hover:text-cream glass-pill'
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

        <footer className="glass-dark border-t border-white/[0.10] text-center py-3 text-xs text-cream/50">
          Memphis Meat Scout · Deals verified by our team
        </footer>
      </div>
    </div>
  )
}
