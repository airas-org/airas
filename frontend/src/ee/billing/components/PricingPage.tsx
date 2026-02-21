import axios from "axios";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: ["Basic research", "Community support"],
    priceId: null,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    features: ["Unlimited research", "Priority support", "Advanced analytics"],
    priceId: "price_pro_monthly",
  },
];

export function PricingPage() {
  const handleCheckout = async (priceId: string) => {
    const res = await axios.post("/airas/ee/billing/create-checkout-session", {
      price_id: priceId,
      success_url: `${window.location.origin}/?checkout=success`,
      cancel_url: `${window.location.origin}/?checkout=canceled`,
    });
    window.location.href = res.data.url;
  };

  return (
    <div className="mx-auto max-w-3xl p-8">
      <h2 className="text-2xl font-bold text-foreground mb-8 text-center">Choose your plan</h2>
      <div className="grid grid-cols-2 gap-6">
        {plans.map((plan) => (
          <div key={plan.name} className="rounded-lg border border-border bg-card p-6 space-y-4">
            <h3 className="text-lg font-semibold">{plan.name}</h3>
            <div className="text-3xl font-bold">
              {plan.price}
              <span className="text-sm font-normal text-muted-foreground">{plan.period}</span>
            </div>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {plan.features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            {plan.priceId && (
              <button
                type="button"
                onClick={() => handleCheckout(plan.priceId as string)}
                className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Subscribe
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
