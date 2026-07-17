import { Link } from "react-router-dom";

export function ShotMethodology() { return <section className="methodology"><h2>Methodology</h2><p>Shot attempts use canonical game, team, and player mappings. Expected FG is a transparent distance-and-shot-type lookup and remains unavailable until enough observations exist.</p><p><Link to="/data-status">Review coverage and provenance</Link> · <Link to="/players">Explore player definitions</Link></p></section>; }
