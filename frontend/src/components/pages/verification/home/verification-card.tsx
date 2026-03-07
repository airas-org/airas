import * as SubframeCore from "@subframe/core";
import { FeatherCopy, FeatherMoreVertical, FeatherTrash2 } from "@subframe/core";
import { Badge } from "@/ui";
import type { Verification, VerificationPhase } from "../types";

const badgeVariantMap: Record<VerificationPhase, "neutral" | "brand" | "warning" | "success"> = {
  initial: "neutral",
  "methods-proposed": "brand",
  "plan-generated": "brand",
  "code-generating": "brand",
  "code-generated": "warning",
  "experiments-done": "success",
  "paper-writing": "success",
};

const badgeLabelMap: Record<VerificationPhase, string> = {
  initial: "未開始",
  "methods-proposed": "方針提案済み",
  "plan-generated": "計画済み",
  "code-generating": "生成中",
  "code-generated": "実装済み",
  "experiments-done": "実験完了",
  "paper-writing": "情報収集中",
};

interface VerificationCardProps {
  verification: Verification;
  onClick: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

export function VerificationCard({
  verification,
  onClick,
  onDelete,
  onDuplicate,
}: VerificationCardProps) {
  const truncatedQuery =
    verification.query.length > 60 ? `${verification.query.slice(0, 60)}...` : verification.query;

  return (
    <div className="group/card relative rounded-md border border-solid border-neutral-200 bg-card px-2.5 py-2 hover:border-neutral-300 hover:shadow-sm transition-all">
      <button type="button" className="absolute inset-0 cursor-pointer" onClick={onClick} />
      <div className="flex items-center justify-between gap-1">
        <span className="text-[11px] font-semibold text-default-font line-clamp-1">
          {verification.title}
        </span>
        <div className="relative z-10 shrink-0">
          <SubframeCore.DropdownMenu.Root>
            <SubframeCore.DropdownMenu.Trigger asChild>
              <button
                type="button"
                className="flex h-5 w-5 items-center justify-center rounded-md text-white hover:bg-white/10 transition-colors cursor-pointer"
              >
                <FeatherMoreVertical className="h-3 w-3" />
              </button>
            </SubframeCore.DropdownMenu.Trigger>
            <SubframeCore.DropdownMenu.Portal>
              <SubframeCore.DropdownMenu.Content sideOffset={4} align="end">
                <div className="flex min-w-[110px] flex-col rounded-md border border-solid border-neutral-700 bg-neutral-900 px-1 py-1 shadow-lg">
                  <SubframeCore.DropdownMenu.Item asChild>
                    <div
                      className="flex h-6 w-full cursor-pointer items-center gap-1.5 rounded px-2 text-[11px] leading-[16px] text-neutral-200 hover:bg-neutral-800 data-[highlighted]:bg-neutral-800"
                      onSelect={(e: React.BaseSyntheticEvent) => {
                        e.preventDefault();
                        onDuplicate();
                      }}
                    >
                      <FeatherCopy className="h-2.5 w-2.5 text-neutral-400" />
                      <span>Duplicate</span>
                    </div>
                  </SubframeCore.DropdownMenu.Item>
                  <div className="my-0.5 h-px bg-neutral-700" />
                  <SubframeCore.DropdownMenu.Item asChild>
                    <div
                      className="flex h-6 w-full cursor-pointer items-center gap-1.5 rounded px-2 text-[11px] leading-[16px] text-error-400 hover:bg-neutral-800 data-[highlighted]:bg-neutral-800"
                      onSelect={(e: React.BaseSyntheticEvent) => {
                        e.preventDefault();
                        onDelete();
                      }}
                    >
                      <FeatherTrash2 className="h-2.5 w-2.5" />
                      <span>Delete</span>
                    </div>
                  </SubframeCore.DropdownMenu.Item>
                </div>
              </SubframeCore.DropdownMenu.Content>
            </SubframeCore.DropdownMenu.Portal>
          </SubframeCore.DropdownMenu.Root>
        </div>
      </div>
      {truncatedQuery && (
        <p className="text-[10px] leading-[14px] text-neutral-500 mt-0.5 line-clamp-2">
          {truncatedQuery}
        </p>
      )}
      <div className="flex items-center justify-between mt-1.5">
        <span className="text-[10px] leading-[14px] text-neutral-400">
          {verification.createdAt.toLocaleDateString("ja-JP")}
        </span>
        <Badge variant={badgeVariantMap[verification.phase]} className="h-4 text-[9px] px-1.5">
          {badgeLabelMap[verification.phase]}
        </Badge>
      </div>
    </div>
  );
}
