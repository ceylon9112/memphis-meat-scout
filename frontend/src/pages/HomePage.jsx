import { useState, useEffect } from 'react'
import { getDeals, getVendors } from '../api/client'
import WeatherWidget from '../components/WeatherWidget'
import FilterBar from '../components/FilterBar'
import DealCard from '../components/DealCard'
import EmptyState from '../components/EmptyState'

export default function HomePage() {
  const [deals, setDeals] = useState([])
  const [vendors, setVendors] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('')
  const [vendorId, setVendorId] = useState('')
  const [sortBy, setSortBy] = useState('recent')

  useEffect(() => {
    getVendors().then(setVendors).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = { sort: sortBy }
    if (vendorId) params.vendor_id = vendorId
    getDeals(params)
      .then((data) => {
        if (category) {
          setDeals(data.filter((d) => d.category === category))
        } else {
          setDeals(data)
        }
      })
      .catch(() => setDeals([]))
      .finally(() => setLoading(false))
  }, [category, vendorId, sortBy])

  return (
    <>
      <WeatherWidget />

      <FilterBar
        category={category}
        setCategory={setCategory}
        vendorId={vendorId}
        setVendorId={setVendorId}
        vendors={vendors}
        sortBy={sortBy}
        setSortBy={setSortBy}
      />

      <div className="px-4 pt-4 space-y-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl h-28 animate-pulse border border-cream/80" />
          ))
        ) : deals.length === 0 ? (
          <EmptyState message="No current deals for this selection. Check back soon." />
        ) : (
          deals.map((deal) => <DealCard key={deal.id} deal={deal} />)
        )}
      </div>
    </>
  )
}
