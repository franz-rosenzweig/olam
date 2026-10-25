// The world from the vault: Map (World/Places), People (World/People) and Table (World/Encounters + World/Party.md).
'use strict';
(() => {
  const { esc, api, icon, md } = O;
  const $ = (s, el = document) => el.querySelector(s);
  const fileUrl = rel => 'api/vault/file?rel=' + encodeURIComponent(rel);
  O.obsidian = rel => `obsidian://open?vault=${encodeURIComponent(O.vaultName || 'Olam')}&file=${encodeURIComponent(rel)}`;
  const view = { pv: false };                       // DM view or the players' view, shared by Map and People

  // A note's markdown with [[links]] turned into links to the screen that shows them.
  let names = {};
  async function loadNames() {
    try {
      const [m, ppl] = await Promise.all([api('world/map').catch(() => ({ places: [] })), api('world/people').catch(() => [])]);
      names = {};
      (m.places || []).forEach(p => { names[p.name.toLowerCase()] = '#/map?place=' + encodeURIComponent(p.rel); });
      ppl.forEach(p => { names[p.name.toLowerCase()] = '#/people/' + encodeURIComponent(p.rel); });
    } catch (e) { /* no vault */ }
  }
  O.noteHTML = text => {
    const toks = [];
    const pre = String(text || '').replace(/```[\s\S]*?```/g, '').replace(/\n(\*\*[^*\n]+:\*\*)/g, '\n\n$1').replace(/\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]/g, (m, n, alias) => {
      toks.push([n.trim(), alias]); return `⟦${toks.length - 1}⟧`;
    });
    return md(pre, { link: false }).replace(/⟦(\d+)⟧/g, (m, i) => {
      const [n, alias] = toks[+i];
      const href = names[n.toLowerCase()];
      return href ? `<a href="${href}">${esc(alias || n)}</a>` : `<span class="dim">${esc(alias || n)}</span>`;
    });
  };

  const seg = (on) => `<div class="seg" role="group" aria-label="View"><button type="button" data-v="dm" class="${on ? '' : 'on'}" aria-pressed="${!on}">DM</button>
    <button type="button" data-v="pv" class="${on ? 'on' : ''}" aria-pressed="${on}">Players</button></div>`;
  const bindSeg = (el, redraw) => el.querySelectorAll('[data-v]').forEach(b => b.onclick = () => { view.pv = b.dataset.v === 'pv'; redraw(); });
  const noVault = msg => `<div class="empty">${esc(msg)}</div>`;

  // ======================================================================== Map
  O.routes.map = async (main, r) => {
    await loadNames();
    let M;
    try { M = await api('world/map'); } catch (e) { main.innerHTML = noVault(e.message); return; }
    let sel = r.q.get('place') || '';
    let adding = false, pending = null;
    let zoom = 1, pan = [0, 0];
    const B = M.bounds;
    const toPct = ([lat, lng]) => [(lng - B.left) / (B.right - B.left) * 100, (B.top - lat) / (B.top - B.bottom) * 100];
    const toLoc = (x, y) => [+(B.top - y * (B.top - B.bottom)).toFixed(2), +(B.left + x * (B.right - B.left)).toFixed(2)];

    const draw = () => {
      const shown = M.places.filter(p => p.location && (!view.pv || (p.visited && !p.dm_only)));
      const P = M.places.find(p => p.rel === sel);
      main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">${esc(M.folder)} · ${M.places.length} places</span><h1>World map</h1></div>
        <div class="chips">${view.pv ? '' : `<button type="button" class="btn ${adding ? 'primary' : ''}" id="addplace">${icon('plus', 18)}${adding ? 'Click the map' : 'Add place'}</button>`}
          ${seg(view.pv)}<a class="btn" href="${O.obsidian(M.note)}">${icon('out', 18)}Open in Obsidian</a></div></header>
        <div class="row"><section class="mapcard" style="flex:999 1 600px;min-width:0">
          <div class="mapview" id="mapview" style="aspect-ratio:${M.width || 16} / ${M.height || 10}">
            <div class="mapinner" id="mapinner" style="width:${zoom * 100}%;transform:translate(${pan[0]}px,${pan[1]}px)">
              ${M.image ? `<img src="${fileUrl(M.image)}" alt="" draggable="false">` : ''}
              ${shown.map(p => { const [x, y] = toPct(p.location); return `<button type="button" class="pin ${p.visited ? 'visited' : ''} ${p.dm_only ? 'dmonly' : ''} ${p.rel === sel ? 'sel' : ''}"
                style="left:${x}%;top:${y}%" data-rel="${esc(p.rel)}" aria-label="${esc(p.name)}"><span class="dot"></span><span class="lbl">${esc(p.name)}</span></button>`; }).join('')}
              ${pending ? `<span class="pin pending" style="left:${pending.x * 100}%;top:${pending.y * 100}%"><span class="dot"></span></span>` : ''}
            </div>
            <div class="mapzoom"><button type="button" id="zin" aria-label="Zoom in">+</button><button type="button" id="zout" aria-label="Zoom out">−</button></div>
          </div></section>
          <aside class="col-side" style="flex:1 1 320px" id="placeside"></aside></div>`;
      bindSeg(main, draw);
      const side = $('#placeside');
      if (pending) {
        side.innerHTML = `<form class="card" id="newplace"><h2>New place</h2>
          <label class="eyebrow" for="pname">Name</label><input id="pname" class="field" required autofocus>
          <label class="eyebrow" for="ptype">Type</label><select id="ptype" class="field">${['City', 'Town', 'Village', 'Ruin', 'Dungeon', 'Wilds', 'Landmark', 'Sea'].map(t => `<option>${t}</option>`).join('')}</select>
          <div class="chips"><button class="btn primary" type="submit">Save</button><button class="btn" type="button" id="pcancel">Cancel</button></div><span class="err" id="perr"></span></form>`;
        $('#pcancel').onclick = () => { pending = null; adding = false; draw(); };
        $('#newplace').onsubmit = async ev => {
          ev.preventDefault();
          try {
            const res = await api('world/place', { body: { name: $('#pname').value.trim(), type: $('#ptype').value, location: toLoc(pending.x, pending.y) } });
            M = await api('world/map'); sel = res.rel; pending = null; adding = false; await loadNames(); draw();
          } catch (e) { $('#perr').textContent = e.message; }
        };
      } else if (P) {
        side.innerHTML = `<section class="card"><div class="cardhead" style="align-items:flex-start"><div><span class="eyebrow">${esc(P.type || 'Place')}</span><h2>${esc(P.name)}</h2></div>
            <span class="chip ${P.visited ? 'brass' : ''}">${P.dm_only ? 'DM only' : P.visited ? 'Visited' : 'Not yet'}</span></div>
          ${view.pv ? '' : `<div class="chips"><button type="button" class="btn small" id="tvisit">${P.visited ? 'Mark not visited' : 'Mark visited'}</button>
            <button type="button" class="btn small" id="tdm">${P.dm_only ? 'Show to players' : 'DM only'}</button></div>`}
          <div class="prose" id="pbody"><span class="spinner"></span></div>
          ${P.people.length ? `<div class="chips"><span class="eyebrow" style="align-self:center">People</span>${P.people.map(q => `<a class="chip" href="#/people/${encodeURIComponent(q.rel)}">${esc(q.name)}</a>`).join('')}</div>` : ''}
          <div class="chips"><a class="btn small" href="${O.obsidian(P.rel)}">${icon('out', 16)}Open in Obsidian</a><button type="button" class="btn small" id="pclose">All places</button></div></section>`;
        api('world/note?rel=' + encodeURIComponent(P.rel)).then(n => {
          let body = n.body;
          if (view.pv) body = body.split('\n').filter(l => !/secret/i.test(l)).join('\n');
          $('#pbody').innerHTML = O.noteHTML(body) || '<span class="dim">—</span>';
        }).catch(() => { $('#pbody').textContent = ''; });
        $('#pclose').onclick = () => { sel = ''; draw(); };
        const tv = $('#tvisit'), td = $('#tdm');
        if (tv) tv.onclick = async () => { await api('world/place/set', { body: { rel: P.rel, key: 'visited', value: !P.visited } }); P.visited = !P.visited; draw(); };
        if (td) td.onclick = async () => { await api('world/place/set', { body: { rel: P.rel, key: 'dm-only', value: !P.dm_only } }); P.dm_only = !P.dm_only; draw(); };
      } else {
        const list = M.places.filter(p => !view.pv || (p.visited && !p.dm_only));
        side.innerHTML = `<section class="card"><h2>Places</h2>${list.length ? list.map(p => `<button type="button" class="result" data-pick="${esc(p.rel)}" style="text-align:left">
          <span class="t">${O.gi(p.icon, 20)}${esc(p.name)}</span><span class="s">${esc(p.type || 'Place')}${p.location ? '' : ' · not on the map'}${p.dm_only ? ' · DM only' : ''}</span></button>`).join('')
          : `<div class="empty" style="padding:16px">${view.pv ? 'Nothing visited yet' : 'No places yet'}</div>`}</section>`;
        side.querySelectorAll('[data-pick]').forEach(b => b.onclick = () => { sel = b.dataset.pick; draw(); });
      }
      wireMap();
    };

    const wireMap = () => {
      const viewEl = $('#mapview'), inner = $('#mapinner');
      const ab = $('#addplace');
      if (ab) ab.onclick = () => { adding = !adding; pending = null; draw(); };
      $('#zin').onclick = () => { zoom = Math.min(4, zoom * 1.5); draw(); };
      $('#zout').onclick = () => { zoom = Math.max(1, zoom / 1.5); if (zoom === 1) pan = [0, 0]; draw(); };
      let drag = null;
      inner.addEventListener('pointerdown', ev => {
        const pin = ev.target.closest('.pin[data-rel]');
        drag = { pin, x0: ev.clientX, y0: ev.clientY, pan0: pan.slice(), moved: false };
        inner.setPointerCapture(ev.pointerId);
      });
      inner.addEventListener('pointermove', ev => {
        if (!drag) return;
        const dx = ev.clientX - drag.x0, dy = ev.clientY - drag.y0;
        if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
        if (drag.pin && !view.pv && drag.moved) {
          const rc = inner.getBoundingClientRect();
          drag.pin.style.left = ((ev.clientX - rc.left) / rc.width * 100) + '%';
          drag.pin.style.top = ((ev.clientY - rc.top) / rc.height * 100) + '%';
        } else if (!drag.pin && zoom > 1 && drag.moved) {
          pan = [drag.pan0[0] + dx, drag.pan0[1] + dy];
          inner.style.transform = `translate(${pan[0]}px,${pan[1]}px)`;
        }
      });
      inner.addEventListener('pointerup', async ev => {
        const d = drag; drag = null;
        if (!d) return;
        const rc = inner.getBoundingClientRect();
        const fx = (ev.clientX - rc.left) / rc.width, fy = (ev.clientY - rc.top) / rc.height;
        if (d.pin && d.moved && !view.pv) {
          const rel = d.pin.dataset.rel;
          const loc = toLoc(Math.min(1, Math.max(0, fx)), Math.min(1, Math.max(0, fy)));
          await api('world/place/set', { body: { rel, key: 'location', value: loc } });
          M.places.find(p => p.rel === rel).location = loc;
          sel = rel; draw();
        } else if (d.pin && !d.moved) {
          sel = d.pin.dataset.rel; pending = null; draw();
        } else if (!d.moved && adding) {
          pending = { x: fx, y: fy }; draw();
        }
      });
      viewEl.addEventListener('wheel', ev => {
        if (!ev.ctrlKey && !ev.metaKey) return;
        ev.preventDefault();
        zoom = Math.min(4, Math.max(1, zoom * (ev.deltaY < 0 ? 1.2 : 1 / 1.2)));
        if (zoom === 1) pan = [0, 0];
        inner.style.width = zoom * 100 + '%'; inner.style.transform = `translate(${pan[0]}px,${pan[1]}px)`;
      }, { passive: false });
    };
    draw();
  };

  // ======================================================================== People
  O.routes.people = async (main, r) => {
    await loadNames();
    if (r.rest) return person(main, r.rest);
    let list;
    try { list = await api('world/people'); } catch (e) { main.innerHTML = noVault(e.message); return; }
    const places = await api('world/map').then(m => m.places).catch(() => []);
    main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">World/People · ${list.length}</span><h1>People</h1></div>
      <button type="button" class="btn primary" id="newperson">${icon('plus', 18)}New person</button></header>
      <form class="card hidden" id="pform"><h2>New person</h2>
        <div class="grid2"><label class="field-l"><span class="eyebrow">Name</span><input id="nname" class="field" required></label>
        <label class="field-l"><span class="eyebrow">Role</span><input id="nrole" class="field" placeholder="Harbormaster"></label>
        <label class="field-l"><span class="eyebrow">Home</span><select id="nhome" class="field"><option value="">—</option>${places.map(p => `<option>${esc(p.name)}</option>`).join('')}</select></label></div>
        <div class="chips"><button class="btn primary" type="submit">Create</button></div><span class="err" id="nerr"></span></form>
      <div class="peoplegrid">${list.length ? list.map(p => `<a class="personcard" href="#/people/${encodeURIComponent(p.rel)}">
        ${p.image ? `<img src="${fileUrl(p.image)}" alt="">` : `<span class="mono-av">${esc(p.name[0] || '?')}</span>`}
        <span class="pn">${esc(p.name)}</span><span class="dim">${esc([p.role, p.home].filter(Boolean).join(' · ') || ' ')}</span>
        ${p.excerpt ? `<span class="px">${esc(p.excerpt)}</span>` : ''}</a>`).join('') : '<div class="empty">No one yet</div>'}</div>`;
    $('#newperson').onclick = () => { $('#pform').classList.toggle('hidden'); $('#nname').focus(); };
    $('#pform').onsubmit = async ev => {
      ev.preventDefault();
      try { const res = await api('world/person', { body: { name: $('#nname').value.trim(), role: $('#nrole').value.trim(), home: $('#nhome').value } }); O.go('#/people/' + encodeURIComponent(res.rel)); }
      catch (e) { $('#nerr').textContent = e.message; }
    };
  };

  const chats = {};
  async function person(main, rel) {
    let P;
    try { P = await api('world/person?rel=' + encodeURIComponent(rel)); } catch (e) { main.innerHTML = noVault(e.message); return; }
    const chat = chats[rel] || (chats[rel] = []);
    let busy = false;
    const draw = () => {
      const ties = {};
      P.ties.forEach(t => (ties[t.type] ||= []).push(t));
      const tieLink = t => t.rel ? `<a class="chip" href="${t.rel.startsWith('World/Places/') ? '#/map?place=' + encodeURIComponent(t.rel) : '#/people/' + encodeURIComponent(t.rel)}">${esc(t.name)}</a>` : `<span class="chip">${esc(t.name)}</span>`;
      main.innerHTML = `<div class="chips" style="font-size:14px"><a href="#/people">People</a><span class="dim">›</span><span class="dim">${esc(P.name)}</span></div>
        <header class="pagehead"><div class="chips" style="align-items:center"><span class="mono dim">${esc(P.rel)}</span></div>
          <div class="chips">${seg(view.pv)}<a class="btn" href="${O.obsidian(P.rel)}">${icon('out', 18)}Open in Obsidian</a></div></header>
        <div class="row"><article class="col-main">
          <div style="display:flex;flex-wrap:wrap;align-items:center;gap:18px">
            ${P.image ? `<img class="portrait" src="${fileUrl(P.image)}" alt="">` : `<span class="portrait mono-av big">${esc(P.name[0] || '?')}</span>`}
            <div style="display:flex;flex-direction:column;gap:6px;min-width:0;flex:1 1 260px">
              <h1 class="serif" style="font-size:44px;line-height:1.05">${esc(P.name)}</h1>
              <span style="font-size:18px;color:var(--text-2)">${esc(P.role || '')}${P.role && P.home ? ' · ' : ''}${P.home ? (P.home_rel ? `<a href="#/map?place=${encodeURIComponent(P.home_rel)}">${esc(P.home)}</a>` : esc(P.home)) : ''}</span>
              ${P.ties.length ? `<div class="chips">${Object.entries(ties).map(([k, ts]) => `<span class="eyebrow" style="align-self:center">${esc(k)}</span>${ts.map(tieLink).join('')}`).join('')}</div>` : ''}
            </div></div>
          ${view.pv ? '' : `<div class="cards3">${P.facts.map(f => `<div class="lcard"><span class="eyebrow">${esc(f.k)}</span><span>${O.noteHTML(f.v) || '<span class="dim">—</span>'}</span></div>`).join('')}</div>`}
          <section class="card"><h2>Known to the party</h2>${P.known.length ? `<ul class="points">${P.known.map(k => `<li>${O.noteHTML(k).replace(/^<p>|<\/p>$/g, '')}</li>`).join('')}</ul>` : '<span class="dim">Nothing yet</span>'}
            ${view.pv ? '' : `<form class="composer" data-add="Known to the party"><input placeholder="Add something the party knows" aria-label="Add something the party knows"><button class="btn" type="submit">${icon('plus', 16)}</button></form>`}</section>
          ${view.pv ? '' : `<section class="card" style="border-color:var(--teal-line)"><div class="cardhead"><h2>Secrets</h2><span class="chip" style="background:var(--teal-bg);color:var(--teal);border-color:var(--teal-line)">${icon('lock', 12)}DM only</span></div>
            ${P.secrets.length ? P.secrets.map((s, i) => `<div class="srcrow"><span class="what">${O.noteHTML(s).replace(/^<p>|<\/p>$/g, '')}</span><button type="button" class="btn small" data-reveal="${i}">Reveal</button></div>`).join('') : '<span class="dim">None</span>'}
            <form class="composer" data-add="Secrets"><input placeholder="Add a secret" aria-label="Add a secret"><button class="btn" type="submit">${icon('plus', 16)}</button></form></section>
          ${P.details.length ? `<section class="card"><h2>Details</h2><ul class="points">${P.details.map(k => `<li>${O.noteHTML(k).replace(/^<p>|<\/p>$/g, '')}</li>`).join('')}</ul></section>` : ''}
          ${P.notes ? `<section class="card prose">${O.noteHTML(P.notes)}</section>` : ''}
          ${Object.entries(P.extra).filter(([k, v]) => v).map(([k, v]) => `<section class="card"><h2>${esc(k)}</h2><div class="prose">${O.noteHTML(v)}</div></section>`).join('')}`}
          ${P.appears.length ? `<div class="chips"><span class="eyebrow" style="align-self:center">Appears in</span>${P.appears.map(a => `<a class="chip" href="${O.obsidian(a.rel)}">${esc(a.name)}</a>`).join('')}</div>` : ''}
        </article>
        ${view.pv || !O.ai ? '' : `<aside class="col-side"><section class="card"><div class="cardhead"><h2>Interview</h2><span class="chip brass">In character</span></div>
          <div class="chat" id="ichat">${chat.map(m => m.who === 'you' ? `<div class="bubble you">${esc(m.text)}</div>`
            : `<div class="bubble gm"><span class="who">${esc(P.name)}</span>${esc(m.text)}${m.new ? `<span class="rule">${esc(m.new)}${m.kept ? ' · kept' : ` <button type="button" class="btn small" data-keep="${chat.indexOf(m)}" style="margin-left:6px">Keep</button>`}</span>` : ''}</div>`).join('')}
            ${busy ? `<div class="typing"><span class="spinner"></span> ${esc(P.name)} is thinking</div>` : ''}</div>
          <form class="composer" id="iform"><input id="imsg" placeholder="Ask ${esc(P.name)}" aria-label="Ask ${esc(P.name)}"><button class="btn primary" type="submit" ${busy ? 'disabled' : ''} aria-label="Send">${icon('send', 18)}</button></form></section></aside>`}
        </div>`;
      bindSeg(main, draw);
      main.querySelectorAll('[data-reveal]').forEach(b => b.onclick = async () => { P = await api('world/person/reveal', { body: { rel, i: +b.dataset.reveal } }); draw(); });
      main.querySelectorAll('form[data-add]').forEach(f => f.onsubmit = async ev => {
        ev.preventDefault();
        const t = f.querySelector('input').value.trim();
        if (t) { P = await api('world/person/add', { body: { rel, where: f.dataset.add, text: t } }); draw(); }
      });
      main.querySelectorAll('[data-keep]').forEach(b => b.onclick = async () => {
        const m = chat[+b.dataset.keep];
        P = await api('world/person/add', { body: { rel, where: 'Details', text: m.new } }); m.kept = true; draw();
      });
      const f = $('#iform');
      if (f) f.onsubmit = async ev => {
        ev.preventDefault();
        const t = $('#imsg').value.trim();
        if (!t || busy) return;
        const history = chat.map(m => ({ who: m.who, text: m.text }));
        chat.push({ who: 'you', text: t }); busy = true; draw();
        try { const res = await api('world/interview', { body: { rel, message: t, history } }); chat.push({ who: 'npc', text: res.reply, new: res.new }); }
        catch (e) { chat.push({ who: 'npc', text: e.message }); }
        busy = false; draw();
        const c = $('#ichat'); if (c) c.scrollTop = c.scrollHeight;
      };
      const c = $('#ichat'); if (c) c.scrollTop = c.scrollHeight;
    };
    draw();
  }

  // ======================================================================== Table
  const COLORS = ['#7FB3D5', '#E39B5B', '#B9D58A', '#C7A4E0', '#E8D27A', '#8FD3C9'];
  const CONDITIONS = ['Blinded', 'Charmed', 'Deafened', 'Exhaustion', 'Frightened', 'Grappled', 'Incapacitated', 'Invisible', 'Paralyzed', 'Petrified', 'Poisoned', 'Prone', 'Restrained', 'Stunned', 'Unconscious'];
  const COND_ICON = { Blinded: 'blindfold', Charmed: 'charm', Deafened: 'hearing-disabled', Exhaustion: 'tired-eye', Frightened: 'terror', Grappled: 'grab', Incapacitated: 'knockout',
    Invisible: 'invisible', Paralyzed: 'frozen-body', Petrified: 'stone-bust', Poisoned: 'poison-bottle', Prone: 'falling', Restrained: 'manacles', Stunned: 'knocked-out-stars', Unconscious: 'night-sleep' };
  const health = c => c.hp <= 0 ? 'Down' : c.hp <= c.max / 2 ? 'Bloodied' : 'Unhurt';
  const initial = c => c.name.replace(/[^A-Za-z]/g, '')[0] || '?';
  const tag = c => (c.name.match(/ ([A-Z])$/) || [])[1] || '';
  const label = c => c.kind === 'pc' ? initial(c) : initial(c) + tag(c);   // "OA" for Owlbear A, "G" for a lone goblin

  function battleHTML(S, dm) {
    const g = S.grid || { cols: 24, rows: 15 };
    return `<div class="battle" style="aspect-ratio:${g.cols} / ${g.rows};--cols:${g.cols};--rows:${g.rows}">
      ${g.image ? `<img src="${fileUrl(g.image)}" alt="" draggable="false">` : ''}<div class="gridlines"></div>
      ${S.combatants.map((c, i) => `<div class="token ${c.kind} ${i === S.turn && S.started ? 'now' : ''} ${c.hp <= 0 ? 'down' : ''}" data-i="${i}"
        style="left:${(c.pos[0] + 0.5) / g.cols * 100}%;top:${(c.pos[1] + 0.5) / g.rows * 100}%;width:${100 / g.cols}%;${c.kind === 'pc' ? `background:${c.color}` : c.pic ? `background-image:url('${esc(c.pic)}')` : ''}" title="${esc(c.name)}">${c.pic ? `<span>${esc(label(c))}</span>` : esc(label(c))}</div>`).join('')}</div>`;
  }

  O.routes.table = async (main, r) => {
    if (r.rest === 'players') return players(main);
    document.body.classList.remove('tv');
    let encs, party;
    try { [encs, party] = await Promise.all([api('world/encounters'), api('world/party')]); } catch (e) { main.innerHTML = noVault(e.message); return; }
    let S = await api('table');
    if (!S.combatants) S = { combatants: [], round: 1, turn: 0, started: false, grid: { cols: 24, rows: 15, image: '' } };
    let showSB = -1, saveT = null, endMsg = '';
    const save = () => { clearTimeout(saveT); saveT = setTimeout(async () => { S = Object.assign(S, { v: (await api('table', { body: { state: S } })).v }); }, 250); };

    const load = enc => {
      const out = party.map((m, i) => ({ id: 'pc' + i, name: m.name, kind: 'pc', hp: m.hp, max: m.hp, ac: m.ac, init: m.init, roll: null, conds: [], pos: [2 + (i % 3), 5 + Math.floor(i / 3) * 2 + i % 2], color: COLORS[i % COLORS.length] }));
      let k = 0;
      enc.creatures.forEach(c => {
        for (let j = 0; j < c.n; j++) {
          out.push({ id: 'foe' + (k++), name: c.n > 1 ? `${c.name} ${String.fromCharCode(65 + j)}` : c.name, kind: 'foe', hp: c.hp, max: c.hp, ac: c.ac, init: c.init,
            roll: null, conds: [], pos: [17 + (k % 4), 3 + Math.floor(k / 4) * 2 + (k % 2)], eid: c.id, note: c.note, pic: c.pic || '', icon: c.icon || '' });
        }
      });
      S = Object.assign({ grid: S.grid || { cols: 24, rows: 15, image: '' } }, { encounter: enc.rel, name: enc.name, combatants: out, round: 1, turn: 0, started: false });
      showSB = -1; endMsg = ''; save(); draw();
    };

    const draw = () => {
      const C = S.combatants;
      const cur = C[S.turn];
      main.innerHTML = `<header class="pagehead"><div><span class="eyebrow">${esc(S.name || 'No encounter loaded')}${S.started ? ` · Round ${S.round}` : ''}</span><h1>Table</h1></div>
        <div class="chips"><select class="field" id="encsel" aria-label="Encounter">${encs.map(e => `<option value="${esc(e.rel)}" ${e.rel === S.encounter ? 'selected' : ''}>${esc(e.name)} · ${e.creatures.reduce((a, c) => a + c.n, 0)}</option>`).join('')}</select>
          <button type="button" class="btn" id="encload" ${encs.length ? '' : 'disabled'}>Load</button>
          <button type="button" class="btn" id="partybtn">${icon('people', 18)}Party · ${party.length}</button>
          <a class="btn" href="#/table/players" target="_blank" rel="noopener">${icon('table', 18)}Players' screen</a></div></header>
        <form class="card hidden" id="partyform"><div class="cardhead"><h2>The party</h2><span class="mono dim">World/Party.md</span></div>
          <div id="prows" style="display:flex;flex-direction:column;gap:6px">${(party.length ? party : [{ name: '', hp: 10, ac: 12, init: 0 }]).map(prow).join('')}</div>
          <div class="chips"><button type="button" class="btn small" id="padd">${icon('plus', 14)}Add</button><button class="btn primary small" type="submit">Save</button></div></form>
        ${C.length ? `<div class="row"><section style="flex:999 1 560px;min-width:0;display:flex;flex-direction:column;gap:12px">${battleHTML(S, true)}
          <div class="chips"><button type="button" class="btn primary" id="rollinit">${icon('d20', 18)}${S.started ? 'Reroll initiative' : 'Roll initiative'}</button>
            <button type="button" class="btn" id="prev" ${S.started ? '' : 'disabled'}>Back</button><button type="button" class="btn primary" id="next" ${S.started ? '' : 'disabled'}>Next turn</button>
            <span class="dim" style="align-self:center">${S.started && cur ? `${esc(cur.name)}’s turn` : ''}</span>
            <button type="button" class="btn" id="endenc" style="margin-left:auto">End encounter</button></div>
          ${endMsg ? `<div class="done"><b>Written to the note</b><span class="mono dim" style="flex-basis:100%">${esc(endMsg)}</span></div>` : ''}
          ${showSB >= 0 ? '<div id="sbpanel"></div>' : ''}</section>
          <aside class="initlist" style="flex:1 1 300px;min-width:0">${C.map((c, i) => `<div class="initrow ${i === S.turn && S.started ? 'now' : ''} ${c.hp <= 0 ? 'down' : ''}">
            <input class="initnum" type="number" value="${c.roll ?? ''}" data-roll="${i}" aria-label="Initiative for ${esc(c.name)}" placeholder="${c.init >= 0 ? '+' : ''}${c.init}">
            <span class="av ${c.kind}" style="${c.kind === 'pc' ? 'background:' + c.color : c.pic ? `background-image:url('${esc(c.pic)}')` : ''}">${c.kind !== 'pc' && c.pic ? `<span>${esc(label(c))}</span>` : esc(label(c))}</span>
            <div class="who"><span class="nm">${esc(c.name)} <span class="dim">AC ${c.ac}</span></span>
              <span class="hpbar"><i style="width:${Math.max(0, Math.min(100, c.hp / c.max * 100))}%;background:${c.hp > c.max / 2 ? '#9BC48A' : c.hp > c.max / 4 ? '#E0A84A' : '#E07A5F'}"></i></span>
              <span class="chips">${c.conds.map((k, j) => `<button type="button" class="chip" data-uncond="${i}:${j}" title="Remove">${O.gi(COND_ICON[k], 16)}${esc(k)} ×</button>`).join('')}
                <select class="cond" data-cond="${i}" aria-label="Add a condition"><option value="">+ condition</option>${CONDITIONS.map(k => `<option>${k}</option>`).join('')}</select></span></div>
            <div class="hpctl"><span>${c.hp}/${c.max}</span><input type="number" min="1" value="" placeholder="0" data-amt="${i}" aria-label="Amount for ${esc(c.name)}">
              <button type="button" class="btn small" data-dmg="${i}">Hit</button><button type="button" class="btn small" data-heal="${i}">Heal</button>
              ${c.kind === 'foe' ? `<button type="button" class="btn small" data-sb="${i}">Stats</button>` : ''}</div></div>`).join('')}</aside></div>`
          : `<div class="empty">${encs.length ? 'Load an encounter' : 'No encounters in World/Encounters. Add monsters from their Codex pages.'}</div>`}`;
      wire();
      if (showSB >= 0) statblock(showSB);
    };
    const prow = m => `<div class="chips prow"><input class="field" value="${esc(m.name)}" placeholder="Name" data-f="name" style="flex:2 1 140px">
      <label class="dim">HP <input class="field n" type="number" value="${m.hp}" data-f="hp"></label><label class="dim">AC <input class="field n" type="number" value="${m.ac}" data-f="ac"></label>
      <label class="dim">Init <input class="field n" type="number" value="${m.init}" data-f="init"></label><button type="button" class="btn small" data-prm>×</button></div>`;

    async function statblock(i) {
      const c = S.combatants[i], el = $('#sbpanel');
      if (!el) return;
      if (c.eid) { const e = await api('entry/' + c.eid).catch(() => null); el.innerHTML = e ? O.statblock(e) : ''; }
      else el.innerHTML = c.note ? `<a class="btn" href="${O.obsidian(c.note)}">${icon('out', 18)}Open ${esc(c.name)} in Obsidian</a>` : '';
    }

    const wire = () => {
      $('#encload').onclick = () => { const e = encs.find(x => x.rel === $('#encsel').value); if (e) load(e); };
      $('#partybtn').onclick = () => $('#partyform').classList.toggle('hidden');
      $('#padd').onclick = () => $('#prows').insertAdjacentHTML('beforeend', prow({ name: '', hp: 10, ac: 12, init: 0 }));
      $('#prows').onclick = ev => { const b = ev.target.closest('[data-prm]'); if (b) b.closest('.prow').remove(); };
      $('#partyform').onsubmit = async ev => {
        ev.preventDefault();
        const members = [...main.querySelectorAll('.prow')].map(rw => Object.fromEntries([...rw.querySelectorAll('[data-f]')].map(x => [x.dataset.f, x.dataset.f === 'name' ? x.value.trim() : +x.value])));
        party = await api('world/party', { body: { members } }); draw();
      };
      if (!S.combatants.length) return;
      $('#rollinit').onclick = () => {
        S.combatants.forEach(c => { c.roll = O.rollDice(1, 20)[0] + c.init; });
        S.combatants.sort((a, b) => b.roll - a.roll || b.init - a.init);
        S.turn = 0; S.round = 1; S.started = true; save(); draw();
      };
      $('#next').onclick = () => { const n = S.combatants.length; do { S.turn = (S.turn + 1) % n; if (S.turn === 0) S.round++; } while (S.combatants[S.turn].hp <= 0 && S.combatants[S.turn].kind === 'foe' && S.combatants.some(c => c.hp > 0)); save(); draw(); };
      $('#prev').onclick = () => { const n = S.combatants.length; if (S.turn === 0) { if (S.round > 1) { S.round--; S.turn = n - 1; } } else S.turn--; save(); draw(); };
      $('#endenc').onclick = async () => { const res = await api('table/end', { body: { state: S } }); endMsg = (res.note ? res.note + ': ' : '') + (res.written || []).join(' '); S = { combatants: [], round: 1, turn: 0, started: false, grid: S.grid }; draw(); };
      main.querySelectorAll('[data-roll]').forEach(inp => inp.onchange = () => { S.combatants[+inp.dataset.roll].roll = inp.value === '' ? null : +inp.value; S.combatants.sort((a, b) => (b.roll ?? -99) - (a.roll ?? -99)); save(); draw(); });
      const amt = i => Math.max(0, +(main.querySelector(`[data-amt="${i}"]`).value || 0));
      main.querySelectorAll('[data-dmg]').forEach(b => b.onclick = () => { const c = S.combatants[+b.dataset.dmg]; c.hp = Math.max(c.kind === 'pc' ? 0 : -999, c.hp - amt(+b.dataset.dmg)); if (c.hp < 0) c.hp = 0; save(); draw(); });
      main.querySelectorAll('[data-heal]').forEach(b => b.onclick = () => { const c = S.combatants[+b.dataset.heal]; c.hp = Math.min(c.max, c.hp + amt(+b.dataset.heal)); save(); draw(); });
      main.querySelectorAll('[data-cond]').forEach(s => s.onchange = () => { if (s.value) { const c = S.combatants[+s.dataset.cond]; if (!c.conds.includes(s.value)) c.conds.push(s.value); save(); draw(); } });
      main.querySelectorAll('[data-uncond]').forEach(b => b.onclick = () => { const [i, j] = b.dataset.uncond.split(':').map(Number); S.combatants[i].conds.splice(j, 1); save(); draw(); });
      main.querySelectorAll('[data-sb]').forEach(b => b.onclick = () => { showSB = showSB === +b.dataset.sb ? -1 : +b.dataset.sb; draw(); });
      // Drag tokens on the grid; they snap to squares.
      const bt = $('.battle'); let dg = null;
      bt.addEventListener('pointerdown', ev => { const t = ev.target.closest('.token'); if (!t) return; dg = { t, i: +t.dataset.i }; bt.setPointerCapture(ev.pointerId); });
      bt.addEventListener('pointermove', ev => { if (!dg) return; const rc = bt.getBoundingClientRect(); dg.t.style.left = ((ev.clientX - rc.left) / rc.width * 100) + '%'; dg.t.style.top = ((ev.clientY - rc.top) / rc.height * 100) + '%'; });
      bt.addEventListener('pointerup', ev => {
        if (!dg) return;
        const rc = bt.getBoundingClientRect(), g = S.grid || { cols: 24, rows: 15 };
        const c = S.combatants[dg.i];
        c.pos = [Math.max(0, Math.min(g.cols - 1, Math.floor((ev.clientX - rc.left) / rc.width * g.cols))), Math.max(0, Math.min(g.rows - 1, Math.floor((ev.clientY - rc.top) / rc.height * g.rows)))];
        dg = null; save(); draw();
      });
    };
    draw();
  };

  // The players' screen: the table as the TV shows it. It follows the DM's table every second and a half.
  async function players(main) {
    document.body.classList.add('tv');
    let v = -1, alive = true;
    const tick = async () => {
      if (!alive || !document.body.classList.contains('tv')) return;
      try {
        const S = await api('table');
        if (S.v !== v) { v = S.v; draw(S); }
      } catch (e) { /* signed out or offline: try again */ }
      setTimeout(tick, 1500);
    };
    const draw = S => {
      if (!S.combatants || !S.combatants.length) { main.innerHTML = '<div class="tvwait"><span class="serif">Olam</span></div>'; return; }
      const C = S.combatants, cur = C[S.turn], nxt = C.slice(S.turn + 1).concat(C.slice(0, S.turn)).find(c => c.hp > 0 || c.kind === 'pc');
      main.innerHTML = `<div class="tvwrap"><section class="tvmap">${battleHTML(S, false)}
          ${S.started && cur ? `<div class="tvbanner"><b>${esc(cur.name)}’s turn</b><span>${nxt ? 'Next: ' + esc(nxt.name) : ''}</span></div>` : ''}</section>
        <aside class="tvinit"><div class="cardhead"><h2>Initiative</h2><span class="dim">${S.started ? 'Round ' + S.round : ''}</span></div>
          ${C.map((c, i) => `<div class="initrow ${i === S.turn && S.started ? 'now' : ''} ${c.hp <= 0 ? 'down' : ''}">
            <span class="av ${c.kind}" style="${c.kind === 'pc' ? 'background:' + c.color : c.pic ? `background-image:url('${esc(c.pic)}')` : ''}">${c.kind !== 'pc' && c.pic ? `<span>${esc(label(c))}</span>` : esc(label(c))}</span>
            <div class="who"><span class="nm">${esc(c.name)}</span>
              ${c.kind === 'pc' ? `<span class="hpbar"><i style="width:${Math.max(0, c.hp / c.max * 100)}%;background:${c.hp > c.max / 2 ? '#9BC48A' : c.hp > c.max / 4 ? '#E0A84A' : '#E07A5F'}"></i></span><span class="dim">${c.hp} / ${c.max}</span>`
                : `<span style="color:${health(c) === 'Unhurt' ? 'var(--dim)' : 'var(--red)'}">${health(c)}</span>`}
              ${c.conds.length ? `<span class="chips">${c.conds.map(k => `<span class="chip">${esc(k)}</span>`).join('')}</span>` : ''}</div>
            ${i === S.turn && S.started ? '<span class="chip brass">Now</span>' : ''}</div>`).join('')}</aside></div>`;
    };
    window.addEventListener('hashchange', () => { alive = false; document.body.classList.remove('tv'); }, { once: true });
    tick();
  }
})();
