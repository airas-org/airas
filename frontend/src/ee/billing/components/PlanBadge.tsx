import { cn } from "@/lib/utils";

interface PlanBadgeProps {
  plan: "free" | "pro" | "enterprise";
}

export function PlanBadge({ plan }: PlanBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        plan === "pro" && "bg-blue-100 text-blue-800",
        plan === "enterprise" && "bg-purple-100 text-purple-800",
        plan === "free" && "bg-gray-100 text-gray-800",
      )}
    >
      {plan.charAt(0).toUpperCase() + plan.slice(1)}
    </span>
  );
}
