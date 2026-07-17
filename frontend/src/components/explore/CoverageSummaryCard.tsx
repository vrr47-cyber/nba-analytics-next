import type { ExploreData } from "../../api/types";
import { ExploreCard } from "./ExploreCard";
export function CoverageSummaryCard({ data }: { data: ExploreData }) { return <ExploreCard title="Coverage"><p>{data.coverage_summary.recent_games.included_games} recent final games in the recorded scope.</p><small>{data.coverage_summary.teams.reason}</small></ExploreCard>; }
