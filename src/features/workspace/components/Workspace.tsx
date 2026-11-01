"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { AccountForm } from "@/features/auth";
import Markdown from "react-markdown";
import { Icon, Sidebar } from "@/common/components";
import { MulaLogo } from "@/common/components";
import { OperatorCore } from "@/features/operator";
import { SpeechPlayer } from "@/features/voice";
import type { VoiceState } from "@/features/voice";
import { readChatStream } from "@/features/operator";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  note?: string;
};

const suggestions = [
  { title: "Find my next step", text: "Help me choose the next practical step for my business. Ask me what you need to know." },
  { title: "Plan my day", text: "Help me create a daily operations checklist for my business." },
  { title: "Think through an idea", text: "I have a business idea. Help me think it through and decide where to begin." },
];

export default function Workspace() {
  const [account, setAccount] = useState<{ username: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [accountError, setAccountError] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Ready when you are");
  const controller = useRef<AbortController | null>(null);
  const sessionId = useRef<string | null>(null);
  const conversation = useRef<HTMLDivElement>(null);
  const followMessages = useRef(true);
  const [muted, setMuted] = useState(false);
  const mutedRef = useRef(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [voiceError, setVoiceError] = useState("");
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const voice = useRef<SpeechPlayer | null>(null);
  const [expanded, setExpanded] = useState(false);
  const input = useRef<HTMLTextAreaElement>(null);
  const form = useRef<HTMLFormElement>(null);

  useEffect(() => {
    const element = conversation.current;
    if (element && followMessages.current) element.scrollTop = element.scrollHeight;
  }, [messages, expanded, account]);

  useEffect(() => {
    const player = new SpeechPlayer(setVoiceState, setAnalyser);
    voice.current = player;
    try {
      const saved = localStorage.getItem("mula.voice-muted") === "true";
      mutedRef.current = saved;
      setMuted(saved);
    } catch {
      setVoiceError("Your browser cannot remember voice preferences. You can still mute this session.");
    }
    function onVisibility() {
      if (document.hidden) player.stop();
    }
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      controller.current?.abort();
      document.removeEventListener("visibilitychange", onVisibility);
      void player.dispose();
      voice.current = null;
    };
  }, []);

  function reportVoiceError(failure: unknown) {
    if (failure instanceof Error) setVoiceError(failure.message);
    else setVoiceError("AI voice is unavailable. You can still use chat.");
  }

  function setChatMode(chatOnly: boolean) {
    mutedRef.current = chatOnly;
    setMuted(chatOnly);
    setVoiceError("");
    voice.current?.stop();
    if (!chatOnly) void voice.current?.unlock().catch(reportVoiceError);
    try {
      localStorage.setItem("mula.voice-muted", String(chatOnly));
    } catch {
      setVoiceError("Voice preference applies for this session; your browser could not save it.");
    }
  }

  function playReply(text: string) {
    if (mutedRef.current || document.hidden) return;
    setVoiceError("");
    void voice.current?.speak(text).catch(reportVoiceError);
  }

  function updateReply(id: string, text: string, note?: string) {
    setMessages((previous) =>
      previous.map((message) => {
        if (message.id === id) return { ...message, text, note };
        return message;
      }),
    );
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;

    voice.current?.stop();
    setVoiceError("");
    // Unlock audio during the user's gesture, before waiting for the LLM.
    if (!mutedRef.current) void voice.current?.unlock().catch(reportVoiceError);
    followMessages.current = true;
    const abort = new AbortController();
    controller.current = abort;
    const replyId = crypto.randomUUID();
    setMessages((previous) => [
      ...previous,
      { id: crypto.randomUUID(), role: "user", text },
      { id: replyId, role: "assistant", text: "" },
    ]);
    setDraft("");
    setError("");
    setBusy(true);
    setStatus("Connecting to Operator…");
    let reply = "";
    let firstToken = true;
    const start = performance.now();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          stream: true,
          session_id: sessionId.current,
        }),
        signal: abort.signal,
      });
      if (!response.ok) {
        const failure = await response.json();
        if (typeof failure.detail === "string") throw new Error(failure.detail);
        throw new Error(
          "Please send a message of 1–8,000 characters and try again.",
        );
      }
      if (!response.body)
        throw new Error("Streaming is unavailable in this browser.");

      await readChatStream(response.body, (chunk) => {
        if (chunk.type === "token" && typeof chunk.content === "string") {
          if (firstToken) {
            setStatus(
              `Reply started in ${((performance.now() - start) / 1000).toFixed(1)}s`,
            );
            firstToken = false;
          }
          reply += chunk.content;
          updateReply(replyId, reply);
        }
        if (chunk.type === "done" && chunk.truncated) {
          updateReply(
            replyId,
            reply,
            "Reply reached its length limit. Ask for a shorter answer or a specific section.",
          );
        }
      });
      playReply(reply);
      setStatus("Ready when you are");
    } catch (failure) {
      if (abort.signal.aborted) {
        updateReply(replyId, reply, "Stopped by you.");
        setStatus("Reply stopped");
      } else {
        let detail =
          "Could not complete the reply. Check your connection and try again.";
        if (failure instanceof Error) detail = failure.message;
        setError(detail);
        updateReply(replyId, reply, "Reply incomplete.");
        // Restore the question so a failed request can be edited and sent again.
        setDraft(text);
        setStatus("Could not complete reply");
      }
    } finally {
      controller.current = null;
      setBusy(false);
      input.current?.focus();
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      form.current?.requestSubmit();
    }
  }

  async function loadAccount() {
    setAccountError("");
    const response = await fetch("/api/auth/me", { cache: "no-store" });
    if (response.status === 401) {
      setAccount(null);
      return;
    }
    if (!response.ok) throw new Error("Could not load your account. Check the backend and retry.");
    const user = await response.json();
    const conversation = await fetch("/api/conversation", { cache: "no-store" });
    if (!conversation.ok) throw new Error("Could not load your conversation. Please retry.");
    const saved = await conversation.json();
    sessionId.current = saved.session_id;
    setMessages(saved.messages.map((message: Message) => ({ ...message, id: String(message.id) })));
    setAccount(user);
  }

  useEffect(() => {
    loadAccount().catch((failure: Error) => setAccountError(failure.message)).finally(() => setLoading(false));
  }, []);

  async function signOut() {
    voice.current?.stop();
    const response = await fetch("/api/auth/logout", { method: "POST" });
    if (!response.ok) { setError("Could not sign out. Please retry."); return; }
    // Also stop work started while the sign-out request was in flight.
    controller.current?.abort();
    voice.current?.stop();
    sessionId.current = null;
    setMessages([]);
    setDraft("");
    setError("");
    setAccount(null);
    setVoiceError("");
    setStatus("Ready when you are");
  }

  if (loading) return <main className="account-screen"><p role="status">Opening your workspace…</p></main>;
  if (accountError) return <main className="account-screen"><div><p role="alert">{accountError}</p><button onClick={() => { setLoading(true); loadAccount().catch((failure: Error) => setAccountError(failure.message)).finally(() => setLoading(false)); }}>Retry</button></div></main>;
  if (!account) return <AccountForm onSignedIn={loadAccount} />;

  let presence = "Ready when you are";
  if (busy) presence = "Thinking with you…";
  if (voiceState === "preparing") presence = "Preparing voice…";
  if (voiceState === "speaking") presence = "Speaking…";
  let voiceLabel = "Mute AI voice · switch to chat";
  if (muted) voiceLabel = "Enable AI voice";
  let mainClass = "main-panel";
  if (expanded) mainClass += " conversation-expanded";

  return (
    <div className="app-shell">
      <Sidebar active="workspace" username={account.username} onSignOut={signOut} busy={busy} />

      <main className={mainClass}>
        <header className="topbar">
          <div className="workspace-title"><span className="mobile-brand"><MulaLogo /></span><span className="desktop-title">Your workspace <span className="header-divider">/</span> <strong>Operator</strong></span></div>
          <div className="topbar-actions"><a className="mobile-team-link" href="/team">My team</a><span className="preview-badge">EARLY PREVIEW</span><button className="mobile-signout icon-button" aria-label="Sign out" onClick={signOut} disabled={busy}><Icon name="exit" /></button></div>
        </header>

        <section className="operator-stage" aria-label="Your Operator">
          <div className="eyebrow">A LITTLE CLARITY. A LOT OF POSSIBILITY.</div>
          <OperatorCore analyser={analyser} />
          <h1>I’m here. What are we building today?</h1>
          <div className="presence" role="status"><span className="presence-dot" />{presence}</div>
        </section>

        <div className="conversation-heading">
          <span>YOU & MULA <span className="saved-label">· One ongoing conversation</span></span>
          <button className="text-button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
            {!expanded && "Expand chat"}{expanded && "Show Operator"}
          </button>
        </div>
        <div className="conversation" ref={conversation} onScroll={() => {
          const element = conversation.current;
          if (element) followMessages.current = element.scrollHeight - element.scrollTop - element.clientHeight < 80;
        }}>
          {messages.length === 0 && <div className="empty-conversation"><p>Every beginning starts with a conversation.</p><span>Tell me what’s on your mind. We’ll find the next step together.</span></div>}
          <section className="messages" role="log" aria-label="Chat messages" aria-live="polite" aria-relevant="additions text">
            {messages.map((message) => (
              <article key={message.id} className={`message ${message.role}`}>
                <div className="message-label">{message.role === "assistant" && "Mula"}{message.role === "user" && "You"}</div>
                <div className="message-body">
                  {message.text && <div className="message-text">
                    {message.role === "assistant" && <Markdown skipHtml components={{ a: (props) => <a {...props} target="_blank" rel="noreferrer noopener" /> }}>{message.text}</Markdown>}
                    {message.role === "user" && message.text}
                  </div>}
                  {!message.text && !message.note && <div className="waiting"><span /><span /><span /><span className="waiting-label">Preparing your reply</span></div>}
                  {message.note && <p className="message-note">{message.note}</p>}
                  {message.role === "assistant" && message.text && !busy && !muted && <button className="play-reply text-button" onClick={() => playReply(message.text)}><Icon name="voice" />Play reply</button>}
                </div>
              </article>
            ))}
          </section>
        </div>

        <div className="composer-wrap">
          {error && <div className="error" role="alert">{error}</div>}
          {voiceError && <div className="error voice-error" role="status">{voiceError}<button type="button" className="text-button" onClick={() => setVoiceError("")}>Dismiss</button></div>}
          <form ref={form} className="composer" onSubmit={sendMessage}>
            <label htmlFor="message" className="sr-only">Message Mula</label>
            <textarea ref={input} id="message" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={handleKeyDown} maxLength={8000} rows={1} placeholder="Ask Mula anything…" disabled={busy} />
            <div className="composer-controls">
              <div className="mode-switch" role="group" aria-label="AI response mode">
                <button type="button" aria-pressed={muted} onClick={() => setChatMode(true)}>Chat</button>
                <button type="button" aria-pressed={!muted} onClick={() => setChatMode(false)}>Voice</button>
              </div>
              <button type="button" className="voice-button icon-button" aria-label={voiceLabel} title={voiceLabel} aria-pressed={!muted} onClick={() => setChatMode(!muted)}>
                {muted && <Icon name="muted" />}{!muted && <Icon name="voice" />}
              </button>
              {busy && <button type="button" className="send-button stop-button" aria-label="Stop reply" onClick={() => { controller.current?.abort(); voice.current?.stop(); }}><Icon name="stop" /></button>}
              {!busy && <button type="submit" className="send-button" disabled={!draft.trim()} aria-label="Send message"><Icon name="send" /></button>}
            </div>
          </form>
          <div className="composer-meta"><span>{muted && "Chat mode · AI voice off"}{!muted && "Voice mode · replies read aloud"}</span>
            {voiceState !== "idle" && <button className="text-button" onClick={() => voice.current?.stop()}>Stop audio</button>}
            {voiceState === "idle" && <span className="keyboard-hint">Enter to send · Shift + Enter for a new line</span>}
          </div>
          <p className="scope-note">Planning and guidance for now. Your conversation is saved to your account.</p>
          <span className="sr-only" role="status">{status}</span>
        </div>
      </main>

      <aside className="desk-panel" aria-label="On your desk">
        <div className="desk-heading"><h2>On your desk</h2><span className="desk-count">01</span></div>
        <div className="desk-card">
          <span className="card-icon"><Icon name="home" /></span>
          <span className="card-kicker">YOUR STARTING POINT</span>
          <h3>A little space<br />for your next big idea.</h3>
          <p>Your Operator is ready to help you think, plan, and find a way forward.</p>
          <button className="outline-button" onClick={() => { setDraft(suggestions[0].text); input.current?.focus(); }} disabled={busy}>Find my next step<Icon name="arrow" /></button>
        </div>
        <div className="desk-section-title">A spark to get you started</div>
        <div className="desk-suggestions">{suggestions.slice(1).map((suggestion) => <button key={suggestion.title} onClick={() => { setDraft(suggestion.text); input.current?.focus(); }} disabled={busy}><span>{suggestion.title}</span><Icon name="arrow" /></button>)}</div>
        <div className="desk-footnote"><span className="presence-dot" /><span>One Operator. Always in your corner.</span></div>
      </aside>
    </div>
  );
}
