export const isSelfHosted = (): boolean => import.meta.env.VITE_SELF_HOSTED === "true";
