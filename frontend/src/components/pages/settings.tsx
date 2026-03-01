export function SettingsPage() {
  return (
    <div className="flex-1 p-8">
      <h1 className="text-2xl font-bold text-foreground">Settings</h1>
      <div className="mt-6 space-y-6">
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-lg font-semibold text-foreground">GitHub Integration</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Connect your GitHub account to enable repository access and collaboration features.
          </p>
          <div className="mt-4">
            <span className="inline-block rounded-md bg-muted px-3 py-1 text-xs text-muted-foreground">
              Coming soon
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
