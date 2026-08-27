import { useEffect, useState } from 'react'
import { api, type EvidenceEntry, type Incident, type PriorityDetail, type Recommendation } from '../api'
import { PRIORITY_COLOR } from './NetraMap'
import PriorityRadar from './PriorityRadar'

const COMPONENT_LABELS: Record<string, string> = {
  severity: 'Severity',
  vulnerability: 'Vulnerability',
  victims: 'Victim count',
  freshness: 'Freshness',
  location: 'Location quality',
  access: 'Access risk',
}

export default function DetailPanel({
  incident,
  onClose,
  onRefresh,
  canCommand,
}: {
  incident: Incident | null
  onClose: () => void
  onRefresh: () => void
  canCommand: boolean
}) {
  const [priority, setPriority] = useState<PriorityDetail | null>(null)
  const [rec, setRec] = useState<Recommendation | null>(null)
  const [evidence, setEvidence] = useState<EvidenceEntry[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!incident) {
      setPriority(null)
      setRec(null)
      setEvidence(null)
      return
    }
    api.priority(incident.incident_id).then(setPriority).catch(() => setPriority(null))
    api.recommendation(incident.incident_id).then(setRec).catch(() => setRec(null))
    api.incidentEvidence(incident.incident_id).then(setEvidence).catch(() => setEvidence(null))
  }, [incident])

  if (!incident) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-xs text-slate-500">
        Select an incident for details, priority score, and recommendations.
      </div>
    )
  }

  const color = PRIORITY_COLOR[incident.priority] ?? PRIORITY_COLOR.UNRATED

  const act = async (type: string, values: Record<string, unknown> = {}, notes = '') => {
    setBusy(true)
    setMsg(null)
    try {
      await api.fieldUpdate(incident.incident_id, type, values, notes)
      setMsg(`${type} applied`)
      onRefresh()
    } catch (e) {
      setMsg(String((e as Error).message))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto p-3">
      <div className="flex items-center justify-between">
        <span className="font-mono text-sm text-slate-200">{incident.incident_id}</span>
        <button onClick={onClose} className="rounded px-2 text-slate-500 hover:bg-slate-800">
          ✕
        </button>
      </div>

      <div className="mt-2 flex items-center gap-2">
        <span className="rounded px-2 py-0.5 text-xs font-bold text-white" style={{ backgroundColor: color }}>
          {incident.priority}
        </span>
        <span className="text-xs text-slate-400">{incident.severity}</span>
        <span className="text-xs text-slate-500">conf {incident.confidence != null ? Math.round(incident.confidence * 100) : '?'}%</span>
        {incident.location.lat === null && (
          <span className="rounded bg-amber-950/60 px-1.5 py-0.5 font-mono text-[9px] text-amber-300">
            NO LOCATION
          </span>
        )}
      </div>

      {priority && (
        <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/80 p-3">
          <div className="flex items-baseline justify-between">
            <span className="text-[11px] font-semibold tracking-widest text-slate-400 uppercase">
              Rescue Priority Score
            </span>
            {priority.current_level && priority.current_level !== priority.level && (
              <span className="font-mono text-[10px] text-amber-400">
                {priority.current_level} → {priority.level}
              </span>
            )}
          </div>
          <div className="mt-2">
            <PriorityRadar
              components={priority.components}
              corroborationBoost={priority.corroboration_boost}
              score={priority.score}
            />
          </div>
          <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5">
            {Object.entries(priority.components).map(([k, v]) => (
              <span key={k} className="text-[10px] text-slate-400">
                {COMPONENT_LABELS[k] ?? k} {v.toFixed(2)}
              </span>
            ))}
          </div>
          <ul className="mt-2 space-y-1">
            {(priority.reasons ?? []).slice(0, 6).map((r, i) => (
              <li key={i} className="text-[11px] text-slate-300">
                • {r.note ?? r.factor}
              </li>
            ))}
          </ul>
        </div>
      )}

      {rec && (
        <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/80 p-3">
          <div className="text-[11px] font-semibold tracking-widest text-slate-400 uppercase">Recommended resources</div>
          <div className="mt-2 space-y-1.5">
            {rec.resources.map((r) => (
              <div key={r.resource} className="flex items-center justify-between text-xs">
                <span className="text-slate-200">{r.resource}</span>
                <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-slate-300">
                  ×{r.quantity} {r.priority}
                </span>
              </div>
            ))}
          </div>
          <ul className="mt-2 space-y-1">
            {(rec.reasons ?? []).map((reason, i) => (
              <li key={i} className="text-[11px] text-slate-400">
                • {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/80 p-3">
        <div className="text-[11px] font-semibold tracking-widest text-slate-400 uppercase">Field actions</div>
        <div className="mt-2 grid grid-cols-2 gap-1.5">
          <button
            disabled={busy}
            onClick={() => act('VERIFY', {}, 'verified by field unit')}
            className="rounded border border-cyan-700 bg-cyan-950/50 px-2 py-1.5 text-xs text-cyan-300 hover:bg-cyan-900/50 disabled:opacity-50"
          >
            Verify
          </button>
          <button
            disabled={busy}
            onClick={() => act('VICTIM_COUNT', { count: 5 })}
            className="rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-xs text-slate-200 hover:bg-slate-700 disabled:opacity-50"
          >
            Victim count 5
          </button>
          <button
            disabled={busy}
            onClick={() => act('MEDICAL', { critical: true }, 'medical unit on site')}
            className="rounded border border-emerald-700 bg-emerald-950/50 px-2 py-1.5 text-xs text-emerald-300 hover:bg-emerald-900/50 disabled:opacity-50"
          >
            Medical on-site
          </button>
          <button
            disabled={busy}
            onClick={() => act('RESCUED', {}, 'all victims evacuated')}
            className="rounded border border-green-600 bg-green-900/40 px-2 py-1.5 text-xs text-green-300 hover:bg-green-800/50 disabled:opacity-50"
          >
            Mark rescued
          </button>
          <button
            disabled={busy || !canCommand}
            onClick={() => act('FALSE', {}, 'field inspection: no incident')}
            className="col-span-2 rounded border border-red-800 bg-red-950/40 px-2 py-1.5 text-xs text-red-300 hover:bg-red-900/50 disabled:opacity-40"
            title={canCommand ? '' : 'COMMANDER role required'}
          >
            Mark FALSE (commander only)
          </button>
        </div>
      </div>

      {priority?.history && priority.history.length > 1 && (() => {
        const unique = priority.history.filter((h, i, arr) =>
          i === 0 || h.score.toFixed(2) !== arr[i - 1].score.toFixed(2) || h.level !== arr[i - 1].level,
        )
        if (unique.length <= 1) return null
        return (
          <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/80 p-3">
            <div className="text-[11px] font-semibold tracking-widest text-slate-400 uppercase">Priority history</div>
            <div className="mt-1.5 space-y-1">
              {[...unique].reverse().map((h, i) => (
                <div key={i} className="flex justify-between text-[11px] text-slate-400">
                  <span>{new Date(h.timestamp).toLocaleTimeString()}</span>
                  <span>
                    {h.level} · {h.score.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )
      })()}

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/80 p-3">
        <div className="flex items-baseline justify-between">
          <span className="text-[11px] font-semibold tracking-widest text-slate-400 uppercase">
            Evidence timeline
          </span>
          <span className="text-[10px] text-slate-500">{evidence?.length ?? '…'} sources</span>
        </div>
        {evidence && evidence.length === 0 && (
          <div className="mt-2 text-[11px] text-slate-500">No evidence recorded.</div>
        )}
        {evidence && evidence.length > 0 && (
          <ol className="mt-2 space-y-0">
            {evidence.map((e, i) => {
              const attrs = Object.entries(e.extraction?.attributes ?? {}).filter(
                ([, v]) => v.value === true,
              )
              const llmMerged = e.extraction?.llm?.status === 'merged'
              return (
                <li key={e.event_id} className="relative flex gap-2 pb-3">
                  {i < evidence.length - 1 && (
                    <span className="absolute top-4 left-[4.5px] h-full w-px bg-slate-800" />
                  )}
                  <span
                    className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                      e.flagged ? 'bg-amber-400' : e.relationship === 'FIELD_VERIFIED' ? 'bg-emerald-400' : 'bg-cyan-500'
                    }`}
                    title={e.flagged ? `flagged: ${e.flagged}` : e.relationship}
                  />
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="rounded bg-slate-800 px-1 py-px font-mono text-[9px] text-slate-400">
                        {e.source_type}
                      </span>
                      <span className="font-mono text-[10px] text-slate-500">
                        {new Date(e.timestamp).toLocaleTimeString()}
                      </span>
                      {e.flagged && (
                        <span className="rounded bg-amber-950/60 px-1 py-px text-[9px] text-amber-300">
                          {e.flagged}
                        </span>
                      )}
                      {llmMerged && (
                        <span className="rounded bg-violet-950/60 px-1 py-px text-[9px] text-violet-300" title={e.extraction?.llm?.model_version}>
                          LLM
                        </span>
                      )}
                      <span className="rounded bg-slate-800 px-1 py-px text-[9px] text-slate-400">
                        {e.relationship.toLowerCase().replace('_', ' ')}
                      </span>
                    </div>
                    <div className="mt-0.5 line-clamp-2 text-[11px] text-slate-300">{e.text}</div>
                    <div className="mt-0.5 flex flex-wrap gap-1">
                      <span className="text-[9px] text-slate-500">
                        sev {e.extraction?.severity ?? '?'} · conf {Math.round(e.confidence * 100)}%
                      </span>
                      {attrs.length > 0 && (
                        <span className="text-[9px] text-cyan-400">
                          {attrs.map(([k]) => k.replace('_', ' ')).join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              )
            })}
          </ol>
        )}
      </div>

      {msg && <div className="mt-2 rounded bg-slate-800 px-2 py-1.5 text-xs text-slate-300">{msg}</div>}
    </div>
  )
}