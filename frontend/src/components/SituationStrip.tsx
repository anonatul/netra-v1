import type { Incident, MapData, SystemStatus } from '../api'

export default function SituationStrip({
  status,
  incidents,
  mapData,
}: {
  status: SystemStatus | null
  incidents: Incident[]
  mapData: MapData | null
}) {
  const events = status?.total_events ?? 0
  const incs = status?.total_incidents ?? 0
  const zones = mapData?.zones.length ?? 0
  const critical = incidents.filter((i) => i.priority === 'P1').length
  const dedup = events > 0 ? Math.round((1 - incs / events) * 100) : 0
  const bySource = status?.events_by_source ?? {}
  const sourceEntries = Object.entries(bySource).sort(([, a], [, b]) => b - a)
  const sourceMax = Math.max(...sourceEntries.map(([, value]) => value), 1)

  const Metric = ({ label, value, detail, accent }: { label: string; value: string; detail: string; accent: string }) => (
    <div className="netra-metric-card">
      <div className="netra-metric-label">{label}</div>
      <div className={`netra-metric-value ${accent}`}>{value}</div>
      <div className="netra-metric-detail">{detail}</div>
    </div>
  )

  return (
    <section className="netra-metrics" aria-label="Live operations summary">
      <Metric label="Signals received" value={String(events)} detail="raw reports" accent="netra-accent-violet" />
      <Metric label="Triaged incidents" value={String(incs)} detail={`${dedup}% deduplicated`} accent="netra-accent-blue" />
      <Metric label="Open response" value={String(status?.open_incidents ?? 0)} detail={`${zones} active zones`} accent="netra-accent-sage" />
      <Metric label="Priority one" value={String(critical)} detail={critical ? 'immediate attention' : 'no critical cases'} accent={critical ? 'netra-accent-rust' : 'netra-accent-muted'} />
      <div className="netra-source-card">
        <div className="netra-metric-label">Signal mix</div>
        <div className="netra-source-list">
          {sourceEntries.length > 0 ? sourceEntries.map(([source, count]) => (
            <div key={source} className="netra-source-row">
              <span>{source}</span>
              <div className="netra-source-track"><span style={{ width: `${Math.max((count / sourceMax) * 100, 8)}%` }} /></div>
              <strong>{count}</strong>
            </div>
          )) : <span className="netra-metric-detail">Waiting for source data</span>}
        </div>
        {status?.connectivity_mode && <span className="netra-connectivity">{status.connectivity_mode}</span>}
      </div>
    </section>
  )
}