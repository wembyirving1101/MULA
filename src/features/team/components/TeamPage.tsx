"use client";

import { useEffect, useRef, useState } from "react";
import { AccountForm } from "@/features/auth";
import { Icon, MulaLogo, Sidebar } from "@/common/components";
import "../team.css";

const agents = [
  { id: "operator", name: "Operator", role: "Your starting point", initial: "O", available: true,
    description: "Your partner for turning a busy mind into a clear next step. Talk through ideas, make a plan, and keep your business moving.",
    capabilities: ["Think through business ideas", "Plan daily operations", "Continue your saved conversation"],
    handoff: "The Operator is available for planning and guidance. Specialist delegation will come as more agents join." },
  { id: "inventory", name: "Inventory", role: "Keep things in stock", initial: "I", available: false,
    description: "A planned teammate for understanding stock levels and spotting what needs attention.",
    capabilities: ["Track stock availability", "Flag low-stock items", "Help plan replenishment"],
    handoff: "Planned connection: share stock needs with the Operator and Procurement." },
  { id: "forecasting", name: "Forecasting", role: "See what’s ahead", initial: "F", available: false,
    description: "A planned teammate for turning business data into a clearer picture of future demand.",
    capabilities: ["Explore sales trends", "Estimate future demand", "Explain forecast uncertainty"],
    handoff: "Planned connection: help the Operator and Inventory prepare for changing demand." },
  { id: "procurement", name: "Procurement", role: "Find the right supplies", initial: "P", available: false,
    description: "A planned teammate for comparing suppliers and preparing purchasing decisions.",
    capabilities: ["Compare supplier options", "Prepare purchase recommendations", "Coordinate replenishment needs"],
    handoff: "Planned connection: turn inventory needs into purchase proposals for owner review." },
  { id: "customer-service", name: "Customer service", role: "Care for your customers", initial: "C", available: false,
    description: "A planned teammate for helping customers get timely answers, with room for human support.",
    capabilities: ["Answer common questions", "Use approved business information", "Escalate issues to a human"],
    handoff: "Planned connection: bring customer issues and questions to the Operator." },
  { id: "website", name: "Website", role: "Build your front door", initial: "W", available: false,
    description: "A planned teammate for shaping your website using the building blocks available in Mula.",
    capabilities: ["Recommend supported page blocks", "Help personalize your website", "Explain available feature options"],
    handoff: "Planned connection: work with the Operator to translate your idea into a supported website." },
];

export default function TeamPage() {
  const [account, setAccount] = useState<{ username: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [signingOut, setSigningOut] = useState(false);
  const [selectedId, setSelectedId] = useState("operator");
  const detail = useRef<HTMLElement>(null);
  const selected = agents.find((agent) => agent.id === selectedId)!;

  function selectAgent(id: string) {
    setSelectedId(id);
    // On smaller screens the inspector sits below the office, outside view.
    if (window.matchMedia("(max-width: 1050px)").matches) {
      let behavior: ScrollBehavior = "smooth";
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) behavior = "auto";
      detail.current?.scrollIntoView({ behavior, block: "start" });
    }
  }

  async function loadAccount(signal?: AbortSignal) {
    setError("");
    const response = await fetch("/api/auth/me", { cache: "no-store", signal });
    if (response.status === 401) { setAccount(null); return; }
    if (!response.ok) throw new Error("Could not open your team. Please retry.");
    setAccount(await response.json());
  }

  useEffect(() => {
    const controller = new AbortController();
    loadAccount(controller.signal).catch((failure: Error) => {
      if (!controller.signal.aborted) setError(failure.message);
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
    return () => controller.abort();
  }, []);

  async function signOut() {
    setSigningOut(true);
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok) throw new Error("Could not sign out. Please retry.");
      window.location.assign("/");
    } catch (failure) {
      if (failure instanceof Error) setError(failure.message);
    } finally { setSigningOut(false); }
  }

  if (loading) return <main className="account-screen"><p role="status">Opening your team…</p></main>;
  if (!account && error) return <main className="account-screen"><div><p role="alert">{error}</p><button className="account-submit" onClick={() => window.location.reload()}>Retry</button></div></main>;
  if (!account) return <AccountForm onSignedIn={() => loadAccount()} />;

  return (
    <div className="app-shell team-shell">
      <Sidebar active="team" username={account.username} onSignOut={signOut} busy={signingOut} />
      <main className="team-main">
        <header className="topbar">
          <span className="desktop-title">Your workspace <span className="header-divider">/</span> <strong>My team</strong></span>
          <span className="mobile-brand"><MulaLogo /></span>
          <div className="topbar-actions"><a className="text-button" href="/">Back to Operator</a><button className="mobile-signout icon-button" onClick={signOut} disabled={signingOut} aria-label="Sign out"><Icon name="exit" /></button></div>
        </header>
        <div className="team-content">
          {error && <p className="error" role="alert">{error}</p>}
          <div className="team-intro"><div><div className="eyebrow">GOOD COMPANY FOR YOUR NEXT CHAPTER</div><h1>Your ambition. A little more support.</h1><p>Meet your Operator and explore the team taking shape around you.</p></div><span className="team-count">1 available <span>· 5 planned</span></span></div>
          <section className="office" aria-label="Your AI office">
            <div className="office-heading"><span><Icon name="team" /> Mula office</span><span>Select a teammate to explore</span></div>
            <div className="office-floor">
              <svg className="office-connections" viewBox="0 0 600 480" preserveAspectRatio="none" aria-hidden="true"><path d="M300 240H100V80M300 240H500V80M300 240H100M300 240H500M300 240V400" /></svg>
              {agents.map((agent) => {
                let className = `agent-station station-${agent.id}`;
                if (agent.id === selectedId) className += " selected";
                if (agent.available) className += " available";
                return <button key={agent.id} className={className} onClick={() => selectAgent(agent.id)} aria-pressed={agent.id === selectedId} aria-controls="agent-detail" aria-label={`Explore ${agent.name}`}>
                  <span className="station-avatar"><span>{agent.initial}</span><i aria-hidden="true" /></span>
                  <strong>{agent.name}</strong><span className="station-role">{agent.role}</span>
                  <span className="station-status">{agent.available && <><span className="presence-dot" /> Available</>}{!agent.available && "Planned"}</span>
                </button>;
              })}
            </div>
            <div className="office-legend"><span><i />Planned collaboration paths</span><span>Specialists aren’t connected yet</span></div>
          </section>
          <section className="team-activity"><span className="card-icon"><Icon name="team" /></span><div><h2>Room to grow, at your own pace.</h2><p>Start with your Operator. As specialists become available, this is where you’ll see your team and how they work together.</p></div></section>
        </div>
      </main>
      <aside ref={detail} id="agent-detail" className="agent-detail" aria-label="Selected teammate" aria-live="polite">
        <div className="eyebrow">MEET YOUR TEAMMATE</div><span className="detail-avatar">{selected.initial}</span>
        <div className="detail-title"><h2>{selected.name}</h2><span className="team-status">{selected.available && "Available"}{!selected.available && "Planned"}</span></div>
        <p>{selected.description}</p>
        <h3>{selected.available && "How I can help"}{!selected.available && "What’s planned"}</h3>
        <ul className="capabilities">{selected.capabilities.map((item) => <li key={item}><span aria-hidden="true">↗</span>{item}</li>)}</ul>
        <div className="handoff-note"><Icon name="team" /><p>{selected.handoff}</p></div>
        {selected.available && <a className="outline-button" href="/">Talk to Operator<Icon name="arrow" /></a>}
        {!selected.available && <div className="planned-notice">This agent isn’t available to hire yet.</div>}
        <div className="team-owner"><span className="avatar">{account.username.slice(0, 1).toUpperCase()}</span><div><strong>You’re in charge.</strong><p>Your business. Your decisions.</p></div></div>
      </aside>
    </div>
  );
}
