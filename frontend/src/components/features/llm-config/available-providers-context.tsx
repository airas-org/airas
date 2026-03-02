import { createContext, useContext } from "react";

/**
 * Providers for which the user has API keys configured.
 * null = not loaded yet (show all models), empty array = none configured.
 */
const AvailableProvidersContext = createContext<string[] | null>(null);

export const AvailableProvidersProvider = AvailableProvidersContext.Provider;

export function useAvailableProviders(): string[] | null {
  return useContext(AvailableProvidersContext);
}
