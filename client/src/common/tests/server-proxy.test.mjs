import assert from "node:assert/strict";
import test from "node:test";
import { proxyBackend } from "../services/server-proxy.ts";

test("auth proxy forwards a private session cookie and login cookie", async (context) => {
  const fetch = context.mock.method(globalThis, "fetch", async (url, options) => {
    assert.ok(url.endsWith("/api/auth/login"));
    assert.equal(options.headers.Cookie, "mula_session=old-session");
    assert.equal(options.cache, "no-store");
    return Response.json({ username: "owner" }, { headers: {
      "Set-Cookie": "mula_session=new-session; Path=/; HttpOnly; SameSite=Strict",
    } });
  });
  const response = await proxyBackend(new Request("http://localhost:3000/api/auth/login", {
    method: "POST", headers: { host: "localhost:3000", origin: "http://localhost:3000", cookie: "mula_session=old-session" }, body: "{}",
  }), "/api/auth/login");
  assert.equal(response.status, 200);
  assert.match(response.headers.get("set-cookie"), /HttpOnly/);
  assert.match(response.headers.get("cache-control"), /no-store/);
  assert.equal(fetch.mock.callCount(), 1);
});

test("cross-origin account changes are rejected before forwarding", async (context) => {
  const fetch = context.mock.method(globalThis, "fetch", () => { throw new Error("Should not run"); });
  const response = await proxyBackend(new Request("http://localhost:3000/api/auth/logout", {
    method: "POST", headers: { host: "localhost:3000", origin: "https://another-site.example" },
  }), "/api/auth/logout");
  assert.equal(response.status, 403);
  assert.equal(fetch.mock.callCount(), 0);
});

test("speech proxy preserves audio bytes, authentication and no-store", async (context) => {
  context.mock.method(globalThis, "fetch", async (url, options) => {
    assert.ok(url.endsWith("/api/speech"));
    assert.equal(options.headers.Cookie, "mula_session=test");
    return new Response(new Uint8Array([82, 73, 70, 70]), { headers: { "content-type": "audio/wav" } });
  });
  const response = await proxyBackend(new Request("http://localhost:3000/api/speech", {
    method: "POST", headers: { host: "localhost:3000", origin: "http://localhost:3000", cookie: "mula_session=test" }, body: JSON.stringify({ text: "Hello" }),
  }), "/api/speech");
  assert.equal(response.headers.get("content-type"), "audio/wav");
  assert.match(response.headers.get("cache-control"), /no-store/);
  assert.equal(await response.text(), "RIFF");
});
