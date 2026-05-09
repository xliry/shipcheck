import Stripe from "stripe";

export async function POST(req: Request) {
  await rateLimit(req);
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
  const signature = req.headers.get("stripe-signature")!;
  const event = stripe.webhooks.constructEvent(await req.text(), signature, process.env.STRIPE_WEBHOOK_SECRET!);
  if (event.type === "checkout.session.completed") {
    const idempotencyKey = event.id;
    console.error("processed", idempotencyKey);
  }
  return Response.json({ received: true });
}

async function rateLimit(_req: Request) {
  return true;
}
