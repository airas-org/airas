import { Progress } from "@/ui";

export function UsagePage() {
  const apiUsed = 1234;
  const apiLimit = 10000;
  const apiPercent = Math.round((apiUsed / apiLimit) * 100);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font mb-8">利用量</h1>

        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-body-bold font-body-bold text-default-font mb-4">API利用状況</h2>
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-caption font-caption text-subtext-color">今月のAPI利用</span>
              <span className="text-caption-bold font-caption-bold text-default-font">
                {apiUsed.toLocaleString()} / {apiLimit.toLocaleString()}
              </span>
            </div>
            <Progress value={apiPercent} />
            <span className="text-caption font-caption text-subtext-color">
              {apiPercent}% 使用済み
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
