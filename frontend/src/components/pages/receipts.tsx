export function ReceiptsPage() {
  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <h1 className="text-2xl font-bold text-foreground">領収書 / 請求書</h1>
      <p className="mt-2 text-sm text-muted-foreground">過去の領収書や請求書を確認できます。</p>
      <div className="mt-8 rounded-lg border border-border p-6 text-center text-sm text-muted-foreground">
        領収書・請求書はまだありません。
      </div>
    </div>
  );
}
