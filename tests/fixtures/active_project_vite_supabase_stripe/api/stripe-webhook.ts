import Stripe from "stripe";

export default async function handler(req, res) {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  const signature = req.headers["stripe-signature"];
  const event = stripe.webhooks.constructEvent(req.body, signature, process.env.STRIPE_WEBHOOK_SECRET);

  if (event.type === "checkout.session.completed") {
    const stripe_payment_id = event.data.object.payment_intent;
    const existing = await supabase.from("payments").select("id").eq("stripe_payment_id", stripe_payment_id).single();
    if (!existing.data) {
      await supabase.from("payments").insert({ stripe_payment_id });
    }
  }

  res.status(200).json({ received: true });
}
