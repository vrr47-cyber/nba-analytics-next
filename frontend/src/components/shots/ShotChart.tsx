import type { ShotCoordinate } from "../../api/types";

function scale(value: number, minimum: number, maximum: number) { return maximum === minimum ? 50 : 10 + ((value - minimum) / (maximum - minimum)) * 80; }

export function ShotChart({ coordinates }: { coordinates: ShotCoordinate[] }) {
  if (!coordinates.length) return <p className="unavailable">No normalized coordinates are available for a shot chart.</p>;
  const xs = coordinates.map((point) => point.x); const ys = coordinates.map((point) => point.y); const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
  return <div className="shot-chart"><svg role="img" aria-label="Shot chart using normalized coordinates" viewBox="0 0 100 100"><rect x="5" y="5" width="90" height="90" rx="4" fill="none" /><line x1="50" y1="5" x2="50" y2="95" /><line x1="5" y1="50" x2="95" y2="50" />{coordinates.map((point, index) => <circle key={`${point.x}-${point.y}-${index}`} cx={scale(point.x, minX, maxX)} cy={100 - scale(point.y, minY, maxY)} r="2.8" className={point.result === "made" ? "shot-made" : "shot-missed"}><title>{point.shot_type.replaceAll("_", " ")} — {point.result}</title></circle>)}</svg><small>Normalized provider coordinates; the recorded sample is not a complete shot map.</small></div>;
}
