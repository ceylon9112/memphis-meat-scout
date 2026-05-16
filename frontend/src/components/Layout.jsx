import { Outlet, NavLink } from 'react-router-dom'

const navLinks = [
  { to: '/', label: 'Deals' },
  { to: '/cuts', label: 'Cuts' },
  { to: '/stores', label: 'Stores' },
]

export default function Layout() {
  return (
    <div className="relative flex flex-col min-h-dvh">
      <div className="relative z-10 flex flex-col min-h-dvh">

        {/* Light frosted glass header */}
        <header className="glass-light-surface sticky top-0 z-20">
          <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">

            <NavLink to="/" className="flex items-center gap-2.5">
              <span className="text-2xl">🔥</span>
              <span className="font-display leading-none uppercase tracking-wide">
                <span className="text-espresso text-lg">Memphis</span><br />
                <span className="text-ember text-sm font-bold">Meat Scout</span>
              </span>
            </NavLink>

            <nav className="flex gap-1">
              {navLinks.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `min-tap px-4 py-1.5 rounded-full text-sm font-semibold transition-all duration-200 flex items-center ${
                      isActive
                        ? 'pill-active'
                        : 'glass-pill'
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
        <main className="flex-1 max-w-2xl mx-auto w-full pb-8">
          <Outlet />
        </main>

        <footer className="glass-light-surface border-t border-espresso/[0.07] text-center py-3 text-xs text-bark/70">
          Memphis Meat Scout · Deals verified by our team
        </footer>
      </div>
    </div>
  )
}
