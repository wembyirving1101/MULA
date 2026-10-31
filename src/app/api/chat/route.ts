import { proxyBackend } from "@/common/services/server-proxy";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function POST(request: Request) {
  return proxyBackend(request, "/api/agents/operator/chat");
}
