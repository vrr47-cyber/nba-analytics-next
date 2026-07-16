import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Status } from "../api/types";
import { CoverageStatus } from "../components/CoverageStatus";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
export function DataStatusPage() { const [status, setStatus] = useState<Status | null>(null); const [error, setError] = useState<string | null>(null); useEffect(() => { api.status().then(setStatus).catch((e: Error) => setError(e.message)); }, []); return <><h1>Data status</h1><p>Operational truth for the application foundation.</p>{!status && !error && <LoadingState />}{error && <ErrorState message={error} />}{status && <><div className="status-grid"><div><span>Database</span><strong>{status.database_ready ? "Ready" : "Not ready"}</strong><small>{status.database_status}</small></div><div><span>Provider</span><strong>{status.provider_ready ? "Ready" : "Unconfigured"}</strong><small>{status.provider_reason}</small></div><div><span>Dataset</span><strong>{status.publication_ready ? "Publishable" : "Unavailable"}</strong><small>{status.publication_reason}</small></div></div><CoverageStatus coverage={{included_games:0,expected_games:null,included_entities:0,expected_entities:null,ratio:null,complete:false,publishable:false,reason:"No validated season dataset is available."}} /><EmptyState message="The status endpoint reports no validated seasons, model versions, or source runs." /></>}</>; }
