export default function FilterSidebar({ filters, onRemove }) {
  /*
  filters comes from Claude/Gemini extracted_intent:
  {
    budget_max: 7500000,
    bhk: 2,
    city: "Chennai",
    vastu: true,
    features: ["natural_light", "parking"],
    proximity: ["school"]
  }
  Filters auto-populate from what the user typed.
  User never sets these manually.
  */

  const chips = []

  if (filters?.budget_max) chips.push({
    key: 'budget_max',
    label: `Under ₹${(filters.budget_max/100000).toFixed(0)}L`,
    color: 'blue'
  })
  if (filters?.bhk) chips.push({
    key: 'bhk',
    label: `${filters.bhk} BHK`,
    color: 'blue'
  })
  if (filters?.city) chips.push({
    key: 'city',
    label: filters.city,
    color: 'cyan'
  })
  if (filters?.vastu) chips.push({
    key: 'vastu',
    label: 'Vastu Compliant',
    color: 'amber'
  })
  filters?.features?.forEach(f => chips.push({
    key: `feature_${f}`,
    label: f.replace('_', ' '),
    color: 'cyan'
  }))
  filters?.proximity?.forEach(p => chips.push({
    key: `prox_${p}`,
    label: `Near ${p}`,
    color: 'amber'
  }))

  if (!chips.length) return null

  return (
    <div className="hidden lg:block w-full">
      <div className="mb-4 hidden">
          <span className="text-xs font-semibold uppercase tracking-wider text-secondary/60">Active Filters</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {chips.map(chip => (
          <button
            key={chip.key}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                chip.color === 'blue' ? 'bg-blue-500/10 text-blue-700 hover:bg-blue-500/20' :
                chip.color === 'cyan' ? 'bg-cyan-500/10 text-cyan-700 hover:bg-cyan-500/20' :
                'bg-amber-500/10 text-amber-700 hover:bg-amber-500/20'
            }`}
            onClick={() => onRemove && onRemove(chip.key)}
          >
            {chip.label}
            <span className="ml-1 hover:text-foreground">×</span>
          </button>
        ))}
      </div>
    </div>
  )
}
