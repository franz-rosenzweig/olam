// Learn: the Road, the lesson for the chosen stop (Read, See, Do, Check), and the Atlas of Rules.
'use strict';
(() => {
  const { esc, api, icon, md, badge } = O;
  const $ = (s, el = document) => el.querySelector(s);

  // Stop positions along the road, in percent of a 1200 × 200 strip.
  const POS = [[3.83, 61.75], [9.27, 75.1], [14.7, 75.15], [20.12, 61.75], [25.56, 42.75], [30.99, 29.1], [36.43, 28.65], [41.85, 41.75], [47.28, 60.75],
    [52.72, 74.7], [58.15, 75.5], [63.57, 62.75], [69.01, 43.8], [74.44, 29.55], [79.88, 28.3], [85.3, 40.75], [90.73, 59.7], [96.17, 74.2]];
  const PTS = POS.map(([x, y]) => [x * 12, y * 2]);
  function seg(i) {
    const p0 = PTS[Math.max(i - 1, 0)], p1 = PTS[i], p2 = PTS[i + 1], p3 = PTS[Math.min(i + 2, PTS.length - 1)];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6], c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    return `C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  const pathTo = n => `M ${PTS[0][0]} ${PTS[0][1]} ` + Array.from({ length: Math.max(0, n - 1) }, (_, i) => seg(i)).join(' ');
  const WEEKLABEL = [[111, 60], [307, 184], [502, 184], [698, 60], [893, 184], [1089, 40]];

  let S = null;          // learn state from the server
  let sel = null;        // selected stop number
  let L = null;          // the open lesson
  let step = 'read';
  let region = 'heart';

  const blank = () => ({ status: '', steps: [], answers: {} });
  const loadState = () => O.demo
    ? api('learn/state', { body: { progress: O.local.progress(), review: O.local.review() } })
    : api('learn');
  function localUpdate(fn) {
    const P = O.local.progress();
    P[L.id] = P[L.id] || blank();
    fn(P[L.id]);
    O.local.setProgress(P);
    L.progress = P[L.id];
  }

  O.routes.learn = async (main, r) => {
    S = await loadState();
    O.setReviewCount(S.review);
    const want = r.rest ? S.stops.find(s => s.id === r.rest) : null;
    sel = want ? want.n : (sel && S.stops[sel - 1] ? sel : S.current);
    main.innerHTML = `<header class="pagehead"><div><span class="eyebrow" id="weeklabel"></span><h1>The Road</h1></div>
      <div class="chips" id="headchips"></div></header>
      <section class="card" style="padding:0;gap:0;overflow:hidden"><div class="roadwrap"><div class="road" id="road"></div></div><div class="stopbar" id="stopbar"></div></section>
      <div class="row"><section class="card" id="lesson" style="flex:3 1 560px;min-width:0"></section>
      <section class="card" id="atlas" style="flex:2 1 380px;min-width:0"></section></div>`;
    drawHead(); drawRoad(); drawStopbar(); drawAtlas();
    await openLesson(S.stops[sel - 1].id);
  };

  function drawHead() {
    const cur = S.current;
    $('#weeklabel').textContent = `Learn · Week ${Math.min(6, Math.ceil(cur / 3))} of 6`;
    $('#headchips').innerHTML = `<span class="chip">Stop ${cur} of ${S.stops.length}</span>
      ${S.review ? `<a class="chip brass" href="#/review">${icon('review', 14)}${S.review} to review</a>` : ''}
      <span class="chip">Rules · 2024</span>`;
  }

  function drawRoad() {
    const done = S.stops.filter(s => s.status === 'done').length;
    const traveled = Math.min(S.stops.length, done + 1);
    const deco = '<defs><g id="rmt"><path d="M-14 9 L0 -12 L14 9" fill="none" stroke="rgba(201,165,90,.28)" stroke-width="1.4" stroke-linejoin="round"/></g>' +
      '<g id="rtr"><circle r="5" fill="none" stroke="rgba(155,174,122,.35)" stroke-width="1.2"/><path d="M0 5 V9" stroke="rgba(155,174,122,.35)" stroke-width="1.2"/></g></defs>' +
      '<g stroke="#2B3038" stroke-dasharray="3 6">' + [209, 404.5, 600, 795.5, 991].map(x => `<path d="M${x} 14 V186"/>`).join('') + '</g>' +
      [[70, 70], [90, 82], [150, 96], [645, 98], [668, 86], [720, 96]].map(([x, y]) => `<use href="#rtr" x="${x}" y="${y}"/>`).join('') +
      [[300, 150], [330, 160], [470, 150], [880, 140], [910, 152], [940, 142]].map(([x, y]) => `<use href="#rmt" x="${x}" y="${y}"/>`).join('');
    $('#road').innerHTML = `<svg viewBox="0 0 1200 200" aria-hidden="true">${deco}
      <path d="${pathTo(PTS.length)}" fill="none" stroke="#3A4049" stroke-width="5" stroke-dasharray="1 11" stroke-linecap="round"/>
      ${traveled > 1 ? `<path d="${pathTo(traveled)}" fill="none" stroke="#D9A54A" stroke-width="4" stroke-linecap="round"/>` : ''}
      <g style="font-family:var(--serif);font-size:16px;fill:#A9A293" text-anchor="middle">${S.weeks.map((w, i) => `<text x="${WEEKLABEL[i][0]}" y="${WEEKLABEL[i][1]}">Week ${i + 1} · ${esc(w)}</text>`).join('')}</g></svg>
      ${S.stops.map((s, i) => `<button type="button" class="stop st-${s.status}${s.n === sel ? ' sel' : ''}" style="left:${POS[i][0]}%;top:${POS[i][1]}%" data-stop="${s.n}"
        aria-label="Stop ${s.n}: ${esc(s.title)}" aria-pressed="${s.n === sel}"><span>${s.n}</span></button>`).join('')}`;
    $('#road').querySelectorAll('[data-stop]').forEach(b => b.onclick = () => {
      sel = +b.dataset.stop; drawRoad(); drawStopbar();
      openLesson(S.stops[sel - 1].id);
    });
  }

  function drawStopbar() {
    const s = S.stops[sel - 1];
    const status = { done: 'Done', current: 'In progress', locked: 'Not yet' }[s.status];
    $('#stopbar').innerHTML = `<span class="eyebrow">Stop ${s.n}</span><span class="title">${esc(s.title)}</span>
      <span class="track ${s.track}">${s.track}</span>${s.minutes ? `<span class="dim">${s.minutes} min</span>` : ''}
      <span style="color:${s.status === 'done' ? 'var(--brass-hi)' : s.status === 'current' ? 'var(--text)' : 'var(--dim)'}">${status}</span>
      ${s.status === 'locked' && S.stops[S.current - 1] ? `<button class="btn small" type="button" id="tocurrent">Back to stop ${S.current}</button>` : ''}`;
    const t = $('#tocurrent');
    if (t) t.onclick = () => { sel = S.current; drawRoad(); drawStopbar(); openLesson(S.stops[sel - 1].id); };
  }

  // ---------- lesson ----------
  async function openLesson(id) {
    const box = $('#lesson');
    box.innerHTML = '<span class="spinner"></span>';
    L = await api('learn/' + id);
    if (O.demo) L.progress = O.local.progress()[id] || blank();
    const steps = stepList();
    step = steps.includes(step) && L.id === box.dataset.id ? step : steps[0];
    box.dataset.id = L.id;
    drawLesson();
  }
  const stepList = () => ['read', 'see', 'do', 'check'].filter(k => k === 'read' || L[k]);
  const LABEL = { read: 'Read', see: 'See', do: 'Do', check: 'Check' };

  function drawLesson() {
    const box = $('#lesson');
    const p = L.progress || {};
    const done = p.status === 'done';
    box.innerHTML = `<div class="cardhead" style="align-items:flex-start"><div style="display:flex;flex-direction:column;gap:4px">
        <span class="eyebrow">Stop ${L.n} · ${esc(L.track)}${L.minutes ? ' · ' + L.minutes + ' min' : ''}</span>
        <h2 style="font-size:32px">${esc(L.title)}</h2></div>
        <span class="chip ${done ? 'brass' : ''}">${done ? 'Complete' : L.outline ? 'Outline' : S.stops[L.n - 1].status === 'locked' ? 'Looking ahead' : 'In progress'}</span></div>
      ${stepList().length > 1 ? `<div class="steps" role="group" aria-label="Lesson steps">${stepList().map(k => `<button type="button" data-step="${k}" class="${k === step ? 'on' : ''}" aria-pressed="${k === step}">
        ${(k === 'check' ? done : (p.steps || []).includes(k) && k !== step) ? icon('check', 14) : ''}${LABEL[k]}</button>`).join('')}</div>` : ''}
      <div id="stepbody" style="display:flex;flex-direction:column;gap:16px"></div>`;
    box.querySelectorAll('[data-step]').forEach(b => b.onclick = () => { step = b.dataset.step; drawLesson(); });
    if (O.demo) localUpdate(p => { if (!p.steps.includes(step)) p.steps.push(step); p.status = p.status || 'started'; });
    else api(`learn/${L.id}/step`, { body: { step } }).then(s => { L.progress.steps = (S = s, s.stops.find(x => x.id === L.id).steps); }).catch(() => {});
    ({ read: drawRead, see: drawSee, do: drawDo, check: drawCheck })[step]($('#stepbody'));
  }

  function drawRead(el) {
    const R = L.read || {};
    el.innerHTML = `<p class="lead">${md(R.lead || '').replace(/^<p>|<\/p>$/g, '')}</p>
      ${R.cards ? `<div class="cards3">${R.cards.map(c => `<div class="lcard ${c.tone || ''}"><b>${esc(c.title)}</b><span>${esc(c.text)}</span></div>`).join('')}</div>` : ''}
      ${R.points ? `<ul class="points">${R.points.map(x => `<li>${md(x).replace(/^<p>|<\/p>$/g, '')}</li>`).join('')}</ul>` : ''}
      ${R.table ? `<div class="prose"><p class="eyebrow">${esc(R.table.title)}</p><table><thead><tr>${R.table.head.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${R.table.rows.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : ''}
      ${R.lists ? `<div class="cards3">${R.lists.map(l => `<div style="display:flex;flex-direction:column;gap:6px"><span class="eyebrow">${esc(l.title)}</span>${l.items.map(i => `<span class="sunk" style="padding:8px 12px">${esc(i)}</span>`).join('')}</div>`).join('')}</div>` : ''}
      <div style="display:flex;flex-direction:column;gap:10px;padding-top:6px;border-top:1px solid var(--line)">
        <div class="cardhead"><span style="font-weight:700">Sources</span><span class="chips">${['rule', 'third', 'expert', 'craft', 'idea', 'yours'].map(k => badge(k)).join('')}</span></div>
        ${L.sources.map(srcHTML).join('')}</div>
      ${L.outline ? `<div class="done" style="background:var(--panel-2);border-color:var(--line-2)"><span style="flex:1 1 200px">${esc(L.progress.status === 'done' ? 'Marked as read' : '')}</span>
        ${L.progress.status === 'done' ? '' : `<button class="btn primary" id="markdone" type="button">${icon('check', 16)}Mark as read</button>`}</div>` : ''}`;
    const m = $('#markdone');
    if (m) m.onclick = async () => {
      if (O.demo) { localUpdate(p => { p.status = 'done'; }); S = await loadState(); }
      else S = await api(`learn/${L.id}/complete`, { body: {} });
      L.progress.status = 'done'; refreshAll();
    };
  }

  function srcHTML(s) {
    if (s.type === 'entry') return `<a class="srcrow" href="#/wiki/${encodeURIComponent(s.id)}" style="text-decoration:none;color:inherit">${badge(s.shelf)}<span class="what"><span>${esc(s.title)}</span><small>${esc(s.sub)}</small></span>${icon('link', 16, '#A9A293')}</a>`;
    if (s.type === 'browse') return `<a class="srcrow" href="#/browse/${esc(s.kind)}" style="text-decoration:none;color:inherit">${badge('rule')}<span class="what"><span>${esc(s.title)}</span><small>${esc(s.sub)}</small></span></a>`;
    if (s.type === 'book') return `<div class="srcrow">${badge(s.shelf)}<span class="what"><span>${esc(s.title)}</span><small>${esc(s.sub)} · private</small></span>
      <div class="pages">${s.passages.map(p => `<a href="#/wiki/${encodeURIComponent(p.id)}">${esc(p.snippet).replace(/\[\[(.+?)\]\]/g, '<mark>$1</mark>')}</a>`).join('')}</div></div>`;
    if (s.type === 'zim') return `<div class="srcrow">${badge(s.shelf, s.note ? 'Idea · not official' : '')}<span class="what"><span>${esc(s.title)}</span><small>${s.total.toLocaleString()} pages for “${esc(s.q)}”</small></span>
      <div class="pages">${s.pages.map(p => `<a href="#/read/${encodeURIComponent(s.zim)}/${encodeURIComponent(p.path)}">${p.votes != null ? `<b style="color:var(--blue)">${p.votes}</b> · ` : ''}${esc(p.title)}</a>`).join('')}</div></div>`;
    return '';
  }

  function drawSee(el) {
    const V = L.see;
    let html = '';
    if (V.lines) html += `<div class="dialog">${V.lines.map(l => `<div class="line"><span class="who">${esc(l.who)}</span><span class="what"><span>${esc(l.text)}</span>${l.tag ? `<span class="tag">${esc(l.tag)}</span>` : ''}</span></div>`).join('')}</div>`;
    if (V.text) html += `<p class="lead">${esc(V.text)}</p>`;
    if (V.chips) html += `<div class="chips">${V.chips.map(c => `<span class="chip">${esc(c)}</span>`).join('')}</div>`;
    el.innerHTML = html + (V.roll ? '<div id="seeroll"></div>' : '');
    if (V.roll) drawRoll($('#seeroll'), V.roll, V.roll.dice);
  }

  function drawRoll(el, R, dice) {
    const keep = R.mode === 'adv' ? Math.max(...dice) : R.mode === 'dis' ? Math.min(...dice) : dice[0];
    const ki = dice.indexOf(keep);
    const total = keep + R.bonus;
    const crit = R.attack && keep === 20, fumble = R.attack && keep === 1;
    const ok = crit || (!fumble && total >= R.target);
    el.innerHTML = `<div class="dicebox">${dice.map((d, i) => `<span class="die ${i === ki ? 'kept' : ''}">${d}</span>`).join('')}
      <span style="font-size:22px;color:var(--dim)">+ ${R.bonus} =</span><span class="total">${total}</span>
      <span class="dim">${R.target_label} ${R.target}</span>
      <span class="verdict ${ok ? 'yes' : 'no'}">${crit ? 'Critical Hit' : fumble ? 'A 1 always misses' : ok ? (R.attack ? 'Hit' : 'Success') : (R.attack ? 'Miss' : 'Failure')}</span></div>
      <button class="btn primary" type="button" style="align-self:flex-start;margin-top:12px">${icon('d20', 18)}Roll again</button>`;
    el.querySelector('button').onclick = () => drawRoll(el, R, O.rollDice(R.mode === 'normal' ? 1 : 2, 20));
  }

  // ---------- Do ----------
  function drawDo(el) {
    const D = L.do;
    ({ sort: doSort, modifier: doModifier, array: doArray, dm: doDM, advantage: doAdvantage })[D.type](el, D);
  }

  function doSort(el, D) {
    const picks = {};
    const draw = () => {
      const right = D.items.filter((it, i) => picks[i] === it.a).length;
      el.innerHTML = `<div class="cardhead"><span style="font-weight:700">${esc(D.prompt)}</span><span class="dim">${right} / ${D.items.length}</span></div>
        <div class="sortitems">${D.items.map((it, i) => {
          const p = picks[i];
          return `<div class="sortitem ${p ? (p === it.a ? 'right' : 'wrong') : ''}"><span>${esc(it.t)}</span>
            <div class="seg">${D.buckets.map(b => `<button type="button" data-i="${i}" data-b="${esc(b)}" class="${p === b ? 'on' : ''}" aria-pressed="${p === b}">${esc(b)}</button>`).join('')}</div></div>`;
        }).join('')}</div>${right === D.items.length ? '<div class="done"><b>All sorted</b></div>' : ''}`;
      el.querySelectorAll('[data-b]').forEach(b => b.onclick = () => { picks[b.dataset.i] = b.dataset.b; draw(); });
    };
    draw();
  }

  function doModifier(el) {
    let score = 14, prof = true, dc = 15, last = null;
    const draw = () => {
      const m = Math.floor((score - 10) / 2), bonus = m + (prof ? 2 : 0);
      el.innerHTML = `<div class="cards3">
        <label class="lcard"><span class="eyebrow">Ability score</span><b>${score} → ${m >= 0 ? '+' : '−'}${Math.abs(m)}</b>
          <input type="range" min="1" max="20" value="${score}" id="mscore" style="accent-color:var(--brass);width:100%"></label>
        <div class="lcard"><span class="eyebrow">Proficient</span><b>${prof ? '+2' : '+0'}</b>
          <button type="button" class="toggle ${prof ? 'on' : ''}" id="mprof"><span class="box">${prof ? '✓' : ''}</span>Proficiency Bonus</button></div>
        <div class="lcard"><span class="eyebrow">Difficulty Class</span><b>DC ${dc}</b>
          <div class="seg" style="flex-wrap:wrap">${[5, 10, 15, 20, 25].map(v => `<button type="button" data-dc="${v}" class="${v === dc ? 'on' : ''}" style="min-width:44px">${v}</button>`).join('')}</div></div></div>
        <div id="mroll"></div>`;
      $('#mscore', el).oninput = e => { score = +e.target.value; draw(); };
      $('#mprof', el).onclick = () => { prof = !prof; draw(); };
      el.querySelectorAll('[data-dc]').forEach(b => b.onclick = () => { dc = +b.dataset.dc; draw(); });
      drawRoll($('#mroll', el), { bonus, target: dc, target_label: 'DC', mode: 'normal' }, last || [10]);
      $('#mroll button', el).onclick = () => { last = O.rollDice(1, 20); drawRoll($('#mroll', el), { bonus, target: dc, target_label: 'DC', mode: 'normal' }, last); };
    };
    draw();
  }

  const AB = ['Str', 'Dex', 'Con', 'Int', 'Wis', 'Cha'];
  const ARR = { Barbarian: [15, 13, 14, 10, 12, 8], Bard: [8, 14, 12, 13, 10, 15], Cleric: [14, 8, 13, 10, 15, 12], Druid: [8, 12, 14, 13, 15, 10],
    Fighter: [15, 14, 13, 8, 10, 12], Monk: [12, 15, 13, 10, 14, 8], Paladin: [15, 10, 13, 8, 12, 14], Ranger: [12, 15, 13, 8, 14, 10],
    Rogue: [12, 15, 13, 14, 10, 8], Sorcerer: [10, 13, 14, 8, 12, 15], Warlock: [8, 14, 13, 12, 10, 15], Wizard: [8, 12, 13, 15, 14, 10] };
  const BG = { Acolyte: ['Int', 'Wis', 'Cha'], Criminal: ['Dex', 'Con', 'Int'], Sage: ['Con', 'Int', 'Wis'], Soldier: ['Str', 'Dex', 'Con'] };
  function doArray(el) {
    let cls = 'Fighter', bg = 'Soldier', scores = ARR.Fighter.slice(), plus2 = 'Str', plus1 = 'Con', even = false;
    const draw = () => {
      const bonus = AB.map(a => even ? (BG[bg].includes(a) ? 1 : 0) : (a === plus2 ? 2 : a === plus1 ? 1 : 0));
      const fin = scores.map((s, i) => Math.min(20, s + bonus[i]));
      el.innerHTML = `<div class="cards3">
        <label class="lcard"><span class="eyebrow">Class</span><select id="acls" style="min-height:44px;background:var(--ground);border:1px solid var(--line-2);border-radius:10px;padding:0 10px">${Object.keys(ARR).map(c => `<option ${c === cls ? 'selected' : ''}>${c}</option>`).join('')}</select></label>
        <label class="lcard"><span class="eyebrow">Background</span><select id="abg" style="min-height:44px;background:var(--ground);border:1px solid var(--line-2);border-radius:10px;padding:0 10px">${Object.keys(BG).map(c => `<option ${c === bg ? 'selected' : ''}>${c}</option>`).join('')}</select>
          <span class="dim" style="font-size:14px">${BG[bg].join(', ')}</span></label>
        <div class="lcard"><span class="eyebrow">Increase</span><div class="seg"><button type="button" id="a21" class="${even ? '' : 'on'}">+2 / +1</button><button type="button" id="a111" class="${even ? 'on' : ''}">+1 each</button></div>
          ${even ? '' : `<div style="display:flex;gap:8px;flex-wrap:wrap">${['+2', '+1'].map((lbl, k) => `<label class="dim" style="display:flex;gap:6px;align-items:center">${lbl}<select data-p="${k}" style="min-height:36px;background:var(--ground);border:1px solid var(--line-2);border-radius:8px">${BG[bg].map(a => `<option ${(k ? plus1 : plus2) === a ? 'selected' : ''}>${a}</option>`).join('')}</select></label>`).join('')}</div>`}</div></div>
        <div class="prose"><table><thead><tr><th></th>${AB.map(a => `<th>${a}</th>`).join('')}</tr></thead><tbody>
          <tr><td class="dim">Array</td>${scores.map((s, i) => `<td><select data-ab="${i}" style="background:var(--ground);border:1px solid var(--line-2);border-radius:6px;min-height:32px">${[15, 14, 13, 12, 10, 8].map(v => `<option ${v === s ? 'selected' : ''}>${v}</option>`).join('')}</select></td>`).join('')}</tr>
          <tr><td class="dim">Background</td>${bonus.map(b => `<td>${b ? '+' + b : ''}</td>`).join('')}</tr>
          <tr><td class="dim">Score</td>${fin.map(s => `<td><b>${s}</b></td>`).join('')}</tr>
          <tr><td class="dim">Modifier</td>${fin.map(s => { const m = Math.floor((s - 10) / 2); return `<td><b style="color:var(--brass-hi)">${m >= 0 ? '+' : '−'}${Math.abs(m)}</b></td>`; }).join('')}</tr></tbody></table></div>
        ${plus2 === plus1 && !even ? '<span class="err">The +2 and the +1 go to different abilities</span>' : ''}`;
      $('#acls', el).onchange = e => { cls = e.target.value; scores = ARR[cls].slice(); draw(); };
      $('#abg', el).onchange = e => { bg = e.target.value; plus2 = BG[bg][0]; plus1 = BG[bg][2]; draw(); };
      $('#a21', el).onclick = () => { even = false; draw(); };
      $('#a111', el).onclick = () => { even = true; draw(); };
      el.querySelectorAll('[data-p]').forEach(s => s.onchange = e => { if (s.dataset.p === '0') plus2 = e.target.value; else plus1 = e.target.value; draw(); });
      el.querySelectorAll('[data-ab]').forEach(s => s.onchange = e => {
        const i = +s.dataset.ab, v = +e.target.value, j = scores.indexOf(v);
        [scores[i], scores[j]] = [v, scores[i]];
        draw();
      });
    };
    draw();
  }

  function doAdvantage(el) {
    const ADV = [['prone5', 'Target prone, you’re within 5 ft'], ['unseen', 'You’re unseen'], ['restr', 'Target is restrained']];
    const DIS = [['close', 'Ranged attack, enemy next to you'], ['blind', 'You can’t see the target'], ['pois', 'You’re poisoned']];
    const on = { unseen: true, restr: true, pois: true };
    let dice = null;
    const draw = () => {
      const a = ADV.filter(([k]) => on[k]).length, d = DIS.filter(([k]) => on[k]).length;
      const mode = a && d ? 'cancel' : a ? 'adv' : d ? 'dis' : 'normal';
      const [label, sub, color] = { cancel: ['Neither · they cancel', 'Roll one d20', 'var(--text)'], adv: ['Advantage', 'Roll two d20s, keep the higher', 'var(--brass-hi)'],
        dis: ['Disadvantage', 'Roll two d20s, keep the lower', 'var(--red)'], normal: ['Normal roll', 'Roll one d20', 'var(--text)'] }[mode];
      const keep = dice ? (mode === 'dis' ? Math.min(...dice) : Math.max(...dice)) : null;
      el.innerHTML = `<div class="cards3"><div style="display:flex;flex-direction:column;gap:6px"><span class="eyebrow" style="color:var(--brass-hi)">Advantage from</span>
        ${ADV.map(([k, l]) => `<button type="button" class="toggle ${on[k] ? 'on' : ''}" data-k="${k}" aria-pressed="${!!on[k]}"><span class="box">${on[k] ? '✓' : ''}</span>${esc(l)}</button>`).join('')}</div>
        <div style="display:flex;flex-direction:column;gap:6px"><span class="eyebrow" style="color:var(--red)">Disadvantage from</span>
        ${DIS.map(([k, l]) => `<button type="button" class="toggle dis ${on[k] ? 'on' : ''}" data-k="${k}" aria-pressed="${!!on[k]}"><span class="box">${on[k] ? '✓' : ''}</span>${esc(l)}</button>`).join('')}</div></div>
        <div class="dicebox"><div style="display:flex;flex-direction:column;gap:2px;flex:1 1 200px"><span class="serif" style="font-size:28px;color:${color}">${label}</span><span class="dim">${sub}</span></div>
          ${dice ? dice.map((v, i) => `<span class="die small ${v === keep && dice.indexOf(v) === i ? 'kept' : ''}">${v}</span>`).join('') : ''}
          <button class="btn primary" type="button" id="sbroll">${icon('d20', 18)}Roll</button></div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { on[b.dataset.k] = !on[b.dataset.k]; dice = null; draw(); });
      $('#sbroll', el).onclick = () => { dice = O.rollDice(mode === 'adv' || mode === 'dis' ? 2 : 1, 20); draw(); };
    };
    draw();
  }

  function doDM(el) {
    if (!O.ai) { el.innerHTML = `<div class="empty">${O.demo ? 'The AI Game Master is off in the demo' : 'The AI Game Master is off'}</div>`; return; }
    let id = localStorage.getItem('olam.dm') || '';
    let msgs = [];
    let busy = false;
    const ruleLine = t => {
      let s = esc(t).replace(/^\s*\*\s*$/gm, '').trim();
      let rule = '';
      s = s.replace(/\n*\**\s*Rule:\s*([\s\S]*?)\**\s*$/, (m, r) => { rule = r.trim(); return ''; });
      s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
      return s.trim() + (rule ? `<span class="rule">Rule: ${rule}</span>` : '');
    };
    const draw = () => {
      el.innerHTML = `${msgs.length ? '' : `<label class="eyebrow" for="dmchar">Your character</label>
          <input id="dmchar" style="min-height:44px;padding:0 12px;border-radius:10px;border:1px solid var(--line-2);background:var(--ground)" placeholder="Tam, a halfling rogue who owes money to the wrong people" value="${esc(localStorage.getItem('olam.dmchar') || '')}">
          <button class="btn primary" type="button" id="dmstart" style="align-self:flex-start">${busy ? '<span class="spinner"></span>' : 'Start the adventure'}</button>`}
        <div class="chat" id="chat">${msgs.map(m => m.who === 'you' ? `<div class="bubble you">${esc(m.text)}</div>` : `<div class="bubble gm"><span class="who">Game Master</span>${ruleLine(m.text)}</div>`).join('')}
          ${busy && msgs.length ? '<div class="typing"><span class="spinner"></span> The GM is thinking</div>' : ''}</div>
        ${msgs.length ? `<div class="dicetray"><span class="eyebrow">Roll</span>
            <button type="button" data-d="20">d20</button><button type="button" data-d="20a">d20 adv</button><button type="button" data-d="20d">d20 dis</button>
            ${[4, 6, 8, 10, 12].map(n => `<button type="button" data-d="${n}">d${n}</button>`).join('')}
            <input id="dmmod" type="number" value="0" aria-label="Modifier"><span id="dmres" class="dim"></span></div>
          <form class="composer" id="dmform"><textarea id="dmmsg" rows="2" placeholder="What do you do?"></textarea>
            <button class="btn primary" type="submit" aria-label="Send" ${busy ? 'disabled' : ''}>${icon('send', 18)}</button></form>
          <button class="btn small" type="button" id="dmnew" style="align-self:flex-start">New adventure</button>` : ''}`;
      const chat = $('#chat', el); if (chat) chat.scrollTop = chat.scrollHeight;
      const st = $('#dmstart', el);
      if (st) st.onclick = () => { const c = $('#dmchar', el).value.trim(); localStorage.setItem('olam.dmchar', c); send('', c); };
      const f = $('#dmform', el);
      if (f) f.onsubmit = ev => { ev.preventDefault(); const t = $('#dmmsg', el).value.trim(); if (t) send(t); };
      const nw = $('#dmnew', el);
      if (nw) nw.onclick = () => { id = ''; localStorage.removeItem('olam.dm'); msgs = []; draw(); };
      el.querySelectorAll('[data-d]').forEach(b => b.onclick = () => {
        const k = b.dataset.d, m = +($('#dmmod', el).value || 0);
        const n = parseInt(k, 10), two = /[ad]$/.test(k);
        const r = O.rollDice(two ? 2 : 1, n);
        const keep = k.endsWith('a') ? Math.max(...r) : k.endsWith('d') ? Math.min(...r) : r[0];
        const total = keep + m;
        $('#dmres', el).textContent = `${r.join(' / ')}${m ? (m > 0 ? ' + ' : ' − ') + Math.abs(m) : ''} = ${total}`;
        const ta = $('#dmmsg', el);
        ta.value = (ta.value ? ta.value + ' ' : '') + `I rolled ${total}.`;
        ta.focus();
      });
    };
    const send = async (text, character) => {
      if (busy) return;
      busy = true;
      if (text) msgs.push({ who: 'you', text });
      draw();
      try {
        const r = await api('dm', { body: { id, message: text, character: character || localStorage.getItem('olam.dmchar') || '' } });
        id = r.id; localStorage.setItem('olam.dm', id); msgs = r.messages;
      } catch (e) { msgs.push({ who: 'gm', text: e.message }); }
      busy = false;
      draw();
    };
    if (id) api('dm/' + id).then(r => { msgs = r.messages; draw(); }).catch(draw); else draw();
  }

  // ---------- Check ----------
  function drawCheck(el) {
    const ans = (L.progress && L.progress.answers) || {};
    const qs = L.check || [];
    const score = qs.filter((q, i) => ans[i] === q.correct).length;
    const done = L.progress.status === 'done';
    el.innerHTML = `<div class="cardhead"><span class="eyebrow">${qs.length} questions</span><span>${score} / ${qs.length}</span></div>
      ${qs.map((q, i) => {
        const a = ans[i];
        const answered = a !== undefined, right = a === q.correct;
        return `<div class="q ${answered ? (right ? 'right' : 'wrong') : ''}"><span style="font-size:17px">${esc(q.q)}</span>
          <div class="opts">${q.opts.map((o, j) => `<button type="button" data-q="${i}" data-j="${j}" class="${a === j ? (right ? 'good' : 'bad') : ''}" aria-pressed="${a === j}">${esc(o)}</button>`).join('')}</div>
          ${answered ? `<div class="chips" style="align-items:center"><b style="color:${right ? 'var(--brass-hi)' : 'var(--red)'}">${right ? 'Correct' : 'Not quite'}</b>
            <span style="flex:1 1 240px;color:var(--text-2)">${esc(q.why)}</span>${q.src ? `<a href="#/wiki/${encodeURIComponent(q.src)}" style="text-decoration:none">${badge('rule', q.src_label || 'Rule')}</a>` : ''}
            ${right ? '' : `<span class="chip brass" style="font-size:12px">${icon('review', 12)}In review</span>`}</div>` : ''}</div>`;
      }).join('')}
      ${done ? `<div class="done"><div style="display:flex;flex-direction:column;gap:2px;flex:1 1 220px"><b>Stop ${L.n} complete</b>
          <span class="dim">${S.stops[L.n] ? 'Next · ' + esc(S.stops[L.n].title) : ''}</span></div>
          ${O.demo ? '' : `<button class="btn primary" type="button" id="note">${icon('pen', 18)}Write it in your words</button><span id="notepath" class="mono dim" style="flex-basis:100%"></span>`}</div>` : ''}`;
    el.querySelectorAll('[data-q]').forEach(b => b.onclick = async () => {
      const i = +b.dataset.q, j = +b.dataset.j;
      const before = L.progress.status === 'done';
      ans[i] = j;
      L.progress.answers = ans;
      if (O.demo) {
        localUpdate(p => {
          p.answers[i] = j;
          p.status = qs.every((q, k) => p.answers[k] === q.correct) ? 'done' : (p.status || 'started');
        });
        if (j !== qs[i].correct) { const rv = O.local.review(); const k = `${L.id}:${i}`; if (!rv.includes(k)) O.local.setReview(rv.concat([k])); }
        S = await loadState();
      } else S = await api(`learn/${L.id}/answer`, { body: { qi: i, choice: j } });
      const wasDone = before;
      L.progress.status = S.stops.find(s => s.id === L.id).status === 'done' ? 'done' : L.progress.status;
      O.setReviewCount(S.review);
      if (!wasDone && L.progress.status === 'done') refreshAll(); else { drawCheck(el); drawHead(); }
    });
    const nb = $('#note', el);
    if (nb) nb.onclick = async () => {
      try { const r = await api('note', { body: { stop: L.id } }); $('#notepath', el).innerHTML = `${esc(r.vault)} / ${esc(r.path)} · <a href="obsidian://open?vault=${encodeURIComponent(r.vault)}&file=${encodeURIComponent(r.path)}">Open in Obsidian</a>`; }
      catch (e) { $('#notepath', el).textContent = e.message; }
    };
  }

  function refreshAll() {
    drawHead(); drawRoad(); drawStopbar(); drawAtlas(); drawLesson();
  }

  // ---------- Atlas ----------
  const PLACES = [['srd-2024/glossary/ability-check', 238, 205, 'Ability checks'], ['srd-2024/glossary/saving-throw', 388, 205, 'Saving throws'],
    ['srd-2024/glossary/attack-roll', 244, 262, 'Attack rolls'], ['srd-2024/glossary/proficiency', 382, 262, 'Proficiency'],
    ['srd-2024/glossary/advantage', 312, 240, 'Advantage'], ['srd-2024/glossary/initiative', 222, 334, 'Initiative'], ['srd-2024/glossary/cover', 288, 346, 'Cover']];
  const FOG = { peaks: [305, 100, 250, 62], court: [118, 255, 82, 112], heart: [312, 222, 128, 72], wilds: [500, 258, 64, 112], combat: [252, 340, 72, 50], fen: [382, 340, 64, 50] };
  const CONT = 'M 80 120 C 120 60 220 40 300 50 C 380 40 480 60 530 110 C 575 155 560 230 540 280 C 520 340 450 380 370 385 C 300 392 230 380 170 360 C 110 340 60 300 50 240 C 42 190 50 150 80 120 Z';
  function drawAtlas() {
    const known = new Set(S.regions.flatMap(g => g.rules.filter(r => r.known).map(r => r.id)));
    const teaching = new Set(S.teaching);
    const base = `<svg viewBox="0 0 600 420" aria-hidden="true"><defs>
      <pattern id="awaves" width="40" height="16" patternUnits="userSpaceOnUse"><path d="M0 8 q10 -5 20 0 t20 0" fill="none" stroke="rgba(201,165,90,.12)"/></pattern>
      <filter id="afog" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>
      <g id="apk"><path d="M-12 8 L0 -10 L12 8 Z" fill="#1B1F26"/><path d="M-12 8 L0 -10 L12 8" fill="none" stroke="#C9A55A" stroke-width="1.3" stroke-linejoin="round"/></g>
      <g id="atr"><circle r="5" fill="none" stroke="#9BAE7A" stroke-width="1.2"/><path d="M0 5 V9" stroke="#9BAE7A" stroke-width="1.2"/></g>
      <g id="afn"><path d="M-6 0 H6 M-3 0 L-4 -5 M0 0 V-7 M3 0 L4 -5" fill="none" stroke="#7FA39A" stroke-width="1.2" stroke-linecap="round"/></g></defs>
      <rect width="600" height="420" fill="#0F1216"/><rect width="600" height="420" fill="url(#awaves)"/>
      <path d="${CONT}" fill="none" stroke="rgba(201,165,90,.14)" stroke-width="16"/><path d="${CONT}" fill="#1B1F26" stroke="#C9A55A" stroke-width="1.6"/>
      <g fill="none" stroke="#8A6A2F" stroke-width="1.2" stroke-dasharray="4 5"><path d="M 64 150 C 160 162 250 138 320 152 C 390 166 470 142 556 156"/><path d="M 192 152 C 178 210 200 262 178 360"/>
        <path d="M 434 154 C 448 210 426 250 446 296 C 456 330 462 350 470 372"/><path d="M 186 292 C 250 282 330 302 446 292"/><path d="M 318 297 C 312 330 326 360 320 390"/></g>
      ${[[130, 112], [165, 96], [200, 114], [240, 92], [280, 110], [330, 88], [372, 106], [412, 92], [452, 112], [490, 100]].map(([x, y]) => `<use href="#apk" x="${x}" y="${y}"/>`).join('')}
      ${[[470, 190], [492, 206], [515, 188], [480, 226], [508, 232], [530, 214], [470, 300], [494, 312], [518, 296]].map(([x, y]) => `<use href="#atr" x="${x}" y="${y}"/>`).join('')}
      ${[[345, 368], [365, 356], [392, 370], [412, 354], [378, 378], [428, 368]].map(([x, y]) => `<use href="#afn" x="${x}" y="${y}"/>`).join('')}
      <path d="M102 316 V290 H118 V316 M100 290 H120 M104 290 V284 M110 290 V284 M116 290 V284" fill="none" stroke="#C9A55A" stroke-width="1.4"/>
      <g style="font-family:var(--sans);font-size:12px;fill:#D3CCBC" text-anchor="middle">${PLACES.map(([id, x, y, l]) => {
        const k = known.has(id), t = teaching.has(id);
        return `<circle cx="${x}" cy="${y}" r="4.5" fill="${k ? '#D9A54A' : '#1B1F26'}" stroke="${k ? 'none' : (t ? '#D9A54A' : '#8A6A2F')}" stroke-width="1.5"/>` +
          (t && !k ? `<circle cx="${x}" cy="${y}" r="6" fill="none" stroke="#D9A54A" stroke-width="1.2"><animate attributeName="r" values="6;13;6" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values=".9;0;.9" dur="1.8s" repeatCount="indefinite"/></circle>` : '') +
          `<text x="${x}" y="${y + 16}" style="fill:${t && !k ? '#ECC277' : '#D3CCBC'}">${l}</text>`;
      }).join('')}</g></svg>`;
    const fog = S.regions.map(g => {
      const [cx, cy, rx, ry] = FOG[g.id];
      const op = Math.max(0.05, 0.92 - g.known / g.total);
      return `<div class="fog" style="opacity:${op.toFixed(2)}"><svg viewBox="0 0 600 420" aria-hidden="true"><ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#0B0D10" filter="url(#afog)"/></svg></div>`;
    }).join('');
    const labels = `<svg viewBox="0 0 600 420" aria-hidden="true" style="pointer-events:none"><g style="font-family:var(--serif);fill:#D9A54A;letter-spacing:1px" text-anchor="middle">
      <text x="305" y="142" font-size="16">Spell Peaks</text><text x="312" y="182" font-size="17">The D20 Heartland</text><text x="118" y="236" font-size="16">Court of</text>
      <text x="118" y="254" font-size="16">Tongues</text><text x="500" y="266" font-size="16">The Wilds</text><text x="252" y="316" font-size="15">Combat Coast</text>
      <text x="382" y="324" font-size="15">Conditions Fen</text></g></svg>`;
    const g = S.regions.find(x => x.id === region) || S.regions[0];
    $('#atlas').innerHTML = `<div class="cardhead"><h2>Atlas of Rules</h2><span class="dim">${S.mastered} of ${S.total}</span></div>
      <div class="atlas">${base}${fog}${labels}</div>
      <div class="regions">${S.regions.map(x => `<button type="button" data-region="${x.id}" class="${x.id === region ? 'on' : ''}" aria-pressed="${x.id === region}">
        <span style="display:flex;justify-content:space-between;gap:8px;font-size:14px"><span>${esc(x.short)}</span><span class="dim">${x.known} / ${x.total}</span></span>
        <span class="bar"><i style="width:${Math.round(100 * x.known / x.total)}%"></i></span></button>`).join('')}</div>
      <div class="chips">${g.rules.map(r => `<a class="chip ${r.known ? 'brass' : ''}" href="#/wiki/${encodeURIComponent(r.id)}" ${teaching.has(r.id) && !r.known ? 'style="border-style:dashed;border-color:var(--brass);color:var(--text)"' : ''}>${r.known ? '✓ ' : ''}${esc(r.name)}</a>`).join('')}</div>`;
    $('#atlas').querySelectorAll('[data-region]').forEach(b => b.onclick = () => { region = b.dataset.region; drawAtlas(); });
  }
})();
