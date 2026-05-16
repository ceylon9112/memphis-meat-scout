const CATEGORIES = ['beef', 'pork', 'poultry', 'seafood', 'other']

export default function FilterBar({ category, setCategory, vendorId, setVendorId, vendors, sortBy, setSortBy }) {
  return (
    <div className="sticky top-14 z-10 bg-cream/95 backdrop-blur-sm border-b border-charcoal/10 px-4 py-3 space-y-2">
      {/* Category pills */}
      <div className="flex gap-2 overflow-x-auto scrollbar-none pb-0.5">
        <button
          onClick={() => setCategory('')}
          className={`shrink-0 min-tap px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
            !category ? 'bg-burnt-orange text-cream' : 'bg-white border border-charcoal/20 text-ash hover:border-burnt-orange'
          }`}
        >
          All
        </button>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(category === cat ? '' : cat)}
            className={`shrink-0 min-tap px-4 py-1.5 rounded-full text-sm font-medium capitalize transition-colors ${
              category === cat
                ? 'bg-burnt-orange text-cream'
                : 'bg-white border border-charcoal/20 text-ash hover:border-burnt-orange'
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
          className="flex-1 min-tap bg-white border border-charcoal/20 rounded-lg px-3 text-sm text-charcoal focus:outline-none focus:border-burnt-orange"
        >
          <option value="">All Stores</option>
          {vendors.map((v) => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="min-tap bg-white border border-charcoal/20 rounded-lg px-3 text-sm text-charcoal focus:outline-none focus:border-burnt-orange"
        >
          <option value="recent">Most Recent</option>
          <option value="price_asc">Price: Low → High</option>
          <option value="discount_desc">Best Discount</option>
        </select>
      </div>
    </div>
  )
}
