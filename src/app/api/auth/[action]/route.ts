import { proxyBackend } from "@/common/services/server-proxy";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
type Context = { params: Promise<{ action: string }> };
export async function GET(request: Request, context: Context) {
  const { action } = await context.params;
  if (action !== "me") return new Response(null, { status: 404 });
  return proxyBackend(request, "/api/auth/me");
}
export async function POST(request: Request, context: Context) {
  const { action } = await context.params;
  if (!["signup", "login", "logout"].includes(action)) return new Response(null, { status: 404 });
  return proxyBackend(request, `/api/auth/${action}`);
}
