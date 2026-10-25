import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45000,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:8010",
    viewport: { width: 1366, height: 900 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "..\\.venv\\Scripts\\python.exe ..\\scripts\\serve_test_app.py",
    url: "http://127.0.0.1:8010/api/health",
    timeout: 60000,
    reuseExistingServer: false,
  },
});
