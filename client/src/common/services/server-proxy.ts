// Proxy only known application endpoints; credentials stay in HttpOnly cookies.
export async function proxyBackend(request: Request, path: string) {
  if (request.method !== "GET") {
    const origin = request.headers.get("origin");
    if (origin) {
      try {
        if (new URL(origin).host !== request.headers.get("host")) {
          return Response.json({ detail: "Request origin is not allowed." }, { status: 403 });
        }
      } catch {
        return Response.json({ detail: "Request origin is not allowed." }, { status: 403 });
      }
    }
  }
  const backend = process.env.LARAS_BACKEND_URL || "http://127.0.0.1:8000";
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Cookie: request.headers.get("cookie") || "",
  };
  const options: RequestInit = {
    method: request.method, headers, cache: "no-store", signal: request.signal,
  };
  if (request.method !== "GET") options.body = await request.text();
  try {
    const response = await fetch(`${backend.replace(/\/$/, "")}${path}`, options);
    const forwarded = new Headers({
      "Content-Type": response.headers.get("content-type") || "application/json",
      "Cache-Control": "no-store, no-transform", "X-Accel-Buffering": "no",
    });
    for (const cookie of response.headers.getSetCookie()) forwarded.append("Set-Cookie", cookie);
    return new Response(response.body, { status: response.status, headers: forwarded });
  } catch {
    return Response.json({ detail: "Cannot reach LARAS. Start the backend on port 8000 and try again." }, { status: 503 });
  }
}
