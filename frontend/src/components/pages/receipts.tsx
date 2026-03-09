export function ReceiptsPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">領収書 / 請求書</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          過去の領収書や請求書を確認できます。
        </p>
        <div className="mt-6 rounded-lg border border-border bg-card p-5 text-center text-body font-body text-subtext-color">
          領収書・請求書はまだありません。
        </div>
      </div>
    </div>
  );
}
