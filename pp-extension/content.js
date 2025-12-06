(function(){
  const LOG_PREFIX = '[CGEDGE-PP]';

  function getSlipFromHash(){
    try{
      const h = (window.location.hash||'').replace(/^#/, '');
      if (!h) return null;
      const params = new URLSearchParams(h.includes('=') ? h : ('cgpp='+h));
      const enc = params.get('cgpp');
      if (!enc) return null;
      const json = decodeURIComponent(escape(atob(enc)));
      const parsed = JSON.parse(json);
      if (!parsed || !Array.isArray(parsed.items)) return null;
      // Persist to PP origin for refreshes
      localStorage.setItem('ppSlip', JSON.stringify(parsed));
      return parsed.items;
    }catch(e){ console.warn(LOG_PREFIX, 'Hash parse failed', e); return null; }
  }

  function getSlip(){
    try{
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

  async function setAuthed(flag){
    try{ await chrome.storage?.local?.set({ ppAuthed: !!flag }); }catch(e){}
  }
  async function isAuthed(){
    try{ const v = await chrome.storage?.local?.get('ppAuthed'); return !!(v && v.ppAuthed); }catch(e){ return false; }
  }

  function detectLoggedIn(){
    // Heuristics: presence of avatar/menu, absence of prominent Log In
    const hasAvatar = !!document.querySelector('[aria-label*="account" i], [data-testid*="avatar" i], [class*="Avatar" i]');
    const loginBtn = Array.from(document.querySelectorAll('a,button')).find(el=>/log\s*in/i.test(el.textContent||''));
    return hasAvatar || !loginBtn;
  }

  function routeToLoginPreservingHash(){
    const h = location.hash || '';
    const target = 'https://www.prizepicks.com/login' + (h || '');
    if (location.href !== target){
      console.log(LOG_PREFIX, 'Routing to login with slip hash');
      location.replace(target);
    }
  }

  function isPlaybookOrArticles(){
    const host = location.hostname;
    const path = location.pathname;
    return host.includes('playbook.prizepicks.com') || path.startsWith('/category/') || path.startsWith('/playbook/');
  }

  function redirectToAppWithHash(){
    const h = location.hash || '';
    const target = 'https://www.prizepicks.com/' + (h || '');
    if (location.href !== target) {
      console.log(LOG_PREFIX, 'Redirecting to app root with hash');
      location.replace(target);
    }
  }

  // Board route not guaranteed; prefer root and let SPA load tabs

  function sleep(ms){ return new Promise(res=>setTimeout(res, ms)); }

  function isHome(){
    return location.pathname === '/' || /All your picks\. One app\./i.test(document.body.textContent||'');
  }

  async function enterPicksFromHome(){
    // Try common CTAs on homepage to enter picks
    const ctas = Array.from(document.querySelectorAll('a,button'));
    const pickNow = ctas.find(el => /pick\s*now/i.test(el.textContent||''));
    const playersCta = ctas.find(el => /players/i.test(el.textContent||''));
    if (pickNow) { pickNow.click(); await sleep(800); return true; }
    if (playersCta) { playersCta.click(); await sleep(800); return true; }
    return false;
  }

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
    // If on homepage, enter the picks area first
    if (isHome()) { await enterPicksFromHome(); await sleep(600); }
    // Navigate to sport/NBA if needed
    try{ await clickByText('NBA'); }catch(e){}
    await sleep(500);

    // Select prop category
    const tab = mapPropToSelector(item.prop);
    if (tab){ tab.click(); await sleep(400); }

    // Find player card
    const card = findPlayerCard(item.name);
    if (!card){ console.warn(LOG_PREFIX, 'Player card not found', item.name); return; }

    // Choose Over explicitly
    let overBtn = card.querySelector('[data-testid*="over"], [aria-label*="Over"], button');
    // Try text-based match within card if generic button was selected
    if (overBtn && !/over/i.test(overBtn.textContent||'')) {
      overBtn = Array.from(card.querySelectorAll('button, [role="button"]')).find(b=>/\bover\b/i.test(b.textContent||'')) || overBtn;
    }
    if (overBtn){ overBtn.click(); await sleep(300); }
    else { card.click(); await sleep(300); }

    // Note: Exact line matching in PP DOM varies; we rely on default selection.
  }

  async function run(){
    if (isPlaybookOrArticles()) { redirectToAppWithHash(); return; }
    // stay on root; extension will pick tabs and players
    const slip = getSlipFromHash() || getSlip();
    if (!slip || !slip.length){ console.log(LOG_PREFIX, 'No slip in localStorage'); return; }
    // Persist slip in extension storage to survive navigation/login
    try{ await chrome.storage?.local?.set({ ppSlip: slip }); }catch(e){}
    // If not logged in, route to login once and wait for user
    const logged = detectLoggedIn() || await isAuthed();
    if (!logged){ routeToLoginPreservingHash(); return; }
    // Mark authed for future runs
    await setAuthed(true);
    console.log(LOG_PREFIX, 'Autofilling slip of', slip.length, 'items');
    for (const it of slip){
      try{ await addPick(it); }catch(e){ console.warn(LOG_PREFIX, 'AddPick failed', it, e); }
      await sleep(200);
    }
  }

  // Delay to allow app shell mount
  window.addEventListener('load', ()=>{
    setTimeout(async ()=>{
      // If arriving on login or post-login, restore slip from storage
      try{
        const st = await chrome.storage?.local?.get(['ppSlip','ppAuthed']);
        if (st && Array.isArray(st.ppSlip)){
          // Ensure localStorage has slip on PP origin
          localStorage.setItem('ppSlip', JSON.stringify({ version:1, items: st.ppSlip }));
        }
        // If we detect logged in after login flow, mark authed and run
        if (detectLoggedIn()) { await setAuthed(true); }
      }catch(e){}
      run();
    }, 2000);
  });
  window.addEventListener('hashchange', ()=> setTimeout(run, 500));

  // Add a small floating manual trigger for debugging
  function addManualButton(){
    try{
      const btn = document.createElement('button');
      btn.textContent = 'CGEDGE: Run Autofill';
      btn.style.position = 'fixed';
      btn.style.bottom = '16px';
      btn.style.right = '16px';
      btn.style.zIndex = '999999';
      btn.style.background = '#003322';
      btn.style.color = '#39d9a9';
      btn.style.border = '1px solid #39d9a966';
      btn.style.borderRadius = '10px';
      btn.style.padding = '8px 10px';
      btn.style.cursor = 'pointer';
      btn.addEventListener('click', run);
      document.body.appendChild(btn);
      // Gentle prompt if not logged in (detect visible Log In button)
      const loginBtn = Array.from(document.querySelectorAll('a,button')).find(el=>/log\s*in/i.test(el.textContent||''));
      if (loginBtn) {
        console.log(LOG_PREFIX, 'Login appears required. Please log in, then click Run Autofill.');
      }
    }catch(e){}
  }
  document.addEventListener('DOMContentLoaded', addManualButton);
})();
