import { createBrowserRouter } from "react-router-dom";
import { Layout } from "./layout";
import { DataStatusPage } from "../pages/DataStatusPage";
import { ExplorePage } from "../pages/ExplorePage";
import { NotFoundPage } from "../pages/NotFoundPage";
export const router = createBrowserRouter([{ path: "/", element: <Layout />, children: [{ index: true, element: <ExplorePage /> }, { path: "data-status", element: <DataStatusPage /> }, { path: "*", element: <NotFoundPage /> }] }]);
