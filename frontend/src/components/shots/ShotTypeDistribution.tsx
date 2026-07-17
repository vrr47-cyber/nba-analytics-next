import type { ShotDistribution } from "../../api/types";

export function ShotTypeDistribution({ distributions }: { distributions: ShotDistribution[] }) {
  if (!distributions.length) return <p className="unavailable">No shot-type observations available.</p>;
  return <ul className="shot-distribution">{distributions.map((item) => <li key={item.key}><span>{item.key.replaceAll("_", " ")}</span><strong>{item.attempts}</strong><small>{item.share === null ? "—" : `${(item.share * 100).toFixed(1)}% of attempts`}</small></li>)}</ul>;
}
