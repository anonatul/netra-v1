const AXES = [
  { key: 'severity', label: 'SEVERITY' },
  { key: 'vulnerability', label: 'VULNERABLE' },
  { key: 'victims', label: 'VICTIMS' },
  { key: 'freshness', label: 'FRESHNESS' },
  { key: 'location_confidence', label: 'LOCATION' },
  { key: 'access', label: 'ACCESS' },
]

export default function PriorityRadar({
  components,
  corroborationBoost,
  score,
}: {
  components: Record<string, number>
  corroborationBoost: number
  score: number
}) {
  const cx = 100
  const cy = 100
  const r = 78

  const point = (i: number, value: number) => {
    const angle = (Math.PI / 3) * i - Math.PI / 2
    const rr = r * Math.min(1, Math.max(0, value))
    return [cx + rr * Math.cos(angle), cy + rr * Math.sin(angle)]
  }

  const poly = (scale: number) =>
    AXES.map((_, i) => point(i, scale).join(',')).join(' ')

  const dataPoints = AXES.map((a, i) => point(i, components[a.key] ?? 0).join(',')).join(' ')
  const ringPts = [0.33, 0.66, 1].map((s) => poly(s)).join(' ')

  return (
    <div className="relative flex items-center justify-center">
      <svg viewBox="0 0 200 200" className="h-44 w-44">
        <defs>
          <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(34,211,238,0.35)" />
            <stop offset="100%" stopColor="rgba(34,211,238,0)" />
          </radialGradient>
          <filter id="radarBlur" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" />
          </filter>
        </defs>

        <polygon points={ringPts} fill="none" stroke="#1e293b" strokeWidth="0.75" />

        {AXES.map((a, i) => {
          const [x, y] = point(i, 1)
          const lx = x + (x - cx) * 0.16
          const ly = y + (y - cy) * 0.16
          return (
            <g key={a.key}>
              <line x1={cx} y1={cy} x2={x} y2={y} stroke="#1e293b" strokeWidth="0.75" />
              <text x={lx} y={ly + 3} textAnchor="middle" fontSize="7.5" fill="#64748b" fontFamily="IBM Plex Mono, monospace">
                {a.label}
              </text>
            </g>
          )
        })}

        <polygon points={dataPoints} fill="url(#radarGlow)" stroke="#22d3ee" strokeWidth="1.5" filter="url(#radarBlur)" className="radar-fill" />
        <polygon points={dataPoints} fill="rgba(34,211,238,0.08)" stroke="#22d3ee" strokeWidth="1" />

        {AXES.map((_, i) => {
          const [x, y] = point(i, components[AXES[i].key] ?? 0)
          return <circle key={AXES[i].key} cx={x} cy={y} r="2" fill="#22d3ee" />
        })}
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-2xl font-medium text-cyan-300">{score.toFixed(2)}</span>
        {corroborationBoost > 1 && (
          <span className="mt-0.5 rounded bg-emerald-950/70 px-1.5 py-px font-mono text-[9px] text-emerald-300">
            +corrob ×{corroborationBoost.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  )
}