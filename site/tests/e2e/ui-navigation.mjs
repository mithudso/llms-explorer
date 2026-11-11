// Browser regressions for the concept tree and shared resources menu.
// Run against an existing local server: SITE=http://127.0.0.1:4328 node tests/e2e/ui-navigation.mjs
// External requests are blocked: this suite needs no model, analytics or live API.
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import puppeteer from 'puppeteer-core';

const site = process.env.SITE || 'http://127.0.0.1:4328';
const origin = new URL(site).origin;
const chrome = process.env.CHROME || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium',
].find(existsSync);
assert.ok(chrome, 'Set CHROME to an installed Chromium browser');
const evidence = process.env.UI_EVIDENCE_DIR;
if (evidence) mkdirSync(evidence, { recursive: true });
const browser = await puppeteer.launch({ executablePath: chrome, headless: true });
const report = { browser: await browser.version(), site, checks: [] };
const record = (name, values) => report.checks.push({ name, ...values });
try {
  const page = await browser.newPage();
  page.setDefaultTimeout(15000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.setRequestInterception(true);
  page.on('request', request => {
    const url = request.url();
    void (url.startsWith(origin + '/') || url.startsWith('data:')
      ? request.continue() : request.abort());
  });
  for (const width of [320, 390, 1440]) {
    await page.setViewport({ width, height: 900 });
    await page.goto(`${site}/tree/`, { waitUntil: 'networkidle0' });
    // Filtering reveals the ancestor path without pointer interaction.
    const concept = await page.$eval('li.frontier', el => el.dataset.concept);
    await page.type('#tree-filter', concept);
    const button = await page.$('li.frontier:not([hidden]) > .frontier-select');
    assert.ok(button, 'Frontier selection must expose a native button');
    await button.focus();
    assert.equal(await button.evaluate(el => document.activeElement === el), true);
    for (const key of ['Enter', 'Space']) {
      await page.keyboard.press(key);
      await page.waitForFunction(name => document.querySelector('#facts-panel .facts-title')?.textContent === name, {}, concept);
    }
    const cdp = await page.createCDPSession();
    const tree = await cdp.send('Accessibility.getFullAXTree');
    assert.ok(tree.nodes.some(node => node.role?.value === 'button' && node.name?.value.includes(concept)), 'AX tree must expose frontier as a named button');
    await cdp.detach();
    // Stress real longest identifiers and every nesting level, not just the collapsed roots.
    await page.$eval('#tree-filter', input => { input.value = ''; input.dispatchEvent(new Event('input', { bubbles: true })); });
    await page.evaluate(() => document.querySelectorAll('#tree-list details').forEach(el => { el.open = true; }));
    const layout = await page.evaluate(() => ({ viewport: innerWidth, content: document.documentElement.scrollWidth }));
    assert.ok(layout.content <= width + 1, `Expanded tree overflows: ${JSON.stringify(layout)}`);
    record('tree-keyboard-and-expanded-reflow', { width, concept, ...layout });
    if (evidence) await page.screenshot({ path: join(evidence, `tree-expanded-${width}.png`) });
  }
  for (const size of [{ width: 390, height: 500 }, { width: 844, height: 390 }, { width: 1440, height: 900 }]) {
    await page.setViewport(size);
    await page.goto(site, { waitUntil: 'networkidle0' });
    await page.focus('details.menu summary');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.querySelector('.menu-items').style.maxHeight !== '');
    const measure = () => page.$eval('.menu-items', panel => ({ top: panel.getBoundingClientRect().top, bottom: panel.getBoundingClientRect().bottom, viewport: innerHeight }));
    let rect = await measure();
    assert.ok(rect.bottom <= size.height, `Menu extends below viewport: ${JSON.stringify(rect)}`);
    await page.$eval('.menu-items', panel => { panel.scrollTop = panel.scrollHeight; });
    const last = await page.$eval('.menu-items a:last-child', el => ({ bottom: el.getBoundingClientRect().bottom, text: el.textContent }));
    assert.ok(last.bottom <= size.height, 'Final resource must be reachable by scrolling');
    await page.setViewport({ ...size, height: size.height - 60 });
    await page.waitForFunction(() => document.querySelector('.menu-items').getBoundingClientRect().bottom <= innerHeight);
    rect = await measure();
    await page.keyboard.press('Escape');
    assert.equal(await page.$eval('details.menu', el => !el.open && document.activeElement === el.querySelector('summary')), true);
    record('menu-fits-scrolls-resizes-and-returns-focus', { size, rect, last: last.text });
  }
  await page.setViewport({ width: 320, height: 900 });
  await page.goto(`${site}/blog/keyword-plus-vector/`, { waitUntil: 'networkidle0' });
  const contrast = await page.$$eval('pre.astro-code span[style]', tokens => {
    const rgb = color => color.match(/[\d.]+/g).slice(0, 3).map(Number);
    const luminance = color => rgb(color).map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
      .reduce((sum, value, i) => sum + value * [.2126, .7152, .0722][i], 0);
    return tokens.filter(el => el.textContent.trim()).map(el => {
      const fg = luminance(getComputedStyle(el).color);
      const bg = luminance(getComputedStyle(el.closest('pre')).backgroundColor);
      return (Math.max(fg, bg) + .05) / (Math.min(fg, bg) + .05);
    });
  });
  assert.ok(contrast.length > 0, 'Exercise real syntax-highlighted instruction text');
  assert.ok(Math.min(...contrast) >= 4.5, `Code token contrast below 4.5:1: ${Math.min(...contrast)}`);
  await page.addStyleTag({ content: '* { line-height:1.5!important; letter-spacing:.12em!important; word-spacing:.16em!important; } p { margin-bottom:2em!important; }' });
  const spacing = await page.evaluate(() => ({ viewport: innerWidth, content: document.documentElement.scrollWidth }));
  assert.ok(spacing.content <= 321, `Inline code overflows with text spacing: ${JSON.stringify(spacing)}`);
  record('article-code-contrast-and-text-spacing', { minimumContrast: Math.min(...contrast), tokens: contrast.length, ...spacing });
  assert.deepEqual(errors, []);
  report.passed = true;
} catch (error) {
  report.passed = false;
  report.failure = error.stack;
  process.exitCode = 1;
} finally {
  await browser.close();
  if (evidence) writeFileSync(join(evidence, 'ui-navigation.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
}
