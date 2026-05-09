import { requireAuth } from "../../../lib/auth";

export async function POST(req: Request) {
  await rateLimit(req);
  const session = await requireAuth();
  if (session.user.role !== "admin") return new Response("forbidden", { status: 403 });
  return Response.json({ ok: true });
}

async function rateLimit(_req: Request) {
  return true;
}
