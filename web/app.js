// Olam: the shell, the router, and the library pages (Codex, wiki hubs, Ask, Review). Learn lives in learn.js.
'use strict';

const O = window.O = {};
const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
O.esc = esc;

// ---------- api ----------
O.api = async (path, opts = {}) => {
  const r = await fetch('api/' + path, {
    method: opts.body ? 'POST' : (opts.method || 'GET'),
    headers: opts.body ? { 'Content-Type': 'application/json' } : {},
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: 'same-origin',
  });
  if (r.status === 401 && path !== 'login') { O.showLogin(); throw new Error('Sign in first'); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || j.error || r.statusText);
  return j;
};

// ---------- icons ----------
const I = O.I = {
  learn: '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
  codex: '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',
  ask: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
  review: '<path d="M12 21v-8"/><path d="M12 13c0-4 3-7 8-7 0 5-3 7-8 7z"/><path d="M12 15c0-3-2-5-6-5 0 3 2 5 6 5z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  d20: '<path d="M12 2 21 7v10l-9 5-9-5V7z"/><path d="M12 2 7.5 14h9L12 2zM3 7l4.5 7M21 7l-4.5 7M7.5 14 12 22l4.5-8"/>',
  out: '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
  check: '<path d="m5 12 5 5 9-10"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  send: '<path d="M4 12 20 4l-6 16-3-7-7-1z"/>',
  pen: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  map: '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
  people: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
  table: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
};
const icon = O.icon = (name, size = 20, stroke = 'currentColor') =>
  `<svg aria-hidden="true" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" style="stroke:${stroke}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${I[name]}</svg>`;

// ---------- pictures and game icons ----------
// Game icons (game-icons.net, CC BY 3.0) from the sprite; pictures (Wikipedia/Commons) come with their credit.
const gi = O.gi = (name, size = 24) => `<svg class="gi" aria-hidden="true" width="${size}" height="${size}"><use href="static/icons.svg#gi-${name || 'open-book'}"/></svg>`;
const DIE = { 4: 'd4', 6: 'perspective-dice-six', 8: 'dice-eight-faces-eight', 10: 'd10', 12: 'd12', 20: 'dice-twenty-faces-twenty' };
O.die = (sides, size = 18) => gi(DIE[sides] || 'rolling-dices', size);
O.credit = p => `${esc(p.author)} · ${p.license_url ? `<a href="${esc(p.license_url)}" target="_blank" rel="noopener">${esc(p.license)}</a>` : esc(p.license)} · <a href="${esc(p.source)}" target="_blank" rel="noopener">Commons</a>`;
O.thumb = (e, cls = '') => e && e.pic
  ? `<img class="thumb ${cls}" src="${esc(e.pic.src || e.pic)}" alt="" loading="lazy"${e.pic.author ? ` title="${esc(e.pic.author + ' · ' + e.pic.license)}"` : ''}>`
  : `<span class="thumb ico ${cls}">${gi(e && e.icon, cls.includes('big') ? 34 : 22)}</span>`;

// ---------- trust badges ----------
const SHELF = { rule: 'Rule', third: '3rd-party', expert: 'Expert', craft: 'Craft', idea: 'Idea', yours: 'Yours', summary: 'Summary' };
O.badge = (shelf, label) => `<span class="badge b-${esc(shelf)}">${esc(label || SHELF[shelf] || shelf)}</span>`;

// ---------- markdown, with rules terms linked ----------
O.terms = [];
let termRe = null, termMap = {};
const SKIP = new Set(['Action', 'Attack', 'Creature', 'Object', 'Spell', 'Target', 'Size', 'Damage', 'Magic', 'Monster', 'Weapon', 'Enemy',
  'Ally', 'Save', 'Adventure', 'Campaign', 'Encounter', 'Player Character', 'Nonplayer Character', 'Per Day', 'Round Down', 'Possession',
  'Hazard', 'Curses', 'Illusions', 'Condition', 'Stat Block', 'Skill', 'Proficiency', 'Speed', 'Reach', 'Ritual', 'Healing', 'Telepathy',
  'Teleportation', 'Dead', 'Stable', 'Swimming', 'Climbing', 'Flying', 'Jumping', 'Crawling', 'Search', 'Study', 'Ready', 'Help', 'Magic',
  'Utilize', 'Influence', 'Hide', 'Dash', 'Dodge', 'Disengage', 'Expertise', 'Darkness', 'Burning', 'Falling', 'Shape-Shifting', 'Line',
  'Cone', 'Cube', 'Sphere', 'Cylinder', 'Emanation', 'Hover', 'Friendly', 'Hostile', 'Indifferent']);
O.setTerms = list => {
  O.terms = list.filter(t => !SKIP.has(t.name));
  termMap = Object.fromEntries(O.terms.map(t => [t.name, t]));
  const names = O.terms.map(t => t.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  termRe = names.length ? new RegExp('\\b(' + names.join('|') + ')\\b', 'g') : null;
};

function inline(s) {
  return s
    .replace(/\[\[(.+?)\]\]/g, '<mark>$1</mark>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*\w])\*(?!\s)(.+?)\*(?!\w)/g, '$1<em>$2</em>');
}

O.md = (text, opts = {}) => {
  if (!text) return '';
  const lines = esc(text).replace(/\r/g, '').split('\n');
  const out = [];
  let i = 0;
  while (i < lines.length) {
    let l = lines[i];
    if (!l.trim()) { i++; continue; }
    if (/^\s*\|/.test(l)) {
      const rows = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) rows.push(lines[i++]);
      const cells = r => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
      const body = rows.filter(r => !/^\s*\|[\s:|-]+\|\s*$/.test(r));
      const head = cells(body.shift() || '');
      out.push('<table><thead><tr>' + head.map(c => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>' +
        body.map(r => '<tr>' + cells(r).map(c => `<td>${inline(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table>');
      continue;
    }
    let m;
    if ((m = l.match(/^(#{1,4})\s+(.*)/))) { out.push(`<h3>${inline(m[2])}</h3>`); i++; continue; }
    if (/^Table:\s/.test(l)) { out.push(`<p class="dim">${inline(l.replace(/^Table:\s*/, ''))}</p>`); i++; continue; }
    if (/^&gt;\s?/.test(l)) {
      const q = [];
      while (i < lines.length && /^&gt;\s?/.test(lines[i])) q.push(lines[i++].replace(/^&gt;\s?/, ''));
      out.push('<blockquote>' + q.map(x => `<p>${inline(x)}</p>`).join('') + '</blockquote>');
      continue;
    }
    if (/^\s*([*-]|\d+\.)\s+/.test(l)) {
      const ordered = /^\s*\d+\./.test(l);
      const items = [];
      while (i < lines.length && /^\s*([*-]|\d+\.)\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*([*-]|\d+\.)\s+/, ''));
      out.push(`<${ordered ? 'ol' : 'ul'}>` + items.map(x => `<li>${inline(x)}</li>`).join('') + `</${ordered ? 'ol' : 'ul'}>`);
      continue;
    }
    const para = [];
    while (i < lines.length && lines[i].trim() && !/^\s*(\||#{1,4}\s|&gt;|[*-]\s|\d+\.\s)/.test(lines[i])) para.push(lines[i++]);
    if (!para.length) { para.push(lines[i++]); }
    out.push(`<p>${inline(para.join(' '))}</p>`);
  }
  let html = out.join('');
  if (opts.link !== false) html = O.linkTerms(html, opts.self);
  return html;
};

O.linkTerms = (html, self) => {
  if (!termRe) return html;
  const seen = new Set();
  let inA = 0;
  return html.split(/(<[^>]+>)/).map(seg => {
    if (seg.startsWith('<')) { if (/^<a\b/.test(seg)) inA++; else if (/^<\/a>/.test(seg)) inA--; return seg; }
    if (inA) return seg;
    return seg.replace(termRe, (w) => {
      const t = termMap[w];
      if (!t || seen.has(w) || t.id === self) return w;
      seen.add(w);
      return `<a class="term" href="#/wiki/${encodeURIComponent(t.id)}" data-term="${esc(t.id)}">${w}</a>`;
    });
  }).join('');
};

// hover previews for linked terms
const previewCache = {};
let previewTimer;
document.addEventListener('mouseover', e => {
  const a = e.target.closest('[data-term]');
  const box = $('#preview');
  if (!a) { clearTimeout(previewTimer); box.classList.add('hidden'); return; }
  clearTimeout(previewTimer);
  previewTimer = setTimeout(async () => {
    const id = a.dataset.term;
    const ent = previewCache[id] || (previewCache[id] = await O.api('entry/' + id).catch(() => null));
    if (!ent || !document.body.contains(a)) return;
    const r = a.getBoundingClientRect();
    const text = (ent.body || '').replace(/[*#|>]/g, '').replace(/\s+/g, ' ').slice(0, 300);
    box.innerHTML = `<b>${esc(ent.name)}</b>${esc(text)}${ent.body && ent.body.length > 300 ? '…' : ''}`;
    box.style.left = Math.min(r.left, innerWidth - 380) + 'px';
    box.style.top = (r.bottom + 8 + 220 > innerHeight ? r.top - 8 - box.offsetHeight : r.bottom + 8) + 'px';
    box.classList.remove('hidden');
  }, 250);
});

// ---------- dice ----------
O.rollDice = (n, d) => Array.from({ length: n }, () => 1 + Math.floor(Math.random() * d));
O.toast = (total, label, detail) => {
  const log = $('#rolllog');
  const el = document.createElement('div');
  el.className = 'rolltoast';
  const sides = Number((String(detail).match(/d(\d+)/) || [])[1]) || 20;
  el.innerHTML = `${O.die(sides, 30)}<b>${esc(total)}</b><span>${esc(label)}<small>${esc(detail)}</small></span>`;
  log.prepend(el);
  setTimeout(() => el.remove(), 7000);
  while (log.children.length > 4) log.lastChild.remove();
};
document.addEventListener('click', e => {
  const b = e.target.closest('[data-roll]');
  if (!b) return;
  const [kind, a1, a2] = b.dataset.roll.split('|');
  if (kind === 'hit') {
    const r = O.rollDice(1, 20)[0], mod = +a1;
    O.toast(r + mod, a2 + ' · to hit', `d20 ${r} ${mod >= 0 ? '+' : '−'} ${Math.abs(mod)}${r === 20 ? ' · Critical Hit' : r === 1 ? ' · a 1 always misses' : ''}`);
  } else if (kind === 'dmg') {
    const m = a1.match(/^(\d+)d(\d+)\s*([+-]\s*\d+)?$/);
    if (!m) return;
    const rs = O.rollDice(+m[1], +m[2]), mod = m[3] ? +m[3].replace(/\s/g, '') : 0;
    O.toast(rs.reduce((x, y) => x + y, 0) + mod, a2 + ' · damage', `${m[1]}d${m[2]} [${rs.join(', ')}]${mod ? (mod > 0 ? ' + ' : ' − ') + Math.abs(mod) : ''}`);
  }
});

// ---------- stat blocks and headers ----------
const sign = n => (n >= 0 ? '+' : '−') + Math.abs(n);
const mod = s => Math.floor((s - 10) / 2);
O.statblock = (e) => {
  const d = e.data || {};
  const sp = Object.entries(d.speed || {}).map(([k, v]) => k === 'walk' ? `${v} ft.` : `${k[0].toUpperCase() + k.slice(1)} ${v} ft.`).join(', ') + (d.hover ? ' (hover)' : '');
  const abil = (d.abilities || []).map(a => `<div><b>${a.k}</b>${a.score} (${sign(mod(a.score))})${a.save != null && a.save !== mod(a.score) ? `<br><small>save ${sign(a.save)}</small>` : ''}</div>`).join('');
  const lines = [];
  const skills = Object.entries(d.skills || {}).map(([k, v]) => `${k} ${sign(v)}`).join(', ');
  if (skills) lines.push(['Skills', skills]);
  if (d.vulnerable) lines.push(['Vulnerabilities', d.vulnerable]);
  if (d.resist) lines.push(['Resistances', d.resist]);
  if (d.immune) lines.push(['Immunities', d.immune + (d.cond_immune ? '; ' + d.cond_immune : '')]);
  else if (d.cond_immune) lines.push(['Condition Immunities', d.cond_immune]);
  if (d.senses) lines.push(['Senses', d.senses]);
  lines.push(['Languages', d.languages || '—']);
  lines.push(['CR', d.cr + (d.xp ? ` (XP ${d.xp.toLocaleString()})` : '')]);
  const groups = { ACTION: 'Actions', BONUS_ACTION: 'Bonus Actions', REACTION: 'Reactions', LEGENDARY_ACTION: 'Legendary Actions', LAIR_ACTION: 'Lair Actions' };
  const acts = Object.entries(groups).map(([k, label]) => {
    const list = (d.actions || []).filter(a => (a.type || 'ACTION') === k);
    if (!list.length) return '';
    return `<h3>${label}</h3>` + list.map(a => {
      const rolls = (a.attacks || []).map(t => {
        const dmg = t.dice ? `${t.dice}${t.bonus ? (t.bonus > 0 ? ' + ' : ' − ') + Math.abs(t.bonus) : ''}` : '';
        return (t.to_hit != null ? `<button class="roll" data-roll="hit|${t.to_hit}|${esc(e.name + ' · ' + a.name)}">${O.die(20, 18)}${sign(t.to_hit)} to hit</button>` : '') +
          (dmg ? `<button class="roll" data-roll="dmg|${esc(dmg.replace(/\s/g, ''))}|${esc(e.name + ' · ' + a.name)}">${O.die(Number((dmg.match(/d(\d+)/) || [])[1]), 18)}${esc(dmg)} ${esc(t.type || '')}</button>` : '');
      }).join('');
      return `<div><p><b><i>${esc(a.name)}${a.cost > 1 ? ` (Costs ${a.cost} Actions)` : ''}.</i></b> ${O.linkTerms(esc(a.desc), e.id)}</p>${rolls ? `<div>${rolls}</div>` : ''}</div>`;
    }).join('');
  }).join('');
  return `<div class="parch">
    <div class="cardhead"><h2>${esc(e.name)}</h2><span style="font-size:13px;color:var(--parch-mid)">${esc(e.doc_name || '')}</span></div>
    <span class="sub">${esc(d.size)} ${esc(d.type)}, ${esc(d.alignment)}</span>
    <div class="rule"></div>
    <div><b class="k">AC</b> ${esc(d.ac)}${d.ac_detail ? ` (${esc(d.ac_detail)})` : ''}${d.initiative != null ? ` &nbsp; <b class="k">Initiative</b> ${sign(d.initiative)} (${10 + d.initiative})` : ''}</div>
    <div><b class="k">HP</b> ${esc(d.hp)}${d.hit_dice ? ` (${esc(d.hit_dice)})` : ''}</div>
    <div><b class="k">Speed</b> ${esc(sp)}</div>
    <div class="rule thin"></div>
    <div class="abil">${abil}</div>
    <div class="rule thin"></div>
    ${lines.map(([k, v]) => `<div><b class="k">${k}</b> ${O.linkTerms(esc(v), e.id)}</div>`).join('')}
    ${(d.traits || []).length ? '<h3>Traits</h3>' + d.traits.map(t => `<p><b><i>${esc(t.name)}.</i></b> ${O.linkTerms(esc(t.desc), e.id)}</p>`).join('') : ''}
    ${acts}
  </div>`;
};

O.entryBlock = (e) => {
  if (e.kind === 'monster') return O.statblock(e);
  const d = e.data || {};
  let head = '';
  if (e.kind === 'spell') {
    head = `<span class="sub">${esc(d.head)}</span><div class="rule"></div>
      <div><b class="k">Casting Time</b> ${esc(d.casting_time)}</div><div><b class="k">Range</b> ${esc(d.range)}</div>
      <div><b class="k">Components</b> ${esc(d.components)}</div><div><b class="k">Duration</b> ${d.concentration ? 'Concentration, ' : ''}${esc(d.duration)}</div>
      ${(d.classes || []).length ? `<div><b class="k">Classes</b> ${esc(d.classes.join(', '))}</div>` : ''}<div class="rule thin"></div>`;
  } else if (e.kind === 'magic-item') {
    head = `<span class="sub">${esc(d.head || e.summary)}</span><div class="rule"></div>`;
  } else if (e.kind === 'item') {
    const bits = [d.category, d.weapon ? `Damage ${d.weapon.damage}` : '', d.armor ? `AC ${d.armor.ac}${d.armor.dex ? ' + Dex' + (d.armor.cap ? ` (max ${d.armor.cap})` : '') : ''}` : '',
      d.cost && +d.cost ? `${(+d.cost).toLocaleString()} GP` : '', d.weight && +d.weight ? `${+d.weight} lb.` : ''].filter(Boolean);
    head = `<span class="sub">${esc(bits.join(' · '))}</span><div class="rule"></div>`;
  } else {
    head = `<span class="sub">${esc(e.summary || e.kind_label)}${e.grp && !(e.summary || '').includes(e.grp) ? ' · ' + esc(e.grp) : ''}</span><div class="rule"></div>`;
  }
  return `<div class="parch"><div class="cardhead"><h2>${esc(e.name)}</h2><span style="font-size:13px;color:var(--parch-mid)">${esc(e.doc_name || '')}</span></div>${head}<div class="prose">${O.md(e.body, { self: e.id })}</div></div>`;
};

// ---------- shell ----------
const NAV = [['learn', 'Learn', '#/learn'], ['map', 'Map', '#/map'], ['codex', 'Codex', '#/codex'], ['people', 'People', '#/people'],
  ['table', 'Table', '#/table'], ['ask', 'Ask', '#/ask'], ['review', 'Review', '#/review'], ['settings', 'Settings', '#/settings']];
const DEMO_HIDE = new Set(['ask', 'map', 'people', 'table', 'settings']);
O.state = { stats: null, review: 0 };
O.demo = false;
O.ai = false;

// The demo keeps each visitor's progress in their own browser; your own copy keeps it on the server.
O.local = {
  read(k, d) { try { return JSON.parse(localStorage.getItem(k) || '') ?? d; } catch (e) { return d; } },
  write(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private window */ } },
  progress() { return O.local.read('olam.progress', {}) || {}; },
  setProgress(p) { O.local.write('olam.progress', p); },
  review() { return O.local.read('olam.review', []) || []; },
  setReview(r) { O.local.write('olam.review', r); },
};
// Kiwix is linked only when Olam is opened on Kiwix's own host name, where its address works.
const kiwixHere = url => { try { return !!url && new URL(url).hostname === location.hostname; } catch (e) { return false; } };

function shell(active) {
  if (!$('.shell')) {
    const nav = NAV.filter(([k]) => !(O.demo && DEMO_HIDE.has(k)) && !(k === 'ask' && !O.ai));
    $('#app').innerHTML = `<div class="shell"><nav class="rail" aria-label="Olam">
      <a class="brand" href="#/learn"><b>Olam</b><span lang="he" dir="rtl">עולם</span></a>
      <div class="nav">${nav.map(([k, label, href]) => `<a href="${href}" data-nav="${k}">${icon(k)}<span>${label}</span>${k === 'review' ? '<span class="count hidden" id="revcount"></span>' : ''}</a>`).join('')}</div>
      <div class="railfoot" id="railfoot"></div></nav><main class="main" id="main"></main></div>`;
    loadFoot();
  }
  document.querySelectorAll('[data-nav]').forEach(a => a.classList.toggle('on', a.dataset.nav === active));
  if (active) document.querySelector(`[data-nav="${active}"]`)?.setAttribute('aria-current', 'page');
  return $('#main');
}
async function loadFoot() {
  try {
    const s = O.state.stats || (O.state.stats = await O.api('stats'));
    $('#railfoot').innerHTML = `${O.demo ? '<div><span>Demo</span><span>open-licensed</span></div>' : ''}
      <div><span>Library</span><span>${Math.round(s.pages / 1000)}k pages</span></div>
      <div><span>Rules</span><span>2024 · SRD 5.2</span></div><div><span>Archives</span><span>${Object.keys(s.archives).length} · Kiwix</span></div>
      <div><a href="#/credits">Credits &amp; licenses</a></div>`;
  } catch (e) { /* signed out */ }
}
O.setReviewCount = n => { const c = $('#revcount'); if (c) { c.textContent = n; c.classList.toggle('hidden', !n); } };

O.showLogin = () => {
  $('#app').innerHTML = `<div class="login"><form id="loginform">
    <div class="brand" style="padding:0"><b>Olam</b><span lang="he" dir="rtl">עולם</span></div>
    <label for="pw" class="eyebrow">Password</label>
    <input id="pw" type="password" autocomplete="current-password" required autofocus>
    <div class="err" id="loginerr"></div>
    <button class="btn primary" type="submit">Sign in</button></form></div>`;
  $('#loginform').onsubmit = async ev => {
    ev.preventDefault();
    try { await O.api('login', { body: { password: $('#pw').value } }); $('#app').innerHTML = ''; start(); }
    catch (e) { $('#loginerr').textContent = e.message; }
  };
};

// ---------- router ----------
O.routes = {};
O.go = h => { location.hash = h; };
function parse() {
  const h = location.hash.replace(/^#\/?/, '') || 'learn';
  const [path, qs] = h.split('?');
  const parts = path.split('/').map(decodeURIComponent);
  return { name: parts[0], rest: parts.slice(1).join('/'), q: new URLSearchParams(qs || '') };
}
async function route() {
  const r = parse();
  const fn = O.routes[r.name] || O.routes.learn;
  const nav = { wiki: 'codex', read: 'codex' }[r.name] || r.name;
  const main = shell(NAV.some(n => n[0] === nav) ? nav : 'learn');
  $('#preview').classList.add('hidden');
  document.body.classList.toggle('tv', r.name === 'table' && r.rest === 'players');
  try { await fn(main, r); }
  catch (e) { if (e.message !== 'Sign in first') main.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}
window.addEventListener('hashchange', () => { route(); window.scrollTo(0, 0); });

async function start() {
  const me = await fetch('api/me').then(r => r.json());
  O.demo = !!me.demo;
  O.ai = !!me.ai;
  if (!me.signed_in) return O.showLogin();
  O.setTerms(await O.api('terms'));
  route();
  if (!O.demo) O.api('vault').then(v => { O.vaultName = (v.vault || '').split('/').pop() || 'Olam'; }).catch(() => {});
  if (O.demo) O.setReviewCount(O.local.review().length);
  else O.api('learn').then(s => O.setReviewCount(s.review)).catch(() => {});
}

// ---------- Codex ----------
const KINDS_ALL = [['', 'All'], ['glossary,rule,condition', 'Rules'], ['monster', 'Monsters'], ['spell', 'Spells'], ['magic-item', 'Magic items'],
  ['item', 'Equipment'], ['class', 'Classes'], ['species,background,feat', 'Origins & feats'], ['book', 'Your library']];
const EDITIONS = [['2024', '2024'], ['2014', '2014'], ['', 'Every edition']];
O.routes.codex = async (main, r) => {
  const KINDS = KINDS_ALL.filter(([k]) => !(O.demo && k === 'book'));
  const q = r.q.get('q') || '';
  const kind = r.q.get('kind') || '';
  const ed = r.q.has('ed') ? r.q.get('ed') : '2024';
  const third = r.q.get('third') === '1';
  main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">Library</span><h1>Codex</h1></div>
    <div class="seg" role="group" aria-label="Edition">${EDITIONS.map(([k, l]) => `<button type="button" data-ed="${k}" class="${k === ed ? 'on' : ''}" aria-pressed="${k === ed}">${l}</button>`).join('')}</div></header>
    <form class="searchbar" id="sform">${icon('search', 20, 'var(--dim)')}<input type="search" id="sq" aria-label="Search the library" placeholder="Owlbear, grappling, fireball, the Menagerie" value="${esc(q)}" autofocus><span class="dim" id="scount"></span></form>
    <div class="row"><div class="facets" role="group" aria-label="Type">
      <span class="eyebrow">Type</span>
      ${KINDS.map(([k, l]) => `<button type="button" data-kind="${k}" class="${k === kind ? 'on' : ''}" aria-pressed="${k === kind}">${l}</button>`).join('')}
      <span class="eyebrow" style="margin-top:10px">Sources</span>
      <button type="button" id="third" class="${third ? 'on' : ''}" aria-pressed="${third}"><span>3rd-party books</span>${O.badge('third')}</button>
    </div>
    <div class="results" id="results">${q ? '<span class="spinner"></span>' : ''}</div>
    <div class="archives" id="archives"></div></div>`;
  const nav = (o) => {
    const p = new URLSearchParams({ q: o.q ?? q });
    if ((o.kind ?? kind)) p.set('kind', o.kind ?? kind);
    p.set('ed', o.ed ?? ed);
    if (o.third ?? third) p.set('third', '1');
    O.go('#/codex?' + p.toString());
  };
  $('#sform').onsubmit = ev => { ev.preventDefault(); nav({ q: $('#sq').value.trim() }); };
  main.querySelectorAll('[data-kind]').forEach(b => b.onclick = () => nav({ kind: b.dataset.kind }));
  main.querySelectorAll('[data-ed]').forEach(b => b.onclick = () => nav({ ed: b.dataset.ed }));
  $('#third').onclick = () => nav({ third: !third });
  if (!q) {
    $('#results').innerHTML = browseHTML();
    return;
  }
  const shelves = third ? '' : (kind === 'book' ? '' : 'rule,idea');
  const res = await O.api(`search?q=${encodeURIComponent(q)}&kind=${kind}&edition=${ed}&shelf=${shelves}&limit=60`);
  $('#scount').textContent = res.results.length ? `${res.results.length}${res.results.length >= 60 ? '+' : ''} found` : '';
  $('#results').innerHTML = res.results.length ? res.results.map(resultHTML).join('') : '<div class="empty">No matches</div>';
  const arc = await O.api(`archives?q=${encodeURIComponent(q)}&n=4`);
  $('#archives').innerHTML = arc.archives.filter(a => a.total).map(a => `<section class="card" style="padding:14px 16px">
      <div class="cardhead"><span style="font-weight:700">${esc(a.label)}</span><span class="chips">${O.badge(a.shelf)}<span class="dim" style="font-size:13px">${a.total.toLocaleString()}</span></span></div>
      ${a.pages.map(p => zimLine(p)).join('')}</section>`).join('') || '';
};
function browseHTML() {
  const links = [['monster', 'Monsters', 'dragon-head'], ['spell', 'Spells', 'magic-swirl'], ['magic-item', 'Magic items', 'crystal-ball'], ['item', 'Equipment', 'battle-axe'],
    ['class', 'Classes', 'wizard-staff'], ['species', 'Species', 'elf-ear'], ['background', 'Backgrounds', 'scroll-unfurled'], ['feat', 'Feats', 'laurels-trophy'],
    ['condition', 'Conditions', 'knocked-out-stars'], ['glossary', 'Rules Glossary', 'spell-book']];
  return `<div class="grid2">${links.map(([k, l, g]) => `<a class="tile itile" href="#/browse/${k}"><span class="thumb ico">${gi(g, 26)}</span><span>${esc(l)}<span class="dim" style="font-size:13px;display:block">SRD 5.2</span></span></a>`).join('')}
    <a class="tile itile" href="#/wiki/srd-2024%2Fmonster%2Fowlbear"><span class="thumb ico">${gi('griffin-symbol', 26)}</span><span>Owlbear<span class="dim" style="font-size:13px;display:block">A wiki page to start with</span></span></a></div>`;
}
function resultHTML(e) {
  const ed = e.edition && e.edition !== '2024' ? `<span class="chip" style="padding:1px 8px;font-size:12px">${esc(e.edition)}</span>` : '';
  const sub = e.kind === 'book' ? `${esc(e.summary || '')} · ${esc(e.grp || '')}` : `${esc(e.kind_label)} · ${esc(e.summary || '')}`;
  return `<a class="result rthumb" href="#/wiki/${encodeURIComponent(e.id)}">${O.thumb(e)}<span class="rb"><span class="t">${esc(e.name)} ${O.badge(e.shelf)}${ed}${e.private ? O.badge('private', 'Private') : ''}</span>
    <span class="s">${sub} · ${esc(e.doc)}</span>${e.snippet && e.kind === 'book' ? `<span class="snip">${O.esc(e.snippet).replace(/\[\[(.+?)\]\]/g, '<mark>$1</mark>')}</span>` : ''}</span></a>`;
}
function zimLine(p) {
  const meta = p.votes != null ? `${p.votes} votes · ${p.answers} answers${p.tags?.length ? ' · ' + p.tags.slice(0, 2).join(', ') : ''}` : (p.note || '');
  return `<a class="thread" href="#/read/${encodeURIComponent(p.zim)}/${encodeURIComponent(p.path)}">
    ${p.votes != null ? `<div class="v"><b>${p.votes}</b><small>votes</small></div>` : ''}
    <div class="b"><span>${esc(p.title)}</span><span class="dim" style="font-size:13px">${esc(meta)}</span></div></a>`;
}
O.zimLine = zimLine;

O.routes.browse = async (main, r) => {
  const kind = r.rest || 'monster';
  const list = await O.api(`browse?kind=${kind}&edition=2024`);
  const groups = {};
  list.forEach(e => (groups[e.name[0].toUpperCase()] ||= []).push(e));
  main.innerHTML = `<header class="pagehead"><div><a class="eyebrow" href="#/codex">Codex</a><h1>${esc({ 'magic-item': 'Magic items', glossary: 'Rules Glossary' }[kind] || kind[0].toUpperCase() + kind.slice(1) + (kind.endsWith('s') ? '' : 's'))}</h1></div><span class="dim">${list.length} · SRD 5.2</span></header>
    ${Object.entries(groups).map(([L, es]) => `<section class="card"><h2>${esc(L)}</h2><div class="gallery">${es.map(e => `<a class="gcard" href="#/wiki/${encodeURIComponent(e.id)}">
      <span class="gimg">${e.pic ? `<img src="${esc(e.pic.src)}" alt="" loading="lazy" title="${esc(e.pic.author + ' · ' + e.pic.license)}">` : gi(e.icon, 44)}</span>
      <b>${esc(e.name)}</b><small>${esc(kind === 'monster' && e.summary ? e.summary : (e.summary || '').slice(0, 60))}</small></a>`).join('')}</div></section>`).join('')}`;
};

// ---------- wiki hub ----------
const HUBSHELVES = ['summary', 'rule', 'third', 'expert', 'craft', 'idea', 'yours'];
O.routes.wiki = async (main, r) => {
  const id = r.rest;
  main.innerHTML = '<span class="spinner"></span>';
  const h = await O.api('hub/' + id);
  const e = h.entry, S = h.sections;
  const shelves = HUBSHELVES.filter(k => !(k === 'summary' && !O.ai) && !(O.demo && k === 'yours'));
  const show = Object.fromEntries(HUBSHELVES.map(k => [k, shelves.includes(k)]));
  const isBook = e.kind === 'book';
  const render = () => {
    const parts = [];
    if (show.summary && !isBook) parts.push(`<section class="card summary" id="s-summary"><div class="cardhead"><span class="chips">${O.badge('summary')}<span class="dim" style="font-size:13px">AI-written · cited</span></span>
      ${e.summary_ai ? '' : `<button class="btn small" id="sumbtn" type="button">Summarize</button>`}</div>
      <div id="sumtext">${e.summary_ai ? summaryHTML(e.summary_ai) : ''}</div></section>`);
    if (show.rule || (isBook && show.idea)) parts.push(`<section class="card" id="s-rules"><div class="cardhead"><h2>${isBook ? 'Passage' : 'Rules'}</h2>${O.badge(e.shelf)}</div>
      ${isBook ? `<div class="prose">${O.md(e.body)}</div><span class="dim">${esc(e.doc_name)} · ${esc(e.grp || '')} · private to this server</span>` : O.entryBlock(e)}
      ${S.terms.length ? `<div class="chips"><span class="eyebrow" style="margin-right:4px">Rules it uses</span>${S.terms.map(t => `<a class="chip" href="#/wiki/${encodeURIComponent(t.id)}" data-term="${esc(t.id)}">${esc(t.name)}</a>`).join('')}</div>` : ''}
      ${S.books.filter(b => b.shelf === 'rule').map(bookRow).join('')}</section>`);
    const vs = S.versions.filter(v => (v.shelf === 'rule' ? show.rule : show.third));
    if (vs.length) parts.push(`<section class="card" id="s-versions"><div class="cardhead"><h2>Other versions</h2></div>
      ${vs.map(v => `<a class="srcrow" href="#/wiki/${encodeURIComponent(v.id)}" style="text-decoration:none;color:inherit">${O.thumb(v, 'small')}${O.badge(v.shelf)}<span class="what"><span>${esc(v.name)}${v.edition ? ` <span class="dim">· ${esc(v.edition)}</span>` : ''}</span><small>${esc(v.doc_name)} · ${esc(v.license)}</small></span><span class="dim" style="font-size:14px">${esc(v.summary || '')}</span></a>`).join('')}</section>`);
    if (show.expert && S.expert.pages.length) parts.push(`<section class="card" id="s-expert"><div class="cardhead"><h2>Expert answers</h2><span class="chips"><span class="dim" style="font-size:13px">RPG Stack Exchange · ${S.expert.total.toLocaleString()} pages</span>${O.badge('expert')}</span></div>
      ${S.expert.pages.map(p => zimLine(p)).join('')}</section>`);
    if (show.idea && S.homebrew.pages.length) parts.push(`<section class="card dashed" id="s-homebrew"><div class="cardhead"><h2>Homebrew</h2><span class="chips"><span class="dim" style="font-size:13px">D&amp;D Wiki · ${S.homebrew.total} pages · ${S.homebrew.mentions} mentions</span>${O.badge('idea', 'Idea · not official')}</span></div>
      <div class="grid2">${S.homebrew.pages.map(p => `<a class="tile dashed" href="#/read/dandwiki/${encodeURIComponent(p.path)}"><span style="font-weight:500">${esc(p.name)}</span><span class="dim" style="font-size:13px">${esc(p.kind)}</span><span style="font-size:14px;color:var(--text-2)">${esc((p.text || '').slice(0, 110))}…</span></a>`).join('')}</div></section>`);
    if (show.craft && S.craft.pages.length) parts.push(`<section class="card" id="s-craft"><div class="cardhead"><h2>Worldbuilding</h2><span class="chips"><span class="dim" style="font-size:13px">Worldbuilding Q&amp;A · ${S.craft.total.toLocaleString()} pages</span>${O.badge('craft')}</span></div>
      ${S.craft.pages.map(p => zimLine(p)).join('')}</section>`);
    if (show.idea && S.myth.length) parts.push(`<section class="card" id="s-myth"><div class="cardhead"><h2>Myth roots</h2>${O.badge('idea')}</div>
      ${S.myth.map(p => `<a class="srcrow" href="#/read/${encodeURIComponent(p.zim)}/${encodeURIComponent(p.path)}" style="text-decoration:none;color:inherit">${O.badge('expert')}<span class="what"><span>${esc(p.title)}</span><small>Mythology Q&amp;A · ${p.votes} votes · about “${esc(p.about)}”</small></span></a>`).join('')}</section>`);
    const lib = S.books.filter(b => b.shelf !== 'rule' && b.id !== e.id);
    if (show.idea && lib.length) parts.push(`<section class="card" id="s-books"><div class="cardhead"><h2>In your books</h2><span class="chips">${O.badge('idea')}${O.badge('private', 'Private')}</span></div>${lib.map(bookRow).join('')}</section>`);
    if (show.yours) parts.push(`<section class="card" id="s-yours" style="border-color:var(--violet-line)"><div class="cardhead"><h2>In your world</h2>${O.badge('yours')}</div>
      ${S.yours.length ? S.yours.map(y => `<div class="srcrow"><span class="what"><span>${esc(y.title)}</span><small>${esc(y.note)}</small></span><span style="flex-basis:100%;font-size:14px;color:var(--text-2)">${esc(y.snippet)}</span></div>`).join('') : '<div class="empty" style="padding:14px">Not in your vault yet</div>'}</section>`);
    const toc = [['s-rules', isBook ? 'Passage' : 'Rules', show.rule], ['s-versions', 'Other versions', vs.length], ['s-expert', 'Expert answers', show.expert && S.expert.pages.length],
      ['s-homebrew', 'Homebrew', show.idea && S.homebrew.pages.length], ['s-craft', 'Worldbuilding', show.craft && S.craft.pages.length], ['s-myth', 'Myth roots', show.idea && S.myth.length],
      ['s-books', 'In your books', show.idea && lib.length], ['s-yours', 'In your world', show.yours]].filter(x => x[2]);
    $('#hubmain').innerHTML = parts.join('') || '<div class="empty">No sources selected</div>';
    $('#toc').innerHTML = toc.map(([id, l]) => `<a href="javascript:void 0" data-jump="${id}"><span>${l}</span></a>`).join('');
    $('#toc').querySelectorAll('[data-jump]').forEach(a => a.onclick = () => document.getElementById(a.dataset.jump)?.scrollIntoView({ behavior: 'smooth' }));
    const sb = $('#sumbtn');
    if (sb) sb.onclick = async () => {
      sb.disabled = true; sb.innerHTML = '<span class="spinner"></span>';
      try { e.summary_ai = await O.api('summary/' + id, { body: {} }); $('#sumtext').innerHTML = summaryHTML(e.summary_ai); sb.remove(); }
      catch (err) { $('#sumtext').innerHTML = `<span class="err">${esc(err.message)}</span>`; sb.disabled = false; sb.textContent = 'Summarize'; }
    };
    main.querySelectorAll('[data-filter]').forEach(b => { const k = b.dataset.filter; b.style.opacity = show[k] ? 1 : .45; b.setAttribute('aria-pressed', show[k]); });
  };
  const tally = [['rule', 1 + S.versions.filter(v => v.shelf === 'rule').length + S.books.filter(b => b.shelf === 'rule').length], ['third', S.versions.filter(v => v.shelf === 'third').length],
    ['expert', S.expert.total + S.myth.length], ['craft', S.craft.total], ['idea', S.homebrew.total + S.books.filter(b => b.shelf !== 'rule').length], ['yours', S.yours.length]];
  main.innerHTML = `<div class="chips" style="font-size:14px"><a href="#/codex">Codex</a><span class="dim">›</span><span class="dim">${esc(e.kind_label)}</span></div>
    <header class="pagehead hubhead"><div class="hubtop">${e.pic ? `<figure class="hero"><a href="${esc(e.pic.article)}" target="_blank" rel="noopener"><img src="${esc(e.pic.src)}" alt="${esc(e.name)}, from Wikipedia"></a>
        <figcaption>${O.credit(e.pic)}</figcaption></figure>` : `<span class="heroicon">${gi(e.icon, 64)}</span>`}
      <div style="display:flex;flex-direction:column;gap:6px;min-width:0"><h1>${esc(e.name)}</h1>
      <span style="font-size:18px;color:var(--text-2)">${esc(e.summary || e.kind_label)}${e.edition ? ' · ' + esc(e.edition === '2024' ? '2024 rules' : e.edition) : ''}</span>
      <span class="mono dim">${esc(e.doc_name)}${e.license ? ' · ' + esc(e.license) : ''}</span></div></div>
      <div class="chips">${!O.demo && e.kind === 'monster' ? `<button class="btn" type="button" id="tovault">${icon('pen', 18)}Add to vault</button>
        <button class="btn" type="button" id="toenc">${icon('d20', 18)}Add to encounter</button>` : ''}
      ${!O.ai ? '' : `<a class="btn" href="#/ask?q=${encodeURIComponent('Tell me about ' + e.name)}">${icon('ask', 18)}Ask about this</a>`}</div></header>
    <div id="vaultmsg" class="mono dim"></div>
    <div class="chips" role="group" aria-label="Show sources"><span class="eyebrow" style="margin-right:4px;align-self:center">Show</span>
      ${shelves.map(k => `<button type="button" class="badge b-${k}" data-filter="${k}" style="min-height:34px;padding:0 12px">${SHELF[k]}</button>`).join('')}</div>
    <div class="row"><div class="col-main" id="hubmain"></div>
    <aside class="col-side" style="flex:1 1 280px"><section class="card toc"><span class="eyebrow">On this page</span><div id="toc"></div></section>
      <section class="card"><span class="eyebrow">Sources</span>${tally.filter(t => t[1]).map(([k, n]) => `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">${O.badge(k)}<b>${n.toLocaleString()}</b></div>`).join('')}</section></aside></div>`;
  main.querySelectorAll('[data-filter]').forEach(b => b.onclick = () => { show[b.dataset.filter] = !show[b.dataset.filter]; render(); });
  render();
  // Notes for the vault's plugins: a Fantasy Statblocks note, and a line in the Initiative Tracker encounter.
  const say = (r, extra = '') => { $('#vaultmsg').innerHTML = `${esc(r.vault)} / ${esc(r.path)}${esc(extra)} · <a href="obsidian://open?vault=${encodeURIComponent(r.vault)}&file=${encodeURIComponent(r.path)}">Open in Obsidian</a>`; };
  const fail = err => { $('#vaultmsg').textContent = err.message; };
  const vb = $('#tovault'), eb = $('#toenc');
  if (vb) vb.onclick = () => O.api('vault/monster', { body: { id } }).then(r => say(r)).catch(fail);
  if (eb) eb.onclick = () => O.api('vault/encounter', { body: { id } }).then(r => say(r, ' · ' + r.creatures.map(c => `${c.n} × ${c.name}`).join(', '))).catch(fail);
};
function bookRow(b) {
  return `<a class="srcrow" href="#/wiki/${encodeURIComponent(b.id)}" style="text-decoration:none;color:inherit">${O.badge(b.shelf)}<span class="what"><span>${esc(b.name)}${b.note ? ` <span class="dim">· ${esc(b.note)}</span>` : ''}</span><small>Your library · ${esc(b.grp || '')}</small></span>
    <span style="flex-basis:100%;font-size:14px;color:var(--text-2)">${esc(b.snippet || '').replace(/\[\[(.+?)\]\]/g, '<mark>$1</mark>')}</span></a>`;
}
function summaryHTML(s) {
  return `<p>${esc(s.text).replace(/\[(\d+)\]/g, (m, n) => `<a class="cite" href="javascript:void 0" title="${esc((s.sources[n - 1] || {}).label || '')}">${n}</a>`)}</p>
    <div class="chips" style="margin-top:8px">${s.sources.map((x, i) => `<span class="chip" style="font-size:12px">${i + 1} · ${esc(x.label)} · ${esc(x.title)}</span>`).join('')}</div>`;
}

// ---------- reading an archive page ----------
O.routes.read = async (main, r) => {
  const [zim, ...rest] = r.rest.split('/');
  const path = rest.join('/');
  main.innerHTML = '<span class="spinner"></span>';
  const p = await O.api(`zim/page?zim=${encodeURIComponent(zim)}&path=${encodeURIComponent(path)}`);
  const by = n => n ? ` · ${esc(n)}` : '';
  const body = p.question != null
    ? `<div class="prose"><p class="eyebrow">Question · ${p.votes} votes${by(p.asker)}</p>${O.md(p.question)}</div>${p.answer ? `<div class="prose"><p class="eyebrow">${p.accepted ? 'Accepted answer' : 'Top answer'} · ${p.answer_score} votes${by(p.answerer)}</p>${O.md(p.answer)}</div>` : ''}`
    : `<div class="prose">${O.md(p.text)}</div>`;
  const LIC = { 'CC BY-SA': ['CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0/'], 'GFDL': ['GFDL 1.3', 'https://www.gnu.org/licenses/fdl-1.3.html'] }[p.license] || [p.license, ''];
  const site = p.original ? new URL(p.original).hostname.replace(/^www\./, '') : '';
  const links = `<div class="chips">${p.original ? `<a class="btn" href="${esc(p.original)}" target="_blank" rel="noopener">${icon('out', 18)}Read it on ${esc(site)}</a>` : ''}
    ${kiwixHere(p.url) ? `<a class="btn" href="${esc(p.url)}" target="_blank" rel="noopener">${icon('out', 18)}Open in Kiwix</a>` : ''}</div>
    <span class="dim" style="font-size:13px">${esc(p.source)}${p.asker ? ' · ' + esc([...new Set([p.asker, p.answerer].filter(Boolean))].join(', ')) : ''} · ${LIC[1] ? `<a href="${LIC[1]}" target="_blank" rel="noopener">${esc(LIC[0])}</a>` : esc(LIC[0])}</span>`;
  main.innerHTML = `<div class="chips" style="font-size:14px"><a href="javascript:history.back()">Back</a></div>
    <header class="pagehead"><div style="min-width:0"><span class="eyebrow">${esc(p.source)}</span><h1>${esc(p.title)}</h1></div>
    <span class="chips">${O.badge(p.shelf, p.note ? SHELF[p.shelf] + ' · ' + p.note : '')}<span class="chip">${esc(p.license)}</span></span></header>
    ${p.tags?.length ? `<div class="chips">${p.tags.map(t => `<span class="chip">${esc(t)}</span>`).join('')}</div>` : ''}
    <section class="card">${body}${links}</section>`;
};

// ---------- credits ----------
const SRD52 = 'This work includes material from the System Reference Document 5.2.1 (“SRD 5.2.1”) by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode.';
const SRD51 = 'This work includes material taken from the System Reference Document 5.1 (“SRD 5.1”) by Wizards of the Coast LLC and available at https://dnd.wizards.com/resources/systems-reference-document. The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License available at https://creativecommons.org/licenses/by/4.0/legalcode.';
const linkify = s => esc(s).replace(/https?:\/\/[^\s)]+[^\s).,]/g, u => `<a href="${u}" target="_blank" rel="noopener">${u}</a>`);
O.routes.credits = async (main, r) => {
  if (r && r.rest === 'pictures') {
    const ps = await O.api('credits/pictures');
    main.innerHTML = `<div class="chips" style="font-size:14px"><a href="#/credits">Credits &amp; licenses</a><span class="dim">›</span><span class="dim">Pictures</span></div>
      <header class="pagehead"><div><span class="eyebrow">Wikimedia Commons</span><h1>Pictures</h1></div><span class="dim">${ps.length}</span></header>
      <div class="picgrid">${ps.map(p => `<figure><a href="${esc(p.source)}" target="_blank" rel="noopener"><img src="${esc(p.src)}" alt="" loading="lazy"></a>
        <b>${esc(p.for.slice(0, 4).join(', '))}${p.for.length > 4 ? ' …' : ''}</b><span>${O.credit(p)} · <a href="${esc(p.article)}" target="_blank" rel="noopener">${esc(p.title)}</a></span></figure>`).join('')}</div>`;
    return;
  }
  const c = await O.api('credits');
  const other = c.docs.filter(d => !['srd-2024', 'srd-2014'].includes(d.key));
  const ARCH = { 'CC BY-SA': 'https://creativecommons.org/licenses/by-sa/4.0/', 'GFDL': 'https://www.gnu.org/licenses/fdl-1.3.html' };
  main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">Olam</span><h1>Credits &amp; licenses</h1></div></header>
    <section class="card prose"><h2>The rules</h2><p>${linkify(SRD52)}</p><p>${linkify(SRD51)}</p>
      <p>Olam is an unofficial fan project, compatible with fifth edition.</p></section>
    ${other.length ? `<section class="card prose"><h2>Other books</h2><ul>${other.map(d => `<li><strong>${esc(d.name)}</strong>${d.publisher ? ' by ' + esc(d.publisher) : ''}${d.url ? `, ${linkify(d.url)}` : ''}. ${esc(d.license)}. The text comes from the <a href="https://github.com/open5e/open5e-api" target="_blank" rel="noopener">Open5e</a> project’s data.${d.note ? ' ' + linkify(d.note) : ''}</li>`).join('')}</ul></section>` : ''}
    <section class="card prose"><h2>The archives</h2><ul>${c.archives.map(a => `<li><strong>${esc(a.label)}</strong>, from the Kiwix offline archive ${esc(a.book)}. ${ARCH[a.license] ? `<a href="${ARCH[a.license]}" target="_blank" rel="noopener">${esc(a.license)}</a>` : esc(a.license)}. Every page Olam shows names its authors and links to the original.</li>`).join('')}</ul>
      <p>Stack Exchange questions and answers are by their authors on the Stack Exchange network. D&amp;D Wiki pages are by its contributors at dandwiki.com.</p></section>
    ${c.pictures && c.pictures.entries ? `<section class="card prose"><h2>Pictures</h2><p>${c.pictures.files} pictures from <a href="https://commons.wikimedia.org" target="_blank" rel="noopener">Wikimedia Commons</a>, found through Wikipedia, illustrate ${c.pictures.entries} entries. Each one names its author and license where it’s shown and links to its page on Commons.</p>
      <p class="dim">${Object.entries(c.pictures.licenses).sort((a, b) => b[1] - a[1]).map(([l, n]) => `${esc(l)} (${n})`).join(' · ')}</p><p><a href="#/credits/pictures">Every picture, with its credit</a></p></section>` : ''}
    ${c.icons && c.icons.length ? `<section class="card prose"><h2>Icons</h2><p>Icons by ${c.icons.map(a => esc(a.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join(' '))).join(', ')}, from <a href="https://game-icons.net" target="_blank" rel="noopener">game-icons.net</a>, under <a href="https://creativecommons.org/licenses/by/3.0/" target="_blank" rel="noopener">CC BY 3.0</a>.</p></section>` : ''}
    <section class="card prose"><h2>Type</h2><p>IM Fell English by Igino Marini and Alegreya Sans by Juan Pablo del Peral (Huerta Tipográfica), both under the SIL Open Font License.</p></section>`;
};

// ---------- settings ----------
O.routes.settings = async (main) => {
  if (O.demo) { main.innerHTML = '<div class="empty">Settings are off in the demo</div>'; return; }
  const s = await O.api('settings');
  const AI = { api: `Claude API · ${s.model}`, cli: `Claude CLI · ${s.model}`, off: 'Off' }[s.ai];
  const row = (k, v, mono) => `<div class="kv"><span class="dim">${k}</span><span class="${mono ? 'mono' : ''}">${v}</span></div>`;
  const pw = (id, label, ac) => `<label class="field-l"><span class="eyebrow">${label}</span><input class="field" id="${id}" type="password" autocomplete="${ac}" required minlength="${id === 'pwcur' ? 1 : 8}"></label>`;
  main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">Olam ${esc(s.version)}</span><h1>Settings</h1></div></header>
    <div class="settings">
    <form class="card" id="pwform"><div class="cardhead"><h2>Password</h2>${icon('lock', 20)}</div>
      ${pw('pwcur', 'Current password', 'current-password')}${pw('pwnew', 'New password', 'new-password')}${pw('pwnew2', 'New password again', 'new-password')}
      <div class="err" id="pwerr"></div>
      <div class="chips"><button class="btn primary" type="submit">Change password</button><span class="dim hidden" id="pwok">${icon('check', 18)}Changed</span></div></form>
    <section class="card"><div class="cardhead"><h2>Sign-in</h2></div>
      <div class="chips"><button class="btn" type="button" id="soothers">Sign out other browsers</button><button class="btn" type="button" id="soself">Sign out</button>
        <span class="dim hidden" id="sook">${icon('check', 18)}Done</span></div></section>
    <section class="card"><div class="cardhead"><h2>Appearance</h2></div>
      <div class="seg" id="themeseg">${[['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']].map(([k, l]) => `<button type="button" data-theme="${k}" class="${window.olamTheme() === k ? 'on' : ''}">${l}</button>`).join('')}</div></section>
    <section class="card"><div class="cardhead"><h2>Connected</h2><span class="mono dim">olam.env</span></div>
      ${row('Vault', s.vault ? esc(s.vault) + (s.vault_ok ? '' : ' · not found') : 'None', !!s.vault)}
      ${row('AI', esc(AI))}
      ${row('Kiwix', s.kiwix ? esc(s.kiwix) : 'None', !!s.kiwix)}
      ${row('Calibre', s.calibre ? `${s.books} books` : 'None')}
      ${row('Archives', s.archives.length ? esc(s.archives.join(' · ')) : 'None')}
      ${row('Library', `${s.entries.toLocaleString()} entries`)}
      ${row('Address', esc(s.url), true)}</section>
    </div>`;
  $('#pwform').onsubmit = async ev => {
    ev.preventDefault();
    $('#pwerr').textContent = ''; $('#pwok').classList.add('hidden');
    if ($('#pwnew').value !== $('#pwnew2').value) { $('#pwerr').textContent = 'The new passwords don’t match'; return; }
    try {
      await O.api('account/password', { body: { current: $('#pwcur').value, new: $('#pwnew').value } });
      ev.target.reset(); $('#pwok').classList.remove('hidden');
    } catch (e) { $('#pwerr').textContent = e.message; }
  };
  $('#soothers').onclick = async () => { await O.api('account/signout-others', { body: {} }); $('#sook').classList.remove('hidden'); };
  $('#themeseg').onclick = ev => {
    const b = ev.target.closest('[data-theme]'); if (!b) return;
    window.olamTheme(b.dataset.theme);
    $('#themeseg').querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
  };
  $('#soself').onclick = async () => { await O.api('logout', { body: {} }); $('#app').innerHTML = ''; O.showLogin(); };
};

// ---------- Ask ----------
const PRESETS = ['How does grappling work?', 'Can I take a reaction on my own turn?', 'What happens when I drop to 0 hit points?', 'How do I hide?'];
O.routes.ask = async (main, r) => {
  if (!O.ai) { main.innerHTML = `<div class="empty">${O.demo ? 'Ask is off in the demo' : 'The AI features are off'}</div>`; return; }
  const q = r.q.get('q') || '';
  main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">Your books, cited</span><h1>Ask</h1></div></header>
    <form class="searchbar" id="aform">${icon('ask', 20, 'var(--dim)')}<input id="aq" aria-label="Question" placeholder="Ask a rules question" value="${esc(q)}" autofocus><button class="btn primary" type="submit">Ask</button></form>
    <div class="chips">${PRESETS.map(p => `<a class="chip" href="#/ask?q=${encodeURIComponent(p)}">${esc(p)}</a>`).join('')}</div>
    <div id="answer"></div>`;
  $('#aform').onsubmit = ev => { ev.preventDefault(); const v = $('#aq').value.trim(); if (v) O.go('#/ask?q=' + encodeURIComponent(v)); };
  if (!q) return;
  $('#answer').innerHTML = `<section class="card"><span class="dim"><span class="spinner"></span> Reading the sources</span></section>`;
  try {
    const a = await O.api('ask', { body: { q } });
    if (a.empty) { $('#answer').innerHTML = '<div class="empty">No match in your sources</div>'; return; }
    const lines = esc(a.answer).split('\n');
    const bullets = lines.filter(l => /^\s*-\s/.test(l)).map(l => l.replace(/^\s*-\s/, ''));
    const lead = lines.filter(l => !/^\s*-\s/.test(l) && l.trim()).join(' ');
    const cite = s => s.replace(/\[(\d+)\]/g, (m, n) => `<a class="cite" href="#src-${n}">${n}</a>`);
    $('#answer').innerHTML = `<section class="card"><h2>${esc(q)}</h2><div class="answer">${O.linkTerms(cite(lead))}${bullets.length ? '<ul>' + bullets.map(b => `<li>${O.linkTerms(cite(b))}</li>`).join('') + '</ul>' : ''}</div></section>
      <section class="card"><span class="eyebrow">Sources</span>${a.sources.map((s, i) => {
        const href = s.kind === 'zim' ? `#/read/${encodeURIComponent(s.zim)}/${encodeURIComponent(s.path)}` : `#/wiki/${encodeURIComponent(s.id)}`;
        return `<a class="srcrow" id="src-${i + 1}" href="${href}" style="text-decoration:none;color:inherit"><b style="width:22px">${i + 1}</b>${O.badge(s.shelf)}<span class="what"><span>${esc(s.title)}</span><small>${esc(s.label)}</small></span></a>`;
      }).join('')}</section>`;
  } catch (e) { $('#answer').innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
};

// ---------- Review ----------
O.routes.review = async (main) => {
  const items = O.demo ? await O.api('review/list', { body: { keys: O.local.review() } }) : await O.api('review');
  O.setReviewCount(items.length);
  main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">Questions you missed</span><h1>Review</h1></div><span class="dim">${items.length}</span></header>
    <div id="rev" style="display:flex;flex-direction:column;gap:12px">${items.length ? '' : '<div class="empty">Nothing to review</div>'}</div>`;
  items.forEach(it => {
    const el = document.createElement('div');
    el.className = 'q';
    el.innerHTML = `<span class="eyebrow">${esc(it.title)}</span><span style="font-size:17px">${esc(it.q)}</span>
      <div class="opts">${it.opts.map((o, i) => `<button type="button" data-i="${i}">${esc(o)}</button>`).join('')}</div><div class="fb"></div>`;
    el.querySelectorAll('[data-i]').forEach(b => b.onclick = async () => {
      const ok = +b.dataset.i === it.correct;
      el.querySelectorAll('[data-i]').forEach(x => x.classList.remove('good', 'bad'));
      b.classList.add(ok ? 'good' : 'bad');
      el.className = 'q ' + (ok ? 'right' : 'wrong');
      el.querySelector('.fb').innerHTML = `<span style="color:${ok ? 'var(--brass-hi)' : 'var(--red)'};font-weight:700">${ok ? 'Correct' : 'Not quite'}</span> <span class="dim">${esc(it.why)}</span>`;
      if (ok && O.demo) { const left = O.local.review().filter(k => k !== it.key); O.local.setReview(left); O.setReviewCount(left.length); }
      else if (ok) { const left = await O.api('review/done', { body: { key: it.key } }); O.setReviewCount(left.length); }
    });
    $('#rev').appendChild(el);
  });
};

document.addEventListener('DOMContentLoaded', start);
