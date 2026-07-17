import type { ShotDistribution } from "../../api/types";

export function ShotZoneTable({ zones }: { zones: ShotDistribution[] }) {
  if (!zones.length) return <p className="unavailable">No zone observations available.</p>;
  return <div className="table-wrap"><table><thead><tr><th>Zone</th><th>Attempts</th><th>Share</th></tr></thead><tbody>{zones.map((zone) => <tr key={zone.key}><td>{zone.key}</td><td>{zone.attempts}</td><td>{zone.share === null ? "—" : `${(zone.share * 100).toFixed(1)}%`}</td></tr>)}</tbody></table></div>;
}
