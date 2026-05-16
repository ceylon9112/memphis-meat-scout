import { useState, useEffect } from 'react'
import { getDeals, getVendors } from '../api/client'
import { useZipPreference } from '../hooks/useZipPreference'
import WeatherWidget from '../components/WeatherWidget'
import ZipBar from '../components/ZipBar'
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
  const [zip, setZip] = useZipPreference()

  useEffect(() => {
    const params = zip ? { zip } : {}
    getVendors(params).then(setVendors).catch(() => {})
  }, [zip])

  useEffect(() => {
    setLoading(true)
    const params = { sort: sortBy }
    if (vendorId) params.vendor_id = vendorId
    if (zip && !vendorId) params.zip = zip
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
  }, [category, vendorId, sortBy, zip])

  const handleZipChange = (newZip) => {
    setZip(newZip)
    setVendorId('')  // reset store filter when zip changes
  }

  return (
    <>
      <WeatherWidget />

      <ZipBar zip={zip} onZip={handleZipChange} />

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
            <div key={i} className="glass rounded-2xl h-28 animate-pulse bg-white/50" />
          ))
        ) : deals.length === 0 ? (
          <EmptyState message={
            zip
              ? `No current deals found within 50 miles of ${zip}. Try a different zip or clear the location filter.`
              : 'No current deals for this selection. Check back soon.'
          } />
        ) : (
          deals.map((deal) => <DealCard key={deal.id} deal={deal} />)
        )}
      </div>
    </>
  )
}
