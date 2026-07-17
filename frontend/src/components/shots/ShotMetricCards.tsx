import { MetricValue } from "../teams/MetricValue";
import type { ShotAnalyticsSummary } from "../../api/types";

export function ShotMetricCards({ summary }: { summary: ShotAnalyticsSummary }) {
  const cards: Array<[string, number | null, boolean]> = [["Attempts", summary.attempts, false], ["Makes", summary.makes, false], ["FG%", summary.fg_percentage, true], ["3PT%", summary.three_point_percentage, true], ["eFG%", summary.effective_fg_percentage, true], ["Expected FG%", summary.expected_fg_percentage, true], ["Expected Points", summary.expected_points, false], ["Average Distance", summary.average_distance, false]];
  return <div className="metric-grid shot-metric-grid">{cards.map(([label, value, percent]) => <div className="metric-card" key={label}><small>{label}</small><strong><MetricValue value={value} percent={percent} /></strong></div>)}</div>;
}
