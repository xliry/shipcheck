export const tiers = [
  { name: "Starter", stripePriceId: "price_1234567890abcdef" },
  { name: "Studio", stripePriceId: "price_abcdef1234567890" },
];

export function Pricing() {
  return <main>{tiers.map((tier) => <button key={tier.stripePriceId}>{tier.name}</button>)}</main>;
}
