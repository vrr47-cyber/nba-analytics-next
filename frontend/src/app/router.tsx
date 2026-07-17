import { createBrowserRouter } from "react-router-dom";
import { Layout } from "./layout";
import { DataStatusPage } from "../pages/DataStatusPage";
import { ExplorePage } from "../pages/ExplorePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { TeamsPage } from "../pages/TeamsPage";
import { TeamDetailPage } from "../pages/TeamDetailPage";
export const router = createBrowserRouter([{ path: "/", element: <Layout />, children: [{ index: true, element: <ExplorePage /> }, { path: "teams", element: <TeamsPage /> }, { path: "teams/:teamId", element: <TeamDetailPage /> }, { path: "data-status", element: <DataStatusPage /> }, { path: "*", element: <NotFoundPage /> }] }]);
