import type { ShotDistribution } from "../../api/types";

const MIN_HEATMAP_ATTEMPTS = 20;

export function ShotZoneHeatmap({ zones }: { zones: ShotDistribution[] }) {
  const attempts = zones.reduce((total, zone) => total + zone.attempts, 0);
  if (attempts < MIN_HEATMAP_ATTEMPTS) return <p className="unavailable">Insufficient data for a zone heatmap (minimum {MIN_HEATMAP_ATTEMPTS} attempts).</p>;
  return <div className="shot-heatmap" aria-label="Shot zone heatmap">{zones.map((zone) => <div key={zone.key} style={{ opacity: 0.35 + (zone.share ?? 0) }}><strong>{zone.key}</strong><span>{zone.attempts} attempts</span></div>)}</div>;
}
