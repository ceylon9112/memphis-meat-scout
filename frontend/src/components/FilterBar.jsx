const CATEGORIES = ['beef', 'pork', 'poultry', 'seafood', 'other']

export default function FilterBar({ category, setCategory, vendorId, setVendorId, vendors, sortBy, setSortBy }) {
  return (
    <div className="sticky top-14 z-10 glass-light-surface border-b border-espresso/[0.08] px-4 py-3 space-y-2">

      {/* Category pills */}
      <div className="flex gap-2 overflow-x-auto scrollbar-none pb-0.5">
        {['', ...CATEGORIES].map((cat) => {
          const label = cat === '' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)
          const isActive = category === cat
          return (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`shrink-0 min-tap px-4 py-1.5 rounded-full text-sm font-semibold capitalize transition-all duration-200 ${
                isActive ? 'pill-active' : 'glass-pill'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>

      {/* Store + Sort row */}
      <div className="flex gap-2">
        <select
          value={vendorId}
          onChange={(e) => setVendorId(e.target.value)}
          className="flex-1 min-tap glass-input rounded-lg px-3 text-sm transition-all"
        >
          <option value="">All Stores</option>
          {vendors.map((v) => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="min-tap glass-input rounded-lg px-3 text-sm transition-all"
        >
          <option value="recent">Most Recent</option>
          <option value="price_asc">Price: Low → High</option>
          <option value="discount_desc">Best Discount</option>
        </select>
      </div>
    </div>
  )
}
