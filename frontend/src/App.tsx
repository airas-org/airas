import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/app-layout";
import { GitHubOAuthCallbackRoute } from "@/components/pages/integration";
import { AuthGuard } from "@/ee/auth/components/AuthGuard";
import { isSelfHosted } from "@/ee/config";
import { useEE } from "@/hooks/use-ee-components";

export default function App() {
  const ee = useEE();
  const selfHosted = isSelfHosted();

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

      <Route path="*" element={selfHosted ? appLayout : <AuthGuard>{appLayout}</AuthGuard>} />
    </Routes>
  );
}
