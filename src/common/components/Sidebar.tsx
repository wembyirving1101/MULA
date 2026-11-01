import Icon from "./Icon";
import MulaLogo from "./MulaLogo";

type Props = {
  active: "workspace" | "team";
  username: string;
  onSignOut: () => void;
  busy?: boolean;
};

export default function Sidebar({ active, username, onSignOut, busy = false }: Props) {
  let workspaceClass = "nav-item";
  let teamClass = "nav-item";
  let workspaceCurrent: "page" | undefined;
  let teamCurrent: "page" | undefined;
  if (active === "workspace") { workspaceClass += " active-nav"; workspaceCurrent = "page"; }
  if (active === "team") { teamClass += " active-nav"; teamCurrent = "page"; }
  return (
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Mula home"><MulaLogo /></a>
        <div className="sidebar-caption">A little support. A new beginning.</div>
        <nav aria-label="Main navigation">
          <a className={workspaceClass} href="/" aria-current={workspaceCurrent}><Icon name="home" />Workspace{active === "workspace" && <span className="nav-dot" />}</a>
          <button className="nav-item" disabled title="Reports are coming soon"><Icon name="report" />Reports<span className="soon">Soon</span></button>
          <button className="nav-item" disabled title="Website builder is coming soon"><Icon name="website" />My website<span className="soon">Soon</span></button>
          <a className={teamClass} href="/team" aria-current={teamCurrent}><Icon name="team" />My team{active === "team" && <span className="nav-dot" />}</a>
        </nav>
        <div className="sidebar-note"><span className="tiny-sun" aria-hidden="true">◒</span><p>Big things begin<br />with a small step.</p></div>
        <div className="sidebar-bottom">
          <span className="avatar">{username.slice(0, 1).toUpperCase()}</span>
          <div><strong>{username}</strong><span>Your workspace</span></div>
          <button className="icon-button signout" aria-label="Sign out" onClick={onSignOut} disabled={busy}><Icon name="exit" /></button>
        </div>
      </aside>
  );
}
