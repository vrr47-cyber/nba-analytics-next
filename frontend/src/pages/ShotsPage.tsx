import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { Envelope, ShotAnalyticsSummary, ShotDistribution } from "../api/types";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { TeamCoverageBanner } from "../components/teams/TeamCoverageBanner";
import { ShotMetricCards } from "../components/shots/ShotMetricCards";
import { ShotMethodology } from "../components/shots/ShotMethodology";
import { ShotScopeSelector } from "../components/shots/ShotScopeSelector";
import { ShotTypeDistribution } from "../components/shots/ShotTypeDistribution";
import { ShotZoneHeatmap } from "../components/shots/ShotZoneHeatmap";
import { ShotZoneTable } from "../components/shots/ShotZoneTable";

export function ShotsPage() {
  const [params] = useSearchParams(); const season = params.get("season") ?? undefined; const competition = params.get("competition") ?? undefined; const [summary, setSummary] = useState<Envelope<ShotAnalyticsSummary> | null>(null); const [zones, setZones] = useState<Envelope<ShotDistribution[]> | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { setSummary(null); setZones(null); setError(null); Promise.all([api.shotSummary({ season, competition }), api.shotZones({ season, competition })]).then(([summaryResponse, zonesResponse]) => { setSummary(summaryResponse); setZones(zonesResponse); }).catch((e: Error) => setError(e.message)); }, [season, competition]);
  return <section><header className="page-heading"><p className="eyebrow">Shot analytics</p><h1>Shot Analytics</h1><p>Understand shot location and efficiency within the recorded, coverage-aware sample.</p></header><ShotScopeSelector />{!summary && !error && <LoadingState />}{error && <ErrorState message={error} />}{summary && zones && <><TeamCoverageBanner response={summary} />{summary.data.attempts === 0 ? <EmptyState message="There are no validated shot observations in this scope." /> : <><ShotMetricCards summary={summary.data} /><div className="shot-grid"><section className="panel"><h2>Zone breakdown</h2><ShotZoneTable zones={zones.data} /></section><section className="panel"><h2>Shot type distribution</h2><ShotTypeDistribution distributions={summary.data.shot_type_distribution} /></section></div><section className="panel"><h2>Zone heatmap</h2><ShotZoneHeatmap zones={zones.data} /></section><ShotMethodology /><p className="shot-backlink"><Link to="/players">View player analytics →</Link></p></>}</>}</section>;
}
