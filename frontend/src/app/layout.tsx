import { Outlet } from "react-router-dom";
import { AppNavigation } from "../components/AppNavigation";
export function Layout() { return <><AppNavigation /><main className="shell"><Outlet /></main></>; }
