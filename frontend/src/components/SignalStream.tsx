import { useEffect, useRef, useState } from 'react'
import { api, type SignalEntry } from '../api'

const WIRE: { cat: string; text: string }[] = [
  { cat: 'FLOOD', text: 'Flash floods engulf Mumbai suburbs, rescue boats deployed' },
  { cat: 'CYCLONE', text: 'Cyclone nears Gujarat coast, mass evacuation ordered' },
  { cat: 'COLLAPSE', text: 'Multi-storey building collapse in Old Delhi, trapped being rescued' },
  { cat: 'LANDSLIDE', text: 'Landslide blocks highway NH-58, 200 travellers stranded' },
  { cat: 'EQ', text: 'Earthquake M6.1 jolts Sikkim, relief teams rushed' },
  { cat: 'FIRE', text: 'Gas leak at chemical plant sparks blaze, area cordoned off' },
  { cat: 'GRID', text: 'Storm knocks out city power grid, urban flooding reported' },
  { cat: 'BOAT', text: 'Passenger boat capsizes in the Ganga, rescue search on' },
  { cat: 'RAIL', text: 'Train derailment near Kanpur, rescue trains rushed' },
  { cat: 'HEAT', text: 'Heatwave alert, water distress calls surge in tribal hamlets' },
  { cat: 'HEALTH', text: 'Emergency ward overflow, helpline volumes spike' },
  { cat: 'CIVIL', text: 'Flash protest over relief delays, police deploy rapid units' },
]

const CAT_COLOR: Record<string, string> = {
  FLOOD: 'text-cyan-300',
  CYCLONE: 'text-blue-300',
  EQ: 'text-rose-300',
  FIRE: 'text-orange-300',
  LANDSLIDE: 'text-amber-300',
  RAIL: 'text-violet-300',
  HEALTH: 'text-emerald-300',
  COLLAPSE: 'text-rose-300',
  GRID: 'text-yellow-300',
  BOAT: 'text-sky-300',
  HEAT: 'text-orange-300',
  CIVIL: 'text-pink-300',
  SMS: 'text-slate-400',
  ERSS: 'text-violet-300',
  WHATSAPP: 'text-emerald-300',
  ELS: 'text-amber-300',
}

type Seg = { cat: string; text: string }

export default function SignalStream() {
  const [live, setLive] = useState<SignalEntry[]>([])
  const seenRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    let alive = true
    const poll = async () => {
      try {
        const rows = await api.recentEvents(40)
        if (!alive) return
        const fresh = rows.filter((r) => !seenRef.current.has(r.event_id))
        fresh.forEach((r) => seenRef.current.add(r.event_id))
        if (fresh.length > 0) setLive((prev) => [...fresh, ...prev].slice(0, 24))
      } catch {
        /* backend may be down; keep last state */
      }
    }
    poll()
    const t = setInterval(poll, 2500)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [])

  const segs: Seg[] = [
    ...WIRE,
    ...live.map((s) => ({ cat: s.source_type ?? 'SMS', text: s.text ?? '' })),
  ]

  const copy = (key: string) => (
    <div key={key} className="flex items-center whitespace-nowrap">
      {segs.map((s, i) => (
        <span key={`${key}-${i}`} className="flex items-center">
          {i > 0 && <span className="mx-4 text-slate-700">▪</span>}
          <span className={`font-mono text-[10px] font-semibold ${CAT_COLOR[s.cat] ?? 'text-slate-400'}`}>
            [{s.cat}]
          </span>
          <span className="ml-2 text-[11px] text-slate-300">{s.text}</span>
        </span>
      ))}
    </div>
  )

  return (
    <div className="flex h-11 items-stretch border-t border-slate-800 bg-[#080d1a]">
      <div className="z-10 flex shrink-0 items-center gap-1.5 border-r border-amber-800/40 bg-amber-950/30 px-3">
        <span className="relative flex h-1.5 w-1.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-amber-400" />
        </span>
        <span className="font-mono text-[10px] font-semibold tracking-widest text-amber-300">NEWS WIRE</span>
      </div>
      <div className="ticker-hover flex-1 overflow-hidden">
        <div className="ticker-ltr flex h-full min-w-max items-center will-change-transform">
          {copy('a')}
          {copy('b')}
        </div>
      </div>
    </div>
  )
}