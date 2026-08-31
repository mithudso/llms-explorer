import { defineConfig } from "astro/config";
export default defineConfig({
  site: process.env.SITE_URL || "https://llms-explorer.com",
  trailingSlash: "always",
  build: { format: "directory" },
});
