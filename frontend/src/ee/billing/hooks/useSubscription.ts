import axios from "axios";
import { useCallback, useEffect, useState } from "react";

interface Subscription {
  plan: "free" | "pro" | "enterprise";
  status: "active" | "canceled" | "past_due" | "incomplete" | "trialing";
}

export function useSubscription() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSubscription = useCallback(async () => {
    try {
      const res = await axios.get("/airas/ee/billing/subscription");
      setSubscription(res.data);
    } catch {
      setSubscription(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  return { subscription, loading, refetch: fetchSubscription };
}
