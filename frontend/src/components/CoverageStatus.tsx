import type { Coverage } from "../api/types";
export function CoverageStatus({ coverage }: { coverage: Coverage }) { return <div className="coverage"><strong>{coverage.publishable ? "Publishable" : "Not publishable"}</strong><span>{coverage.reason}</span></div>; }
