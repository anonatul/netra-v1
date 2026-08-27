import { useState } from 'react'
import { api } from '../api'

const SOURCES = ['SMS', 'ERSS', 'FIELD', 'MANUAL'] as const

export default function LiveReportPanel({ onRefresh }: { onRefresh: () => void }) {
  const [text, setText] = useState('')
  const [source, setSource] = useState<(typeof SOURCES)[number]>('MANUAL')
  const [busy, setBusy] = useState(false)
  const [log, setLog] = useState<string[]>([])

  const push = (msg: string) => setLog((l) => [msg, ...l].slice(0, 10))

  const submit = async () => {
    if (!text.trim() || busy) return
    setBusy(true)
    try {
      const res = await api.submitEvent(text.trim(), source)
      push(`✔ ${source} → ${res.incident_id ?? 'no incident'}`)
      setText('')
      onRefresh()
    } catch (e) {
      push(`✘ ${(e as Error).message}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="border-t border-slate-800 p-2">
      <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-3">
        <div className="text-[11px] font-semibold tracking-widest text-slate-400 uppercase">
          Live report ingest
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit()
            }
          }}
          rows={2}
          placeholder="Type a distress report… e.g. building collapse near station, 2 trapped"
          className="mt-2 w-full resize-none rounded border border-slate-700 bg-slate-900 px-2.5 py-2 text-xs text-slate-200 outline-none placeholder:text-slate-600 focus:border-cyan-600"
        />
        <div className="mt-1.5 flex items-center gap-1.5">
          <select
            value={source}
            onChange={(e) => setSource(e.target.value as (typeof SOURCES)[number])}
            className="rounded border border-slate-700 bg-slate-900 px-1.5 py-1 text-[11px] text-slate-300 outline-none"
          >
            {SOURCES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <button
            disabled={busy || !text.trim()}
            onClick={submit}
            className="flex-1 rounded bg-cyan-700 px-2 py-1 text-xs font-semibold text-white hover:bg-cyan-600 disabled:opacity-40"
          >
            Submit report
          </button>
        </div>
        {log.length > 0 && (
          <div className="mt-2 space-y-0.5">
            {log.map((line, i) => (
              <div key={i} className="font-mono text-[10px] text-slate-500">
                {line}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}