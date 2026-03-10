import { FeatherBrain, FeatherFileText, FeatherGithub, FeatherLightbulb } from "@subframe/core";
import { useState } from "react";
import { LoadingSpinner } from "@/ee/auth/components/LoadingSpinner";
import { useAuth } from "@/ee/auth/hooks/useAuth";

type SignInProvider = "google" | "github" | null;

export function LoginPage() {
  const { signInWithGoogle, signInWithGitHub } = useAuth();
  const [loadingProvider, setLoadingProvider] = useState<SignInProvider>(null);

  const handleSignIn = async (provider: "google" | "github") => {
    setLoadingProvider(provider);
    try {
      if (provider === "google") {
        await signInWithGoogle();
      } else {
        await signInWithGitHub();
      }
    } catch {
      setLoadingProvider(null);
    }
  };

  return (
    <div className="flex min-h-screen w-full bg-neutral-900 items-stretch relative">
      <div className="flex flex-col items-center justify-center gap-8 px-12 py-12 grow shrink-0 z-10 mobile:hidden">
        <div className="flex w-full max-w-[448px] flex-col items-start gap-8">
          <div className="flex w-full flex-col items-start gap-4">
            <span className="w-full font-['Inter'] text-[48px] font-[700] leading-[52px] text-[#3f5cd9] -tracking-[0.035em]">
              Accelerate Your Research with AI
            </span>
            <span className="w-full font-['Inter'] text-[18px] font-[400] leading-[28px] text-[#fcfcfc] -tracking-[0.01em]">
              You can validate hypotheses and discover new insights faster than ever before.
            </span>
          </div>
          <div className="flex w-full flex-col items-start gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg">
                <FeatherBrain className="font-['Inter'] text-[32px] font-[400] leading-[48px] text-[#ffffff]" />
              </div>
              <span className="text-body-bold font-body-bold text-[#ffffff] -tracking-[0.01em]">
                AI-Powered Research Automation
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg">
                <FeatherFileText className="font-['Inter'] text-[32px] font-[400] leading-[48px] text-[#ffffff]" />
              </div>
              <span className="text-body-bold font-body-bold text-[#ffffff] -tracking-[0.01em]">
                Automatically validate hypotheses
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg">
                <FeatherLightbulb className="font-['Inter'] text-[32px] font-[400] leading-[48px] text-[#ffffff]" />
              </div>
              <span className="text-body-bold font-body-bold text-[#ffffff] -tracking-[0.01em]">
                Accelerate new discoveries
              </span>
            </div>
          </div>
        </div>
      </div>
      <img
        className="min-w-[0px] grow shrink-0 basis-0 self-stretch object-cover absolute inset-0"
        src="https://res.cloudinary.com/subframe/image/upload/v1772900120/uploads/36719/yb3axrb8m1vpjhrhrppn.png"
        alt=""
      />
      <div className="flex items-start absolute inset-0 bg-gradient-to-br from-neutral-900/60 to-neutral-900/60" />
      <div className="flex max-w-[576px] flex-col items-center justify-center gap-6 bg-neutral-950 px-8 py-12 w-[40%] z-10">
        <div className="flex w-full max-w-[384px] flex-col items-center gap-8 rounded-2xl border border-solid border-neutral-800 px-10 py-10 bg-neutral-900/50 backdrop-blur-sm">
          <div className="flex w-full flex-col items-center gap-4">
            <img className="h-14 flex-none object-contain" src="/airas_logo.png" alt="AIRAS" />
            <div className="flex w-full flex-col items-center gap-2">
              <span className="w-full font-['Inter'] text-[24px] font-[700] leading-[32px] text-white text-center -tracking-[0.02em]">
                Sign in to AIRAS
              </span>
              <span className="w-full text-body font-body text-neutral-400 text-center -tracking-[0.01em]">
                AI-powered Research Assistant
              </span>
            </div>
          </div>
          <div className="flex w-full flex-col items-center gap-3">
            <button
              type="button"
              onClick={() => handleSignIn("google")}
              disabled={loadingProvider !== null}
              className="flex w-full items-center justify-center gap-3 rounded-lg border border-solid border-neutral-700 bg-white px-4 py-3 cursor-pointer hover:bg-neutral-100 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {loadingProvider === "google" ? (
                <LoadingSpinner className="h-5 w-5 text-neutral-600" />
              ) : (
                <svg className="h-5 w-5" viewBox="0 0 24 24" role="img" aria-label="Google">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
              )}
              <span className="text-body-bold font-body-bold text-neutral-800 -tracking-[0.01em]">
                {loadingProvider === "google" ? "Signing in..." : "Sign in with Google"}
              </span>
            </button>
            <button
              type="button"
              onClick={() => handleSignIn("github")}
              disabled={loadingProvider !== null}
              className="flex w-full items-center justify-center gap-3 rounded-lg border border-solid border-neutral-700 bg-neutral-800 px-4 py-3 cursor-pointer hover:bg-neutral-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {loadingProvider === "github" ? (
                <LoadingSpinner className="h-5 w-5 text-white" />
              ) : (
                <FeatherGithub className="text-body font-body text-white" />
              )}
              <span className="text-body-bold font-body-bold text-white -tracking-[0.01em]">
                {loadingProvider === "github" ? "Signing in..." : "Sign in with GitHub"}
              </span>
            </button>
          </div>
          <div className="flex w-full flex-col items-center gap-2">
            <span className="text-[10px] leading-[14px] text-neutral-500 text-center -tracking-[0.01em]">
              By signing in, you agree to our Terms of Service and Privacy Policy.
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] leading-[14px] text-neutral-600 -tracking-[0.01em]">
            &copy; 2026 AIRAS
          </span>
          <span className="text-[10px] leading-[14px] text-neutral-600 -tracking-[0.01em]">
            &bull;
          </span>
          <span className="text-[10px] leading-[14px] text-neutral-500 -tracking-[0.01em]">
            Privacy
          </span>
          <span className="text-[10px] leading-[14px] text-neutral-600 -tracking-[0.01em]">
            &bull;
          </span>
          <span className="text-[10px] leading-[14px] text-neutral-500 -tracking-[0.01em]">
            Terms
          </span>
        </div>
      </div>
    </div>
  );
}
