export default function EmptyState({ message }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <span className="text-5xl mb-4">🥩</span>
      <p className="text-ash text-base max-w-xs leading-relaxed">
        {message || 'No current deals for this selection. Check back soon.'}
      </p>
    </div>
  )
}
