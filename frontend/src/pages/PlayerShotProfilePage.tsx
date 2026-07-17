import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { Envelope, PlayerDetail, PlayerShotProfile, ShotDistribution } from "../api/types";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { PlayerAttribution } from "../components/players/PlayerAttribution";
import { TeamCoverageBanner } from "../components/teams/TeamCoverageBanner";
import { ShotChart } from "../components/shots/ShotChart";
import { ShotMetricCards } from "../components/shots/ShotMetricCards";
import { ShotMethodology } from "../components/shots/ShotMethodology";
import { ShotScopeSelector } from "../components/shots/ShotScopeSelector";
import { ShotTypeDistribution } from "../components/shots/ShotTypeDistribution";
import { ShotZoneHeatmap } from "../components/shots/ShotZoneHeatmap";
import { ShotZoneTable } from "../components/shots/ShotZoneTable";

export function PlayerShotProfilePage() {
  const { playerId } = useParams(); const [params] = useSearchParams(); const season = params.get("season") ?? undefined; const competition = params.get("competition") ?? undefined; const [shots, setShots] = useState<Envelope<PlayerShotProfile> | null>(null); const [player, setPlayer] = useState<Envelope<PlayerDetail> | null>(null); const [zones, setZones] = useState<Envelope<ShotDistribution[]> | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!playerId) return; setShots(null); setPlayer(null); setZones(null); setError(null); Promise.all([api.playerShots(playerId, { season, competition }), api.player(playerId, { season, competition }), api.shotZones({ season, competition, player_id: playerId })]).then(([shotResponse, playerResponse, zoneResponse]) => { setShots(shotResponse); setPlayer(playerResponse); setZones(zoneResponse); }).catch((e: Error) => setError(e.message)); }, [playerId, season, competition]);
  if (error) return <ErrorState message={error} />; if (!shots || !player || !zones) return <LoadingState />; const summary = shots.data.summary;
  return <section><Link to="/shots">← Shot Analytics</Link><header className="team-header"><p className="eyebrow">Player shot profile</p><h1>{player.data.name}</h1><PlayerAttribution player={player.data} /><p>Shot profile for the selected recorded scope.</p></header><ShotScopeSelector /><TeamCoverageBanner response={shots} />{summary.attempts === 0 ? <EmptyState message="No validated shot observations are available for this player and scope." /> : <><ShotMetricCards summary={summary} /><div className="shot-grid"><section className="panel"><h2>Shot chart</h2><ShotChart coordinates={summary.coordinates} /></section><section className="panel"><h2>Zone breakdown</h2><ShotZoneTable zones={zones.data} /></section></div><div className="shot-grid"><section className="panel"><h2>Shot type distribution</h2><ShotTypeDistribution distributions={summary.shot_type_distribution} /></section><section className="panel"><h2>Zone heatmap</h2><ShotZoneHeatmap zones={zones.data} /></section></div><ShotMethodology /></>}</section>;
}
