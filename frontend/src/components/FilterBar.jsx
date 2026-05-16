const CATEGORIES = ['beef', 'pork', 'poultry', 'seafood', 'other']

export default function FilterBar({ category, setCategory, vendorId, setVendorId, vendors, sortBy, setSortBy }) {
  return (
    <div className="sticky top-14 z-10 glass-dark border-b border-white/[0.07] px-4 py-3 space-y-2">
      {/* Category pills */}
      <div className="flex gap-2 overflow-x-auto scrollbar-none pb-0.5">
        <button
          onClick={() => setCategory('')}
          className={`shrink-0 min-tap px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
            !category
              ? 'bg-burnt-orange/85 text-cream shadow-[0_0_12px_rgba(200,71,26,0.45)]'
              : 'glass-pill text-cream/60 hover:text-cream'
          }`}
        >
          All
        </button>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(category === cat ? '' : cat)}
            className={`shrink-0 min-tap px-4 py-1.5 rounded-full text-sm font-medium capitalize transition-all duration-200 ${
              category === cat
                ? 'bg-burnt-orange/85 text-cream shadow-[0_0_12px_rgba(200,71,26,0.45)]'
                : 'glass-pill text-cream/60 hover:text-cream'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Store + Sort row */}
      <div className="flex gap-2">
        <select
          value={vendorId}
          onChange={(e) => setVendorId(e.target.value)}
          className="flex-1 min-tap glass-input rounded-lg px-3 text-sm focus:outline-none"
        >
          <option value="">All Stores</option>
          {vendors.map((v) => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="min-tap glass-input rounded-lg px-3 text-sm focus:outline-none"
        >
          <option value="recent">Most Recent</option>
          <option value="price_asc">Price: Low → High</option>
          <option value="discount_desc">Best Discount</option>
        </select>
      </div>
    </div>
  )
}
