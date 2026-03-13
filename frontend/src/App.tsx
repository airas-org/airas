// frontend/src/App.tsx

import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/app-layout";
import { GitHubOAuthCallbackRoute } from "@/components/pages/integration";
import { isEnterpriseEnabled } from "@/ee/config";
import { useEEComponents } from "@/hooks/use-ee-components";

export default function App() {
  const eeComponents = useEEComponents();

  const appLayout = <AppLayout eeComponents={eeComponents} />;

  const guardedContent = eeComponents ? (
    <eeComponents.AuthGuard>{appLayout}</eeComponents.AuthGuard>
  ) : (
    appLayout
  );

  return (
    <Routes>
      <Route path="/auth/github/callback" element={<GitHubOAuthCallbackRoute />} />
      {isEnterpriseEnabled() && (
        <Route
          path="/auth/callback"
          element={eeComponents ? <eeComponents.AuthCallback /> : <div>Loading...</div>}
        />
      )}
      <Route path="*" element={guardedContent} />
    </Routes>
  );
}
