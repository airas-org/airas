import { createContext, type ReactNode, useContext } from "react";
import type { ProposedMethod, Verification } from "@/components/pages/verification";

interface VerificationContextType {
  verifications: Verification[];
  onDeleteVerification: (id: string) => void;
  onDuplicateVerification: (id: string) => void;
  onUpdateVerification: (id: string, updates: Partial<Verification>) => void;
  onCreateWithQuery: (query: string) => void;
  onCreateWithMethod: (sourceVerification: Verification, method: ProposedMethod) => void;
}

const VerificationContext = createContext<VerificationContextType | null>(null);

export function VerificationProvider({
  children,
  value,
}: {
  children: ReactNode;
  value: VerificationContextType;
}) {
  return <VerificationContext.Provider value={value}>{children}</VerificationContext.Provider>;
}

export function useVerificationContext() {
  const ctx = useContext(VerificationContext);
  if (!ctx) {
    throw new Error("useVerificationContext must be used within VerificationProvider");
  }
  return ctx;
}
