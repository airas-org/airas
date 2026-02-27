export const isEnterpriseEnabled = (): boolean =>
  import.meta.env.VITE_ENTERPRISE_ENABLED !== "false";
