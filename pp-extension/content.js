(function(){
  const LOG_PREFIX = '[CGEDGE-PP]';

  function getSlip(){
    try{
      // Try parent/opener localStorage if available
      const ls = window.localStorage;
      const raw = ls.getItem('ppSlip');
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.items)) return null;
      return parsed.items;
    }catch(e){
      console.warn(LOG_PREFIX, 'Failed to read ppSlip', e);
      return null;
    }
  }

  function sleep(ms){ return new Promise(res=>setTimeout(res, ms)); }

  async function clickByText(text){
    const candidates = Array.from(document.querySelectorAll('*'));
    const target = candidates.find(el => el.textContent && el.textContent.trim() === text);
    if (target){ target.click(); return true; }
    return false;
  }

  function normalizeName(n){
    return String(n||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  }

  function findPlayerCard(name){
    const norm = normalizeName(name);
    const cards = document.querySelectorAll('[data-testid*="player-card"], .PlayerCard, [class*="PlayerCard"]');
    for (const c of cards){
      const t = normalizeName(c.textContent||'');
      if (t.includes(norm)) return c;
    }
    return null;
  }

  function mapPropToSelector(prop){
    // Heuristic: look for prop tabs/buttons containing text
    const candidates = Array.from(document.querySelectorAll('button, [role="tab"], [data-testid*="tab"], [class*="Tab"]'));
    const target = candidates.find(el => {
      const txt = (el.textContent||'').toLowerCase();
      const p = prop.toLowerCase();
      return txt.includes(p);
    });
    return target || null;
  }

  async function addPick(item){
    // Navigate to sport/NBA if needed
    try{ await clickByText('NBA'); }catch(e){}
    await sleep(500);

    // Select prop category
    const tab = mapPropToSelector(item.prop);
    if (tab){ tab.click(); await sleep(400); }

    // Find player card
    const card = findPlayerCard(item.name);
    if (!card){ console.warn(LOG_PREFIX, 'Player card not found', item.name); return; }

    // Choose over/under – default Over
    const overBtn = card.querySelector('[data-testid*="over"], [aria-label*="Over"], button');
    if (overBtn){ overBtn.click(); await sleep(300); }
    else { card.click(); await sleep(300); }

    // Note: Exact line matching in PP DOM varies; we rely on default selection.
  }

  async function run(){
    const slip = getSlip();
    if (!slip || !slip.length){ console.log(LOG_PREFIX, 'No slip in localStorage'); return; }
    console.log(LOG_PREFIX, 'Autofilling slip of', slip.length, 'items');
    for (const it of slip){
      try{ await addPick(it); }catch(e){ console.warn(LOG_PREFIX, 'AddPick failed', it, e); }
      await sleep(200);
    }
  }

  // Delay to allow app shell mount
  window.addEventListener('load', ()=>{
    setTimeout(run, 2000);
  });
})();
