import { chromium } from "playwright";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SITE = "https://llm-map-mu.vercel.app";

async function main() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    colorScheme: "dark",
  });
  const page = await ctx.newPage();

  // 1. Landing page — wait for scenarios to load
  console.log("1/5 Landing page...");
  await page.goto(SITE, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  await page.screenshot({
    path: join(__dirname, "01-landing.png"),
    fullPage: true,
  });

  // 2. Scenario cards section
  console.log("2/5 Scenario cards...");
  const scenariosSection = page.locator("#scenarios");
  await scenariosSection.scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);
  await scenariosSection.screenshot({
    path: join(__dirname, "02-scenario-select.png"),
  });

  // 3. Click Support Bot scenario
  console.log("3/5 Entering lab...");
  const firstScenario = page
    .locator("button")
    .filter({ hasText: "Support Bot" });
  await firstScenario.click();
  await page.waitForTimeout(1500);

  // 4. Run Simulation
  console.log("4/5 Running simulation...");
  const runBtn = page
    .locator("button")
    .filter({ hasText: "Run Simulation" });
  await runBtn.click();

  // Wait for both simulations to complete (vulnerable + defended)
  // The verdict card appears when done
  await page.waitForSelector("text=Attack Succeeded", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(1000);

  // Screenshot: vulnerable mode result
  await page.screenshot({
    path: join(__dirname, "03-lab-vulnerable.png"),
    fullPage: true,
  });

  // 5. Toggle to Defended mode
  console.log("5/5 Defended mode...");
  const defendedBtn = page
    .locator("button")
    .filter({ hasText: /^Defended$/ })
    .first();
  await defendedBtn.click();
  await page.waitForTimeout(800);

  await page.screenshot({
    path: join(__dirname, "04-lab-defended.png"),
    fullPage: true,
  });

  await browser.close();
  console.log("Done — screenshots saved to docs/assets/");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
