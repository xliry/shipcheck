import Stripe from "stripe";

export async function POST(req: Request) {
  const event = await req.json();
  if (event.type === "customer.subscription.updated") {
    return Response.json({ active: true });
  }
  return Response.json({ received: true });
}
