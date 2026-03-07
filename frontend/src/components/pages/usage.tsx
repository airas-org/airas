export function UsagePage() {
  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <h1 className="text-2xl font-bold text-foreground">利用量</h1>
      <p className="mt-2 text-sm text-muted-foreground">現在の利用状況を確認できます。</p>
      <div className="mt-8 rounded-lg border border-border p-6 text-center text-sm text-muted-foreground">
        利用量データはまだありません。
      </div>
    </div>
  );
}
