import process from "node:process";

import { Builder, By, Key, until } from "selenium-webdriver";
import edge from "selenium-webdriver/edge.js";

const baseUrl = (process.env.AXE_BASE_URL || "http://127.0.0.1:8766").replace(/\/$/, "");
const username = process.env.AXE_TEST_USERNAME || "";
const password = process.env.AXE_TEST_PASSWORD || "";

if (!username || !password) {
  throw new Error("Defina AXE_TEST_USERNAME y AXE_TEST_PASSWORD para la prueba funcional.");
}

const options = new edge.Options();
options.addArguments(
  "--headless=new",
  "--disable-gpu",
  "--no-sandbox",
  "--window-size=1440,1000"
);

const driver = await new Builder()
  .forBrowser("MicrosoftEdge")
  .setEdgeOptions(options)
  .build();

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function activeElementDescription() {
  return driver.executeScript(`
    const element = document.activeElement;
    return {
      tag: element?.tagName || "",
      id: element?.id || "",
      className: String(element?.className || ""),
      text: String(element?.textContent || "").trim()
    };
  `);
}

try {
  await driver.get(baseUrl + "/login/");
  await driver.wait(
    () => driver.executeScript("return document.readyState === 'complete'"),
    15000
  );

  await driver.actions().sendKeys(Key.TAB).perform();
  let active = await activeElementDescription();
  assert(active.className.includes("skip-link"), "El primer Tab no enfocó el enlace de salto.");

  await driver.actions().sendKeys(Key.ENTER).perform();
  assert((await driver.getCurrentUrl()).includes("#main-content"), "El enlace de salto no llevó al main.");

  const launcher = await driver.findElement(By.id("a11y-launcher"));
  await launcher.sendKeys(Key.ENTER);
  await driver.wait(async () => (await launcher.getAttribute("aria-expanded")) === "true", 3000);
  active = await activeElementDescription();
  assert(active.className.includes("a11y-close"), "Al abrir no se movió el foco al panel.");

  await driver.actions().sendKeys(Key.ESCAPE).perform();
  await driver.wait(async () => (await launcher.getAttribute("aria-expanded")) === "false", 3000);
  active = await activeElementDescription();
  assert(active.id === "a11y-launcher", "Escape no devolvió el foco al botón.");

  await launcher.sendKeys(Key.SPACE);
  await driver.wait(async () => (await launcher.getAttribute("aria-expanded")) === "true", 3000);

  const scale = await driver.findElement(By.id("a11y-text-scale"));
  await scale.sendKeys(Key.END);
  const contrast = await driver.findElement(By.css('[data-a11y-toggle="contrast"]'));
  const grayscale = await driver.findElement(By.css('[data-a11y-toggle="grayscale"]'));
  const readableFont = await driver.findElement(By.css('[data-a11y-toggle="readableFont"]'));
  const highlightLinks = await driver.findElement(By.css('[data-a11y-toggle="highlightLinks"]'));
  const readingGuide = await driver.findElement(By.css('[data-a11y-toggle="readingGuide"]'));
  const reduceMotion = await driver.findElement(By.css('[data-a11y-toggle="reduceMotion"]'));
  await driver.executeScript("arguments[0].focus();", contrast);
  await driver.actions().sendKeys(Key.SPACE).perform();
  for (const control of [grayscale, readableFont, highlightLinks, readingGuide, reduceMotion]) {
    await driver.executeScript("arguments[0].click();", control);
  }

  const theme = await driver.findElement(By.id("a11y-theme"));
  await driver.executeScript(`
    const select = arguments[0];
    select.value = "dark";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  `, theme);

  let stored = await driver.executeScript("return localStorage.getItem('site.a11y.v1');");
  assert(stored, "Las preferencias no se guardaron.");
  let parsed = JSON.parse(stored);
  assert(parsed.textScale === 200, "El tamaño 200 % no se persistió.");
  assert(parsed.theme === "dark", "El tema oscuro no se persistió.");
  assert(
    parsed.contrast && parsed.grayscale && parsed.reduceMotion,
    "La combinación de opciones no se persistió: " + JSON.stringify(parsed)
  );

  await driver.navigate().refresh();
  await driver.wait(until.elementLocated(By.id("a11y-launcher")), 10000);
  const rootClasses = await driver.executeScript("return document.documentElement.className;");
  assert(rootClasses.includes("a11y-text-200"), "El tamaño no sobrevivió a la recarga.");
  assert(rootClasses.includes("a11y-contrast"), "El alto contraste no sobrevivió a la recarga.");

  const usernameInput = await driver.findElement(By.id("username"));
  const passwordInput = await driver.findElement(By.id("password"));
  const submitButton = await driver.findElement(By.css('button[type="submit"]'));
  await driver.executeScript("arguments[0].scrollIntoView({ block: 'center' });", usernameInput);
  await driver.executeScript(`
    arguments[0].value = arguments[2];
    arguments[1].value = arguments[3];
    arguments[0].dispatchEvent(new Event("input", { bubbles: true }));
    arguments[1].dispatchEvent(new Event("input", { bubbles: true }));
  `, usernameInput, passwordInput, username, password);
  await driver.executeScript("arguments[0].click();", submitButton);
  await driver.wait(until.urlContains("/dashboard/"), 15000);
  stored = await driver.executeScript("return localStorage.getItem('site.a11y.v1');");
  assert(stored, "Las preferencias no permanecieron al navegar.");

  const dashboardLauncher = await driver.findElement(By.id("a11y-launcher"));
  await driver.executeScript("arguments[0].click();", dashboardLauncher);
  const resetButton = await driver.findElement(By.css("[data-a11y-reset]"));
  await driver.executeScript("arguments[0].click();", resetButton);
  const closeButton = await driver.findElement(By.css("[data-a11y-close]"));
  await driver.executeScript("arguments[0].click();", closeButton);
  stored = await driver.executeScript("return localStorage.getItem('site.a11y.v1');");
  assert(stored === null, "Restablecer no eliminó únicamente la clave de accesibilidad.");
  const defaultClasses = await driver.executeScript("return document.documentElement.className;");
  assert(defaultClasses.includes("a11y-text-100"), "Restablecer no volvió al tamaño predeterminado.");

  const linkedIn = await driver.findElement(By.css(".social-link--linkedin"));
  const linkedInIcon = await linkedIn.findElement(By.css(".social-icon"));
  await driver.actions().move({ origin: await driver.findElement(By.css("main")), x: 0, y: 0 }).perform();
  await driver.sleep(100);
  const beforeHover = await driver.executeScript(
    "return getComputedStyle(arguments[0]).backgroundColor;",
    linkedInIcon
  );
  await driver.actions().move({ origin: linkedIn }).perform();
  await driver.sleep(200);
  const afterHover = await driver.executeScript(
    "return getComputedStyle(arguments[0]).backgroundColor;",
    linkedInIcon
  );
  assert(
    beforeHover !== afterHover,
    `El icono de LinkedIn no cambió a su color de marca (${beforeHover} -> ${afterHover}).`
  );

  console.log("Prueba funcional de accesibilidad: OK");
  console.log("- Primer Tab, Enter, Espacio, Escape y retorno de foco: OK");
  console.log("- Combinación, recarga, navegación y persistencia: OK");
  console.log("- Restablecimiento limitado a site.a11y.v1: OK");
  console.log("- Hover de icono social a color de marca: OK");
} finally {
  await driver.quit();
}
