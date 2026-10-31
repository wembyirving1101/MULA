type IconName = "home" | "report" | "website" | "team" | "send" | "voice" | "muted" | "exit" | "arrow" | "stop";

const paths: Record<IconName, string> = {
  home: "m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z",
  report: "M5 3h9l5 5v13H5ZM14 3v6h5M9 13h6M9 17h6",
  website: "M3 4h18v16H3ZM3 9h18M6 6.5h.01M9 6.5h.01",
  team: "M16 21v-3a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v3M9 10a4 4 0 1 0 0-8 4 4 0 0 0 0 8M17 3a4 4 0 0 1 0 7M22 21v-3a4 4 0 0 0-3-3.87",
  send: "m4 4 17 8-17 8 3-8ZM7 12h14",
  voice: "M4 9h4l5-5v16l-5-5H4ZM17 8a6 6 0 0 1 0 8M20 5a10 10 0 0 1 0 14",
  muted: "M4 9h4l5-5v16l-5-5H4ZM17 9l5 6M22 9l-5 6",
  exit: "M10 4H4v16h6M14 8l4 4-4 4M8 12h13",
  arrow: "M5 12h14m-6-6 6 6-6 6",
  stop: "M6 6h12v12H6Z",
};

export default function Icon({ name }: { name: IconName }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
