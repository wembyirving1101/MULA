export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const backend = process.env.LARAS_BACKEND_URL || "http://127.0.0.1:8000";
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json(
      { detail: "Please send a valid message." },
      { status: 400 },
    );
  }

  try {
    // Relay the stream unchanged. Keep the local backend URL on the server.
    const response = await fetch(
      `${backend.replace(/\/$/, "")}/api/agents/operator/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: request.signal,
        cache: "no-store",
      },
    );
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("Content-Type") || "application/json",
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "Cannot reach LARAS. Start the backend on port 8000 and try again.",
      },
      { status: 503 },
    );
  }
}
