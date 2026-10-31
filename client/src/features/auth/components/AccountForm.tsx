"use client";
import { useState } from "react";
import type { FormEvent } from "react";
import { MulaLogo } from "@/common/components";

export default function AccountForm({ onSignedIn }: { onSignedIn: () => Promise<void> }) {
  const [signup, setSignup] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  let title = "Welcome back";
  let action = "Sign in";
  let toggle = "Create an account";
  let endpoint = "login";
  let autocomplete = "current-password";
  if (signup) {
    title = "Your beginning starts here";
    action = "Create account";
    toggle = "I already have an account";
    endpoint = "signup";
    autocomplete = "new-password";
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/auth/${endpoint}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) {
        const failure = await response.json();
        if (typeof failure.detail === "string") throw new Error(failure.detail);
        throw new Error("Check your username and password and try again.");
      }
      setPassword("");
      await onSignedIn();
    } catch (failure) {
      if (failure instanceof Error) setError(failure.message);
    } finally {
      setBusy(false);
    }
  }
  return <main className="account-screen">
    <form className="account-card" onSubmit={submit}>
      <MulaLogo />
      <h1>{title}</h1>
      <p>Your business, your Operator, one ongoing conversation.</p>
      <label htmlFor="username">Username</label>
      <input id="username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" minLength={3} maxLength={40} pattern="[A-Za-z0-9_.-]{3,40}" required disabled={busy} />
      <small>3–40 letters, numbers, dots, underscores or hyphens.</small>
      <label htmlFor="password">Password</label>
      <input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={autocomplete} minLength={10} maxLength={128} required disabled={busy} />
      <small>At least 10 characters.</small>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="account-submit" disabled={busy}>{action}</button>
      <button className="account-toggle" type="button" disabled={busy} onClick={() => { setSignup(!signup); setError(""); }}>{toggle}</button>
    </form>
  </main>;
}
