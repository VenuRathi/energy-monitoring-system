export const APP_META = {
  systemName: "Industrial Energy Monitoring System",
  productName: "Plant Energy Monitor",
  version: import.meta.env.VITE_APP_VERSION || "Pilot v0.1.0",
  deploymentMode: "Plant pilot build",
} as const;
