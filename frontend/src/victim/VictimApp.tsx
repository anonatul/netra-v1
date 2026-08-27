import { useEffect, useRef, useState } from 'react'
import QRCode from 'qrcode'
import { BASE } from '../api'

const HOTSPOTS = [
  { id: 'Z1', lat: 19.076, lon: 72.8777 },
  { id: 'Z2', lat: 19.088, lon: 72.865 },
  { id: 'Z3', lat: 19.065, lon: 72.89 },
  { id: 'Z4', lat: 19.098, lon: 72.87 },
  { id: 'Z5', lat: 19.052, lon: 72.862 },
  { id: 'Z6', lat: 19.07, lon: 72.905 },
]

const PRESETS = [
  { label: 'Trapped on roof', lang: 'EN', text: 'Water rising fast, we are trapped on rooftop, grandmother with us cannot move, please send help' },
  { label: 'Medical emergency', lang: 'HI', text: 'Dadi ko dil ka daura pada, bachcha bemar hai, paani bahut badh gaya, phans gaye hain, jaldi bhejo' },
  { label: 'Bleeding, unconscious', lang: 'HI', text: 'KHOON BAH RAHA HAI, dadi BEHOSH HO GAYI HAI, PAANI CHHAT TAK, 4 log phanse hain, JALDI MADAD' },
  { label: 'Water in house', lang: 'HI', text: 'paani ghar me ghus raha hai, dadi aur bachcha, kuch samajh nahi aa raha, assistance chahiye' },
  { label: 'Need boats NOW', lang: 'EN', text: 'Heavy bleeding, people unconscious, water up to roof, need rescue boats NOW' },
  { label: 'Just informing', lang: 'HI', text: 'paani ghar me ghus raha hai, hum log ghar me hi hain, bas jankari de rahe hain' },
]

const SOURCES = ['SMS', 'ERSS', 'SMS', 'WHATSAPP', 'ERSS']

const isProjector = typeof window !== 'undefined' && window.innerWidth > 768

export default function VictimApp() {
  const [token, setToken] = useState<string | null>(null)
  const [qr, setQr] = useState<string | null>(null)
  const [selected, setSelected] = useState<(typeof PRESETS)[number] | null>(PRESETS[0])
  const [custom, setCustom] = useState('')
  const [sending, setSending] = useState(false)
  const [sentAt, setSentAt] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [gps, setGps] = useState<{ lat: number; lon: number; acc: number } | null>(null)
  const [gpsDenied, setGpsDenied] = useState(false)
  const deviceRef = useRef(`victim-${Math.random().toString(36).slice(2, 8)}`)
  const [hotspot] = useState(() => HOTSPOTS[Math.floor(Math.random() * HOTSPOTS.length)])

  useEffect(() => {
    fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'citizen-sim', password: 'citizen-sim123' }),
    })
      .then((r) => r.json())
      .then((d) => d.access_token && setToken(d.access_token))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (isProjector) QRCode.toDataURL(window.location.href, { width: 200, margin: 1 }).then(setQr).catch(() => {})
  }, [])

  const requestGps = () => {
    if (!('geolocation' in navigator)) return setGpsDenied(true)
    navigator.geolocation.getCurrentPosition(
      (p) => setGps({ lat: p.coords.latitude, lon: p.coords.longitude, acc: Math.round(p.coords.accuracy) }),
      () => setGpsDenied(true),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
    )
  }

  useEffect(() => {
    requestGps()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const text = selected ? selected.text : custom
  const canSend = !!token && !sending && text.trim().length > 0
  const location = gps ?? hotspot

  const send = async () => {
    if (!canSend) return
    setSending(true)
    setError(null)
    const acc = gps ? Math.max(20, gps.acc) : Math.round(120 + Math.random() * 130)
    try {
      const res = await fetch(`${BASE}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          source_type: SOURCES[Math.floor(Math.random() * SOURCES.length)],
          source_timestamp: new Date().toISOString(),
          text,
          source_identifier: deviceRef.current,
          location: { lat: location.lat, lon: location.lon, accuracy_m: acc },
          idempotency_key: `citizen-${deviceRef.current}-${Date.now()}`,
        }),
      })
      const body = await res.json()
      if (!res.ok) throw new Error(body.detail?.message || `${res.status}`)
      setSentAt(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="victim-bg relative flex min-h-screen flex-col items-center px-6 py-8 text-slate-200">
      <div className="w-full max-w-sm">
        <div className="flex items-baseline justify-between">
          <span className="font-display text-2xl font-bold tracking-[0.3em] text-cyan-400">NETRA</span>
          <span className="font-mono text-[9px] tracking-[0.25em] text-amber-400/90 uppercase">
            Citizen · Terminal
          </span>
        </div>
        <div className="netra-hazard mt-3" />

        {qr && (
          <div className="mt-6 flex flex-col items-center">
            <img src={qr} alt="scan" className="h-44 w-44 bg-white p-1.5" />
            <span className="mt-2 font-mono text-[11px] text-slate-400">{window.location.href}</span>
            <span className="mt-1 font-mono text-[9px] tracking-[0.25em] text-slate-600 uppercase">
              scan with your phone
            </span>
          </div>
        )}

        <div className="mt-6">
          <button
            onClick={send}
            disabled={!canSend}
            className={`relative w-full border-2 py-6 font-display text-xl font-bold tracking-[0.3em] transition active:scale-[0.98] ${
              sentAt
                ? 'border-emerald-500 bg-emerald-600/90 text-white'
                : 'border-red-400 bg-gradient-to-b from-red-500 to-red-800 text-white hover:brightness-110'
            } ${!canSend ? 'opacity-40' : ''}`}
          >
            <span className="absolute left-2 top-0 h-2 w-2 border-l-2 border-t-2 border-white/60" />
            <span className="absolute right-2 top-0 h-2 w-2 border-r-2 border-t-2 border-white/60" />
            <span className="absolute bottom-0 left-2 h-2 w-2 border-b-2 border-l-2 border-white/60" />
            <span className="absolute bottom-0 right-2 h-2 w-2 border-b-2 border-r-2 border-white/60" />
            {sending ? 'SENDING…' : sentAt ? `SENT ${sentAt}` : 'SEND SOS'}
          </button>
        </div>

        <div className="mt-3 flex items-center justify-between font-mono text-[10px]">
          {gps ? (
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="h-1.5 w-1.5 bg-emerald-400" /> GPS ±{gps.acc}m
            </span>
          ) : gpsDenied ? (
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="h-1.5 w-1.5 bg-amber-400" /> GPS off · simulated
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-slate-500">
              <span className="h-1.5 w-1.5 animate-pulse bg-cyan-400" /> locating…
            </span>
          )}
          <button onClick={requestGps} className="text-slate-500 underline-offset-2 hover:underline">
            {gps ? 're-locate' : 'allow GPS'}
          </button>
        </div>

        <div className="mt-6">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] tracking-[0.25em] text-slate-500 uppercase">Message</span>
            <span className="h-px flex-1 bg-slate-800" />
          </div>
          <div className="mt-2 grid grid-cols-2 gap-1.5">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => {
                  setSelected(p)
                  setCustom('')
                }}
                className={`border px-2.5 py-2 text-left text-[11px] transition ${
                  selected === p
                    ? 'border-cyan-500 bg-cyan-950/40 text-cyan-200'
                    : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-600'
                }`}
              >
                <span className="block font-medium">{p.label}</span>
                <span className="mt-0.5 block font-mono text-[9px] text-slate-600">{p.lang}</span>
              </button>
            ))}
          </div>
          <textarea
            value={custom}
            onChange={(e) => {
              setCustom(e.target.value)
              if (e.target.value.trim()) setSelected(null)
            }}
            placeholder="…or write your own (any language)"
            className="mt-2 h-20 w-full resize-none border border-slate-800 bg-slate-950/60 px-3 py-2 font-mono text-xs text-slate-200 outline-none placeholder:text-slate-700 focus:border-cyan-600"
          />
        </div>

        {error && (
          <div className="mt-3 border border-red-900 bg-red-950/40 px-3 py-2 text-center font-mono text-[11px] text-red-400">
            {error}
          </div>
        )}
      </div>
      <div className="netra-scanlines pointer-events-none fixed inset-0" />
    </div>
  )
}