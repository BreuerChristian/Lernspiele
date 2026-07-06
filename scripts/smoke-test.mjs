#!/usr/bin/env node
// smoke-test.mjs - Headless-Durchlauf jedes Spiels mit Playwright/Chromium.
//
// Serviert das Repo lokal, oeffnet jedes <spiel>/ und prueft:
//   - keine unbehandelten JS-Fehler (pageerror) und keine console.error
//   - Start-Screen rendert (Karte + Start-Button)
//   - Best-effort: Start klicken -> Game-Screen -> ein paar Taps -> Schliessen
//     (schlaegt NICHT fehl, wenn ein Selektor fehlt; nur echte JS-Fehler zaehlen)
//
// Faengt Runtime-Bugs, die statische Linter nicht sehen (veraltete Timer beim
// Neustart, rAF-Ausnahmen, kaputte Handler). Logik-Korruption ohne throw kann
// er nicht sehen — dafuer ist der Code-Review da.
//
// Usage:  node scripts/smoke-test.mjs [spiel ...]      (ohne Args = alle Spiele)
// Exit 0 = alles ok, 1 = mind. ein Spiel mit Fehler.

import { createServer } from 'node:http';
import { readFile, readdir, stat } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, extname, resolve } from 'node:path';

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const EXCLUDE = new Set(['_lib', '_templates', 'scripts', '.git', '.claude', 'node_modules']);
const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.css': 'text/css',
  '.png': 'image/png', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
};

// Playwright liegt global (/opt/node22/...) — lokal als Fallback.
function loadChromium() {
  const tries = [];
  try { return createRequire(import.meta.url)('playwright').chromium; } catch (e) { tries.push(e.message); }
  try {
    const groot = execSync('npm root -g').toString().trim();
    return createRequire(join(groot, 'x.js'))('playwright').chromium;
  } catch (e) { tries.push(e.message); }
  console.error('Playwright nicht ladbar:\n  ' + tries.join('\n  '));
  process.exit(2);
}

async function findGames() {
  const out = [];
  for (const name of (await readdir(REPO)).sort()) {
    if (EXCLUDE.has(name) || name.startsWith('.')) continue;
    try {
      if ((await stat(join(REPO, name))).isDirectory() &&
          (await stat(join(REPO, name, 'index.html'))).isFile()) out.push(name);
    } catch { /* kein index.html */ }
  }
  return out;
}

function startServer() {
  const server = createServer(async (req, res) => {
    try {
      let path = decodeURIComponent(req.url.split('?')[0]);
      if (path.endsWith('/')) path += 'index.html';
      const file = join(REPO, path);
      if (!file.startsWith(REPO)) { res.writeHead(403).end(); return; }
      const body = await readFile(file);
      res.writeHead(200, { 'Content-Type': MIME[extname(file)] || 'application/octet-stream' });
      res.end(body);
    } catch { res.writeHead(404).end('not found'); }
  });
  return new Promise((res) => server.listen(0, () => res(server)));
}

async function checkGame(browser, base, game) {
  const errors = [];
  const context = await browser.newContext();
  const page = await context.newPage();
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });

  try {
    const resp = await page.goto(`${base}/${game}/`, { waitUntil: 'load', timeout: 15000 });
    if (!resp || !resp.ok()) errors.push(`HTTP ${resp ? resp.status() : 'kein Response'}`);
    await page.waitForTimeout(300);

    // Start-Screen: prominenter Start-Button. Spiele benennen ihn unterschiedlich
    // (#btn-start, .btn-primary, .big-btn, #btn-go, "Los …") — breit suchen, aber
    // Icon-/Schliessen-Buttons (×) ausklammern.
    const startBtn = page.locator(
      '#btn-start, #btn-go, .btn-primary, .big-btn:not(.secondary), button:has-text("Los ")'
    ).first();
    if (await startBtn.count()) {
      await startBtn.click({ timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(300);
      // Best-effort ein paar Taps im Spielbereich (Handler ausloesen)
      const taps = page.locator('.cell, .game-cell, .board button, .choice, .tube, .bolt');
      const n = Math.min(await taps.count(), 4);
      for (let i = 0; i < n; i++) { await taps.nth(i).click({ timeout: 1000 }).catch(() => {}); await page.waitForTimeout(120); }
      // Neustart-Zyklus: schliessen und nochmal starten (deckt veraltete Timer auf)
      const close = page.locator('#hud-close').first();
      if (await close.count()) {
        await close.click({ timeout: 1000 }).catch(() => {});
        await page.waitForTimeout(200);
        if (await startBtn.count()) { await startBtn.click({ timeout: 1000 }).catch(() => {}); await page.waitForTimeout(300); }
      }
    } else {
      errors.push('kein Start-Button auf dem Start-Screen gefunden');
    }
    await page.waitForTimeout(300); // veraltete Timer feuern lassen
  } catch (e) {
    errors.push('Ausnahme: ' + e.message);
  } finally {
    await context.close();
  }
  return errors;
}

async function main() {
  const chromium = loadChromium();
  const only = process.argv.slice(2);
  const games = only.length ? only : await findGames();
  const server = await startServer();
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ headless: true });

  let failed = 0;
  for (const game of games) {
    const errors = await checkGame(browser, base, game);
    if (errors.length) {
      failed++;
      console.log(`### ${game}  — ${errors.length} Fehler`);
      for (const e of errors) console.log(`  ${e}`);
    } else {
      console.log(`ok   ${game}`);
    }
  }

  await browser.close();
  server.close();
  console.log(`\n${'='.repeat(60)}`);
  console.log(failed ? `${failed}/${games.length} Spiele mit Fehlern.` : `Alle ${games.length} Spiele ok.`);
  console.log('='.repeat(60));
  process.exit(failed ? 1 : 0);
}

main();
