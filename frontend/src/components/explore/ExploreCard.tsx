import type { ReactNode } from "react";
export function ExploreCard({ title, children, link }: { title: string; children: ReactNode; link?: ReactNode }) { return <section className="explore-card"><div className="explore-card-heading"><h2>{title}</h2>{link}</div>{children}</section>; }
