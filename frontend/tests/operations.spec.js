import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";

test.describe.configure({ mode: "default" });
const screenshots = path.resolve(process.env.LEADREVIVE_CAPTURE_BASELINE === "1" ? "../screenshots" : "test-results/evidence");
async function ready(page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "A clearer view. A stronger follow-up.",
    }),
  ).toBeVisible();
  await expect(page.locator(".kpi-grid")).toBeVisible();
}
async function noSeriousA11y(page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(
    results.violations.map((v) => ({
      id: v.id,
      description: v.description,
      nodes: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
}

test("overview reconciles to API, cohort filters work, desktop capture", async ({
  page,
  request,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await ready(page);
  const metrics = await (await request.get("/api/analytics/kpis")).json();
  await expect(
    page.locator(".kpi-card").nth(0).locator(".kpi-value"),
  ).toHaveText(String(metrics.new_leads));
  await expect(
    page.locator(".kpi-card").nth(2).locator(".kpi-value"),
  ).toHaveText(String(metrics.overdue));
  await page.screenshot({
    path: path.join(screenshots, "SS01_Overview.png"),
    fullPage: true,
  });
  await noSeriousA11y(page);
  await page.getByLabel("Overview source", { exact: true }).selectOption("Web");
  const web = await (
    await request.get("/api/analytics/kpis?source=Web")
  ).json();
  await expect(
    page.locator(".kpi-card").first().locator(".kpi-value"),
  ).toHaveText(String(web.new_leads));
  await page.getByLabel("Creation cohort", { exact: true }).selectOption("30");
  await expect(page.locator(".kpi-grid")).toBeVisible();
  expect(errors).toEqual([]);
});

test("queue filters, sorting, paging, empty state and export work", async ({
  page,
  request,
}) => {
  await ready(page);
  await page
    .getByRole("button", { name: "Recovery queue", exact: true })
    .click();
  await expect(page.locator("tbody tr")).toHaveCount(12);
  await page
    .getByLabel("Filter by follow-up", { exact: true })
    .selectOption("overdue");
  const overdue = await (
    await request.get("/api/leads?followup=overdue")
  ).json();
  await expect(page.locator(".pagination")).toContainText(
    `${overdue.total} matching leads`,
  );
  await page
    .getByLabel("Filter by owner", { exact: true })
    .selectOption("REP-1");
  await expect(page.locator("tbody tr").first()).toContainText(
    "Fictional Rep 1",
  );
  await page.getByLabel("Sort leads", { exact: true }).selectOption("value");
  await page.screenshot({
    path: path.join(screenshots, "SS02_Recovery_Queue.png"),
    fullPage: true,
  });
  await noSeriousA11y(page);
  await page.getByRole("button", { name: "Next page", exact: true }).click();
  await expect(page.locator(".pagination")).toContainText("Page 2");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export all leads" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("leads_SYNTHETIC.csv");
  await page
    .getByLabel("Search leads", { exact: true })
    .fill("zzzz-no-matches");
  await expect(
    page.getByRole("heading", { name: "No leads match these filters" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reset filters" }).click();
  await expect(page.locator("tbody tr")).toHaveCount(12);
});

test("create, assign, schedule, change stage, record contact and reload timeline", async ({
  page,
  request,
}) => {
  await ready(page);
  await page
    .getByRole("button", { name: "Recovery queue", exact: true })
    .click();
  await page.getByRole("button", { name: "New synthetic lead" }).click();
  await page
    .getByLabel("Contact name", { exact: true })
    .fill("Fictional Browser Contact");
  await page
    .getByLabel("Company", { exact: true })
    .fill("Synthetic Browser Business");
  await page
    .getByLabel("Email", { exact: true })
    .fill("browser@business.example");
  await page
    .getByLabel("Fictional phone", { exact: true })
    .fill("FICTIONAL-IN-BROWSER-001");
  await page
    .getByLabel("Estimated deal value · INR", { exact: true })
    .fill("125000");
  await page.getByRole("button", { name: "Create lead", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Synthetic Browser Business",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByLabel("Assigned owner", { exact: true })
    .selectOption("REP-2");
  await page
    .getByLabel("Sales stage", { exact: true })
    .selectOption("Qualified");
  await page
    .getByLabel("Next action · Asia/Kolkata", { exact: true })
    .fill("2026-10-25T11:00");
  await page
    .getByRole("button", { name: "Save lead changes", exact: true })
    .click();
  await expect(page.locator(".toast")).toContainText("Lead changes saved");
  await expect(page.getByLabel("Assigned owner", { exact: true })).toHaveValue(
    "REP-2",
  );
  await page
    .getByLabel("Activity note", { exact: true })
    .fill(
      "Synthetic follow-up completed. Confirm requirements in the next meeting.",
    );
  await page
    .getByRole("button", { name: "Record activity", exact: true })
    .click();
  await expect(page.locator(".timeline")).toContainText(
    "Synthetic follow-up completed",
  );
  await page
    .getByRole("button", { name: "Audit history", exact: true })
    .click();
  await expect(page.locator(".timeline")).toContainText("before");
  await expect(page.locator(".toast")).toBeHidden({ timeout: 8000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: path.join(screenshots, "SS03_Lead_Timeline.png"),
    fullPage: true,
  });
  await noSeriousA11y(page);
  const list = await (
    await request.get("/api/leads?q=Synthetic%20Browser%20Business")
  ).json();
  expect(list.items[0].owner_id).toBe("REP-2");
  expect(list.items[0].stage).toBe("Qualified");
  expect(list.items[0].next_action_at).toBe("2026-10-25T05:30:00.000000Z");
  await page.reload();
  await page
    .getByRole("button", { name: "Recovery queue", exact: true })
    .click();
  await page
    .getByLabel("Search leads", { exact: true })
    .fill("Synthetic Browser Business");
  await page
    .getByRole("button", { name: "Synthetic Browser Business", exact: true })
    .click();
  await expect(page.getByLabel("Assigned owner", { exact: true })).toHaveValue(
    "REP-2",
  );
  await expect(page.locator(".timeline")).toContainText(
    "Synthetic follow-up completed",
  );
});

test("CSV replay, conflict comparison, review and export preserve original leads", async ({
  page,
  request,
}) => {
  await ready(page);
  await page.getByRole("button", { name: "Data quality", exact: true }).click();
  await page
    .getByLabel("Choose synthetic CSV", { exact: true })
    .setInputFiles(path.resolve("../data/synthetic/leads_SYNTHETIC.csv"));
  await page.getByRole("button", { name: "Import CSV", exact: true }).click();
  await expect(page.locator(".import-result")).toContainText(
    "Existing import recognized",
  );
  await page
    .locator(".exception-item")
    .filter({ hasText: "identity collision" })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Existing candidate records" }),
  ).toBeVisible();
  const before = await (await request.get("/api/leads/export")).text();
  await page
    .getByLabel("Decision note", { exact: true })
    .fill(
      "Conflicting fictional identity; keep the existing lead and its history.",
    );
  await page
    .getByRole("button", {
      name: "Keep existing · record decision",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision recorded" }),
  ).toBeVisible();
  expect(await (await request.get("/api/leads/export")).text()).toBe(before);
  await expect(page.locator(".toast")).toBeHidden({ timeout: 8000 });
  await page.locator(".exception-item.selected").scrollIntoViewIfNeeded();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: path.join(screenshots, "SS04_Data_Quality.png"),
    fullPage: true,
  });
  await noSeriousA11y(page);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export exceptions" }).click();
  expect((await downloadPromise).suggestedFilename()).toBe(
    "exceptions_SYNTHETIC.csv",
  );
});

test("settings validate totals, persist rules and keep email disabled", async ({
  page,
  request,
}) => {
  await ready(page);
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page
    .getByLabel("First-response SLA · elapsed hours", { exact: true })
    .fill("12");
  await page.getByLabel("overdue", { exact: true }).fill("40");
  await expect(
    page.getByRole("button", { name: "Save workspace rules" }),
  ).toBeDisabled();
  await page.getByLabel("value", { exact: true }).fill("20");
  await page.getByRole("button", { name: "Save workspace rules" }).click();
  await expect(page.locator(".toast")).toContainText("Workspace rules updated");
  await page.reload();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(
    page.getByLabel("First-response SLA · elapsed hours", { exact: true }),
  ).toHaveValue("12");
  await expect(page.locator(".safety-panel")).toContainText("Disabled");
  const settings = await (await request.get("/api/settings")).json();
  expect(settings.live_email_enabled).toBe(false);
  await page.getByRole("button", { name: "Show latest", exact: true }).click();
  await expect(page.locator(".audit-entries")).toContainText(
    "settings updated",
  );
  await noSeriousA11y(page);
});

test("mobile overview and queue fit viewport with usable navigation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await ready(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: path.join(screenshots, "SS02a_Mobile_Overview.png"),
    fullPage: true,
  });
  await noSeriousA11y(page);
  await page
    .getByRole("button", { name: "Recovery queue", exact: true })
    .click();
  await expect(page.getByLabel("Search leads", { exact: true })).toBeVisible();
  await page
    .getByLabel("Search leads", { exact: true })
    .fill("Synthetic Browser Business");
  await page
    .getByRole("button", { name: "Synthetic Browser Business", exact: true })
    .click();
  await expect(
    page.getByLabel("Assigned owner", { exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("backend failure is visible and retry restores the workspace", async ({
  page,
}) => {
  await page.route("**/api/overview*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Database temporarily unavailable for browser error-path test",
      }),
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText(
    "Database temporarily unavailable",
  );
  await page.unroute("**/api/overview*");
  await page.reload();
  await expect(page.locator(".kpi-grid")).toBeVisible();
});
