import process from "node:process";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";

import { Builder, By, until } from "selenium-webdriver";
import edge from "selenium-webdriver/edge.js";

const require = createRequire(import.meta.url);
const axeSourcePath = require.resolve("axe-core/axe.min.js");
const axeSource = await readFile(axeSourcePath, "utf8");

const baseUrl = (process.env.AXE_BASE_URL || "http://127.0.0.1:8766").replace(/\/$/, "");
const username = process.env.AXE_TEST_USERNAME || "";
const password = process.env.AXE_TEST_PASSWORD || "";
const routes = [
  { name: "Ingreso", path: "/login/", authenticated: false },
  { name: "Administración", path: "/admin/login/", authenticated: false },
  { name: "Panel de Sostenibilidad", path: "/dashboard/", authenticated: true },
  { name: "Talleres", path: "/profesor/", authenticated: true },
  { name: "Código QR", path: "/codigo-qr/", authenticated: true },
];

const options = new edge.Options();
options.addArguments(
  "--headless=new",
  "--disable-gpu",
  "--no-sandbox",
  "--window-size=1440,1000",
  "--force-device-scale-factor=1"
);

const driver = await new Builder()
  .forBrowser("MicrosoftEdge")
  .setEdgeOptions(options)
  .build();

let failures = 0;

async function audit(name, url) {
  await driver.get(url);
  await driver.wait(
    () => driver.executeScript("return document.readyState === 'complete'"),
    15000
  );
  await driver.executeScript(axeSource);
  const result = await driver.executeAsyncScript(`
    const done = arguments[arguments.length - 1];
    axe.run(document, {
      resultTypes: ["violations", "incomplete"],
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] }
    }).then(done).catch(error => done({ __error: String(error) }));
  `);

  if (result.__error) {
    throw new Error(result.__error);
  }

  const blocking = result.violations.filter((item) =>
    item.impact === "critical" || item.impact === "serious"
  );
  failures += blocking.length;

  console.log(`\n${name}: ${result.violations.length} infracción(es), ${result.incomplete.length} revisión(es) manual(es).`);
  for (const violation of blocking) {
    console.error(`- [${violation.impact}] ${violation.id}: ${violation.help}`);
    for (const node of violation.nodes.slice(0, 5)) {
      console.error(`  ${node.target.join(" ")}`);
      const selector = node.target[0];
      const styles = await driver.executeScript(`
        const element = document.querySelector(arguments[0]);
        if (!element) return null;
        const style = getComputedStyle(element);
        let parent = element;
        let background = "rgba(0, 0, 0, 0)";
        while (parent && background === "rgba(0, 0, 0, 0)") {
          background = getComputedStyle(parent).backgroundColor;
          parent = parent.parentElement;
        }
        return { color: style.color, background };
      `, selector);
      if (styles) console.error(`    color=${styles.color}; fondo=${styles.background}`);
    }
  }
}

try {
  for (const route of routes.filter((item) => !item.authenticated)) {
    await audit(route.name, baseUrl + route.path);
  }

  if (!username || !password) {
    console.warn("\nRutas autenticadas omitidas: defina AXE_TEST_USERNAME y AXE_TEST_PASSWORD.");
  } else {
    await driver.get(baseUrl + "/login/");
    await driver.findElement(By.id("username")).sendKeys(username);
    await driver.findElement(By.id("password")).sendKeys(password);
    await driver.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.urlContains("/dashboard/"), 15000);

    for (const route of routes.filter((item) => item.authenticated)) {
      await audit(route.name, baseUrl + route.path);
    }
  }
} finally {
  await driver.quit();
}

if (failures > 0) {
  console.error(`\naxe-core detectó ${failures} problema(s) critical/serious.`);
  process.exitCode = 1;
} else {
  console.log("\naxe-core: cero problemas critical/serious en las rutas auditadas.");
}
