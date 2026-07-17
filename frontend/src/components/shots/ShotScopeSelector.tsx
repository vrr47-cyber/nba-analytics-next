import { useSearchParams } from "react-router-dom";

export function ShotScopeSelector() {
  const [params, setParams] = useSearchParams();
  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    value ? next.set(key, value) : next.delete(key);
    setParams(next);
  };
  return <div className="shot-scope" aria-label="Shot analytics scope"><label>Season<input aria-label="Shot season" value={params.get("season") ?? ""} onChange={(event) => update("season", event.target.value)} placeholder="All seasons" /></label><label>Competition<input aria-label="Shot competition" value={params.get("competition") ?? ""} onChange={(event) => update("competition", event.target.value)} placeholder="All competitions" /></label></div>;
}
