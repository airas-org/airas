import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/app-layout";
import { GitHubOAuthCallbackRoute } from "@/components/pages/integration";
import { AuthGuard } from "@/ee/auth/components/AuthGuard";
import { isEnterpriseEnabled } from "@/ee/config";
import { useEE } from "@/hooks/use-ee-components";

export default function App() {
  const ee = useEE();
  const enterprise = isEnterpriseEnabled();

  if (ee.loading) return null;

  const appLayout = <AppLayout ee={ee} />;

  return (
    <Routes>
      <Route path="/auth/github/callback" element={<GitHubOAuthCallbackRoute />} />

      {ee.components && (
        <>
          <Route path="/auth/callback" element={<ee.components.AuthCallback />} />
          <Route path="/login" element={<ee.components.LoginPage />} />
        </>
      )}

      <Route path="*" element={enterprise ? <AuthGuard>{appLayout}</AuthGuard> : appLayout} />
    </Routes>
  );
}
