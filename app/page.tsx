"use client";

import { useMemo, useState } from "react";

const leaders = [
  { name: "Shai Gilgeous-Alexander", team: "OKC", value: "32.1", meta: "Points / game", color: "cyan" },
  { name: "Giannis Antetokounmpo", team: "MIL", value: "30.8", meta: "Points / game", color: "orange" },
  { name: "Luka Dončić", team: "DAL", value: "28.7", meta: "Points / game", color: "blue" },
  { name: "Jayson Tatum", team: "BOS", value: "27.2", meta: "Points / game", color: "green" },
  { name: "Nikola Jokić", team: "DEN", value: "26.1", meta: "Points / game", color: "purple" },
];

const teams = [
  { rank: 1, name: "Boston Celtics", abbr: "BOS", record: "64–18", rating: "1248", net: "+12.1", color: "green" },
  { rank: 2, name: "Oklahoma City Thunder", abbr: "OKC", record: "62–20", rating: "1247", net: "+11.8", color: "blue" },
  { rank: 3, name: "Denver Nuggets", abbr: "DEN", record: "57–25", rating: "1221", net: "+8.9", color: "gold" },
  { rank: 4, name: "Cleveland Cavaliers", abbr: "CLE", record: "55–27", rating: "1198", net: "+7.4", color: "red" },
];

const navItems = ["Explore", "Teams", "Players", "Shot Analytics", "Standings & Power", "Playoff Forecast", "Live", "Methodology"];

export default function Home() {
  const [activeNav, setActiveNav] = useState("Explore");
  const [leaderTab, setLeaderTab] = useState("Points per game");
  const [query, setQuery] = useState("");
  const [season, setSeason] = useState("2025–26");

  const visibleLeaders = useMemo(() => {
    if (!query.trim()) return leaders;
    return leaders.filter((leader) => leader.name.toLowerCase().includes(query.toLowerCase()));
  }, [query]);

  return (
    <main className="site-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">✦</div>
          <div><div className="brand-name">NBA <span>ANALYTICS</span></div><div className="brand-tagline">Find the signal.</div></div>
        </div>
        <nav className="primary-nav" aria-label="Primary navigation">
          {navItems.map((item) => <button key={item} className={activeNav === item ? "nav-link active" : "nav-link"} onClick={() => setActiveNav(item)}>{item}</button>)}
        </nav>
        <div className="top-actions">
          <label className="search-box"><span>⌕</span><input aria-label="Search players or teams" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search players, teams..." /></label>
          <button className="icon-button" aria-label="Refresh data">↻</button><button className="icon-button" aria-label="Toggle theme">◐</button>
        </div>
      </header>

      <section className="page-heading">
        <div><div className="eyebrow">ANALYTICAL HOME · LIVE SIGNALS + TRUSTED DATA</div><h1>The league, <em>decoded.</em></h1><p>See what is actually driving the NBA — team strength, player production, shot quality, and the outlook ahead.</p></div>
        <div className="heading-controls"><select value={season} onChange={(event) => setSeason(event.target.value)} aria-label="Season"><option>2025–26</option><option>2024–25</option><option>2023–24</option></select><button className="season-toggle">Regular season <span>⌄</span></button></div>
      </section>

      <section className="status-row" aria-label="Data status"><span className="live-dot" /> <strong>Data is fresh</strong><span>Updated 18 minutes ago</span><span className="status-divider" /><span>Team coverage <b>100%</b></span><span>Player coverage <b>99.4%</b></span><span>Shot model <b>412 qualified</b></span><button className="status-link">View data status →</button></section>

      <section className="dashboard-grid">
        <aside className="rail left-rail">
          <Panel title="LIVE NOW" action="View all →" accent="red">
            <div className="game-card"><div className="game-meta"><span className="live-pill">● LIVE</span><span>4th · 3:12</span></div><div className="team-line"><span className="team-badge lakers">LA</span><strong>LAL</strong><b>102</b></div><div className="team-line"><span className="team-badge bucks">MIL</span><strong>MIL</strong><b>98</b></div><div className="win-bar"><span style={{width:"62%"}} /></div><div className="win-label"><span>Win probability</span><strong>LAL 62%</strong></div></div>
            <div className="game-card"><div className="game-meta"><span>4th · 5:45</span><span className="live-pill">● LIVE</span></div><div className="team-line"><span className="team-badge nugget">DEN</span><strong>DEN</strong><b>96</b></div><div className="team-line"><span className="team-badge suns">PHX</span><strong>PHX</strong><b>91</b></div><div className="win-bar orange"><span style={{width:"71%"}} /></div><div className="win-label"><span>Win probability</span><strong>DEN 71%</strong></div></div>
            <button className="panel-link">Go to live center <span>↗</span></button>
          </Panel>
          <Panel title="TRENDING PLAYERS" action="View all →" accent="purple"><div className="rank-list">{["Nikola Jokić", "Luka Dončić", "Shai Gilgeous-Alexander", "Jayson Tatum", "Victor Wembanyama"].map((name, index) => <div className="rank-row" key={name}><span>{index+1}</span><strong>{name}</strong><small>{["DEN","DAL","OKC","BOS","SAS"][index]}</small></div>)}</div><button className="panel-link">Explore all players <span>↗</span></button></Panel>
        </aside>

        <div className="main-column">
          <section className="hero-card"><div className="hero-glow" /><div className="hero-copy"><div className="eyebrow">MODEL POWER RANK · EAST #1</div><h2>Boston <span>Celtics</span></h2><div className="hero-record"><strong>64–18</strong><span>1st in East</span><span className="positive">+12.1 net rating</span></div><p>Best offense in the league, top-five defense, and the clearest path to a repeat.</p><div className="hero-actions"><button className="primary-button">Team intelligence <span>↗</span></button><button className="secondary-button">Full standings</button></div></div><div className="hero-players"><div className="player-orb orb-one">JT</div><div className="player-orb orb-two">JB</div><div className="player-orb orb-three">KP</div><div className="hero-silhouette">BOS</div></div><div className="hero-metrics"><Metric label="OFF RATING" value="121.4" rank="1st" /><Metric label="DEF RATING" value="109.3" rank="2nd" /><Metric label="NET RATING" value="+12.1" rank="1st" /><Metric label="PACE" value="98.7" rank="16th" /></div></section>

          <section className="leaders-card"><div className="section-header"><div><div className="eyebrow purple-text">LEAGUE LEADERS</div><h3>Who is moving the numbers?</h3></div><button className="mini-link">View all leaders →</button></div><div className="leader-tabs">{["Points per game", "Rebounds per game", "Assists per game", "True shooting %", "Net rating"].map((tab) => <button key={tab} onClick={() => setLeaderTab(tab)} className={leaderTab === tab ? "leader-tab selected" : "leader-tab"}>{tab}</button>)}</div><div className="leader-grid">{visibleLeaders.map((leader, index) => <article className={`leader-card ${leader.color}`} key={leader.name}><div className="leader-avatar">{leader.name.split(" ").map((word) => word[0]).join("").slice(0,2)}</div><div className="leader-rank">0{index + 1}</div><div className="leader-name">{leader.name}</div><div className="leader-team">{leader.team} <span>·</span> {leader.meta}</div><div className="leader-value">{leaderTab === "Points per game" ? leader.value : ["12.4", "9.8", "8.7", "7.1", "6.9"][index]}</div></article>)}</div></section>

          <section className="insight-grid"><InsightCard icon="↗" title="Best offense" metric="121.4" note="Boston Celtics · #1 league rank" color="green" /><InsightCard icon="◒" title="Best defense" metric="108.7" note="Oklahoma City · #1 league rank" color="blue" /><InsightCard icon="≈" title="Shot maker above expected" metric="+6.8%" note="Jalen Brunson · 1,042 shots" color="purple" /></section>
        </div>

        <aside className="rail right-rail"><Panel title="PLAYOFF OUTLOOK" action="Apr 21, 2025" accent="purple"><div className="forecast-head"><strong>Boston is the favorite.</strong><span>Model v2.4 · 82k sims</span></div><div className="forecast-chart"><div className="chart-line" /><div className="chart-dot dot-a" /><div className="chart-dot dot-b" /><div className="chart-dot dot-c" /><span className="chart-label label-a">BOS 98%</span><span className="chart-label label-b">OKC 64%</span><span className="chart-label label-c">DEN 42%</span></div><button className="panel-link">Open full forecast <span>↗</span></button></Panel><Panel title="POWER RANKINGS" action="Model rating" accent="gold"><div className="power-list">{teams.map((team) => <div className="power-row" key={team.name}><span className={`mini-team ${team.color}`}>{team.abbr.slice(0,1)}</span><span className="power-rank">{team.rank}</span><strong>{team.name}</strong><b>{team.rating}</b></div>)}</div><button className="panel-link">See all 30 teams <span>↗</span></button></Panel><Panel title="COVERAGE CHECK" action="Transparent by default" accent="cyan"><div className="coverage-list"><Coverage label="Completed team games" value="100%" /><Coverage label="Player box scores" value="99.4%" /><Coverage label="Shot model eligible" value="412" /><Coverage label="Forecast freshness" value="18m" /></div><button className="panel-link">How we calculate everything <span>↗</span></button></Panel></aside>
      </section>

      <section className="question-strip"><div><div className="eyebrow purple-text">START WITH A QUESTION</div><h2>What do you want to understand?</h2></div><div className="question-links"><button onClick={() => setActiveNav("Teams")}>Who is actually strongest? <span>→</span></button><button onClick={() => setActiveNav("Shot Analytics")}>Who is beating shot quality? <span>→</span></button><button onClick={() => setActiveNav("Playoff Forecast")}>Who has the clearest path? <span>→</span></button></div></section>

      <footer className="footer"><span>NBA ANALYTICS <small>Transparent analysis, built for the curious.</small></span><div><button>Methodology</button><button>Data status</button><button>Labs</button></div><span className="footer-note">External providers own the full game archive.</span></footer>
    </main>
  );
}

function Panel({ title, action, accent, children }: { title: string; action: string; accent: string; children: React.ReactNode }) { return <section className={`panel ${accent}`}><div className="panel-header"><span>{title}</span><small>{action}</small></div>{children}</section>; }
function Metric({ label, value, rank }: { label: string; value: string; rank: string }) { return <div className="metric"><span>{label}</span><strong>{value}</strong><small>{rank}</small></div>; }
function InsightCard({ icon, title, metric, note, color }: { icon: string; title: string; metric: string; note: string; color: string }) { return <article className={`insight-card ${color}`}><div className="insight-icon">{icon}</div><div><span>{title}</span><strong>{metric}</strong><small>{note}</small></div><button aria-label={`Open ${title}`}>↗</button></article>; }
function Coverage({ label, value }: { label: string; value: string }) { return <div className="coverage-row"><span className="coverage-check">✓</span><span>{label}</span><strong>{value}</strong></div>; }
