import { NavLink } from "react-router-dom";
export function AppNavigation() { return <header className="nav"><a className="brand" href="/">NBA Analytics <span>foundation</span></a><nav aria-label="Primary"><NavLink to="/" end>Explore</NavLink><NavLink to="/teams">Teams</NavLink><NavLink to="/data-status">Data status</NavLink></nav></header>; }
