import axios from "axios";

export function BillingPortal() {
  const handlePortal = async () => {
    const res = await axios.post("/airas/ee/billing/create-portal-session", {
      return_url: window.location.origin,
    });
    window.location.href = res.data.url;
  };

  return (
    <button
      type="button"
      onClick={handlePortal}
      className="rounded-md border border-border px-4 py-2 text-sm text-foreground hover:bg-muted/60 transition-colors"
    >
      Manage subscription
    </button>
  );
}
