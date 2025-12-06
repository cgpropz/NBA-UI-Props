const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

const STORAGE_PATH = path.resolve(__dirname, 'storage-state.json');

function decodeCgpp(cgpp){
  try{
    const json = decodeURIComponent(escape(Buffer.from(cgpp, 'base64').toString('binary')));
    const parsed = JSON.parse(json);
    if (!parsed || !Array.isArray(parsed.items)) return null;
    return parsed.items;
  }catch(e){
    console.warn('[PP-AUTO]', 'Failed to parse cgpp', e.message);
    return null;
  }
}

function readSlipFromFile(fp){
  const raw = fs.readFileSync(fp, 'utf8');
  const parsed = JSON.parse(raw);
  if (Array.isArray(parsed.items)) return parsed.items;
  if (Array.isArray(parsed)) return parsed;
  throw new Error('Invalid slip file format');
}

function norm(s){ return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim(); }

async function selectNBA(page){
  // Try common selectors and labels for NBA/Basketball
  const tries = [
    '[data-testid*="nba" i]', '[aria-label*="NBA" i]', '[data-sport*="nba" i]', '[href*="nba" i]',
    '[data-testid*="basketball" i]', '[aria-label*="Basketball" i]', '[data-testid*="chip" i]'
  ];
  for (const sel of tries){
    const els = await page.$$(sel);
    for (const el of els){
      const txt = (await el.textContent()||'') + (await el.getAttribute('data-testid')||'') + (await el.getAttribute('aria-label')||'');
      if (/\b(NBA|Basketball)\b/i.test(txt)) { await el.click(); await page.waitForTimeout(600); return true; }
    }
  }
  // Fallback by text
  const byText = await page.$('//button[normalize-space()="NBA" or contains(translate(.,"BASKETBALL","basketball"),"basketball")]
                              | //a[normalize-space()="NBA"]');
  if (byText){ await byText.click(); await page.waitForTimeout(600); return true; }
  return false;
}

async function ensureInPicks(page){
  // If on marketing homepage, click Pick Now or Players
  const pickNow = await page.$('xpath=//button[contains(translate(.,"PICK NOW","pick now"),"pick now") or @aria-label="Pick Now"]');
  if (pickNow) { await pickNow.click(); await page.waitForTimeout(1200); }
  const players = await page.$('xpath=//a[contains(translate(.,"PLAYERS","players"),"players")]');
  if (players) { await players.click(); await page.waitForTimeout(1200); }
  // Fallback direct navigation if content still looks like marketing page
  const onMarketing = await page.evaluate(()=>/All your picks\. One app\./i.test(document.body.textContent||''));
  if (onMarketing){ await page.goto('https://www.prizepicks.com/', { waitUntil: 'domcontentloaded' }); }
  // Wait for tabs/chips to render
  for (let i=0;i<10;i++){
    const shellReady = await page.$('[role="tablist"], [data-testid*="chip" i], [data-testid*="players" i]');
    if (shellReady) break;
    await page.waitForTimeout(300);
  }
}

async function findPlayerCard(page, name){
  const target = norm(name);
  const candidates = await page.$$('[data-testid*="player-card"], .PlayerCard, [class*="PlayerCard"]');
  for (const c of candidates){
    const txt = norm(await c.textContent());
    if (txt.includes(target)) return c;
  }
  return null;
}

async function clickPropTab(page, prop){
  const p = norm(prop);
  const tabs = await page.$$('button, [role="tab"], [data-testid*="tab"], [class*="Tab"]');
  for (const t of tabs){
    const txt = norm(await t.textContent());
    if (txt.includes(p)) { await t.click(); await page.waitForTimeout(400); return true; }
  }
  return false;
}

async function chooseSide(card, side){
  const wantOver = String(side||'Over').toLowerCase() === 'over';
  const overCand = await card.$('[data-testid*="over" i], [aria-label*="Over"], button');
  const underCand = await card.$('[data-testid*="under" i], [aria-label*="Under"], button');
  let overBtn = overCand;
  if (overBtn){
    const txt = (await overBtn.textContent()||'');
    if (!/over/i.test(txt)) overBtn = await card.$('xpath=.//button[contains(translate(.,"OVER","over"),"over")]');
  }
  let underBtn = underCand;
  if (underBtn){
    const txt = (await underBtn.textContent()||'');
    if (!/under/i.test(txt)) underBtn = await card.$('xpath=.//button[contains(translate(.,"UNDER","under"),"under")]');
  }
  const clickBtn = wantOver ? (overBtn || overCand) : (underBtn || underCand);
  if (clickBtn) { await clickBtn.click(); await card.page().waitForTimeout(300); return true; }
  await card.click(); await card.page().waitForTimeout(300); return true;
}

async function main(){
  const argv = yargs(hideBin(process.argv))
    .option('slip', { type: 'string', describe: 'Path to slip JSON {items:[{name,prop,side}]}' })
    .option('cgpp', { type: 'string', describe: 'Base64 cgpp hash payload' })
    .option('headful', { type: 'boolean', default: false, describe: 'Run with UI for debugging' })
    .argv;

  let items = null;
  if (argv.cgpp) items = decodeCgpp(argv.cgpp);
  if (!items && argv.slip) items = readSlipFromFile(argv.slip);
  if (!items) throw new Error('Provide --cgpp or --slip path');

  const browser = await chromium.launch({ headless: !argv.headful });
  const contextOpts = fs.existsSync(STORAGE_PATH) ? { storageState: STORAGE_PATH } : {};
  const context = await browser.newContext(contextOpts);
  const page = await context.newPage();

  await page.goto('https://www.prizepicks.com/', { waitUntil: 'load' });
  // Extra sleeps to move past marketing/landing transitions
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  // Try up to 5 passes to enter picks UI and select NBA
  for (let i=0; i<5; i++){
    await ensureInPicks(page);
    await page.waitForTimeout(1000);
    const selected = await selectNBA(page);
    if (selected) break;
    await page.waitForTimeout(1500);
  }

  for (const it of items){
    try{
      await clickPropTab(page, it.prop);
      const card = await findPlayerCard(page, it.name);
      if (!card) { console.warn('[PP-AUTO]', 'Player not found:', it.name); continue; }
      await chooseSide(card, it.side || 'Over');
    }catch(e){ console.warn('[PP-AUTO]', 'Failed on item', it, e.message); }
    await page.waitForTimeout(250);
  }

  // Keep open briefly if headful for visual confirmation
  if (argv.headful){
    console.log('[PP-AUTO]', 'Complete. Close the window to finish.');
    await page.waitForTimeout(3000);
  }
  await browser.close();
}

main().catch((e)=>{ console.error(e); process.exit(1); });
