/* Прототип «Дом за 3 дня» — комментарии-пины (как в Figma).
   Тап в любое место → пин с комментарием. Хранение: comments.php на сервере. */
(function () {
  var PAGE = location.pathname.split('/').pop() || 'index.html';
  var API = 'comments.php';
  var placing = false;
  var items = [];
  var sections = [];
  var fab, listBtn;

  function api(method, body) {
    return fetch(API, {
      method: method,
      headers: method === 'POST' ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined
    }).then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); });
  }

  // локальный запас — когда сервера (comments.php) нет, напр. на GitHub Pages
  var LSK = 'proto-cmt-' + PAGE;
  function lsGet() { try { return JSON.parse(localStorage.getItem(LSK) || '[]'); } catch (e) { return []; } }
  function lsSet(a) { try { localStorage.setItem(LSK, JSON.stringify(a)); } catch (e) { } }
  function lsAdd(c) {
    c.id = c.id || ('L' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6));
    c.replies = c.replies || [];
    var a = lsGet(); a.push(c); lsSet(a); return c;
  }
  function lsReply(id, text) {
    var a = lsGet();
    for (var i = 0; i < a.length; i++) {
      if (a[i].id === id) { (a[i].replies = a[i].replies || []).push({ text: text, author: 'gleb', ts: Date.now() }); }
    }
    lsSet(a);
  }
  function lsDelete(id) { lsSet(lsGet().filter(function (c) { return c.id !== id; })); }

  function lsReplyDelete(id, ri) {
    var a = lsGet();
    for (var i = 0; i < a.length; i++) {
      if (a[i].id === id && a[i].replies && a[i].replies[ri] != null) a[i].replies.splice(ri, 1);
    }
    lsSet(a);
  }

  // удаление: локальные (id начинается с L) — только localStorage,
  // серверные — POST delete, при недоступности сети тоже локально
  function removeComment(id) {
    if (id.charAt(0) === 'L') { lsDelete(id); return reload(); }
    return api('POST', { action: 'delete', id: id })
      .then(reload).catch(function () { lsDelete(id); return reload(); });
  }
  function removeReply(id, ri) {
    if (id.charAt(0) === 'L') { lsReplyDelete(id, ri); return reload(); }
    return api('POST', { action: 'reply_delete', id: id, ri: ri })
      .then(reload).catch(function () { lsReplyDelete(id, ri); return reload(); });
  }
  function el(t, c, h) { var e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[m]; }); }
  function fmt(ts) { try { return new Date(ts).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); } catch (e) { return ''; } }

  function locate(cx, cy) {
    var best = null, bi = -1, i;
    for (i = 0; i < sections.length; i++) {
      var r = sections[i].getBoundingClientRect();
      if (cy >= r.top && cy <= r.bottom) { best = sections[i]; bi = i; break; }
    }
    if (!best) {
      var dmin = Infinity;
      for (i = 0; i < sections.length; i++) {
        var rr = sections[i].getBoundingClientRect();
        var d = Math.abs((rr.top + rr.bottom) / 2 - cy);
        if (d < dmin) { dmin = d; best = sections[i]; bi = i; }
      }
    }
    var rect = best.getBoundingClientRect();
    var lbl = best.querySelector('.sec-label');
    return {
      bi: bi,
      block: (lbl ? lbl.textContent : 'Блок').trim(),
      rx: Math.min(1, Math.max(0, (cx - rect.left) / rect.width)),
      ry: Math.min(1, Math.max(0, (cy - rect.top) / rect.height))
    };
  }

  function renderPin(c, idx) {
    var host = sections[c.bi];
    if (!host) return;
    var pin = el('button', 'cpin', String(idx + 1));
    pin.type = 'button';
    pin.style.left = (c.rx * 100) + '%';
    pin.style.top = (c.ry * 100) + '%';
    pin.dataset.id = c.id;
    if ((c.replies || []).length) pin.classList.add('answered');
    pin.onclick = function (ev) { ev.stopPropagation(); openThread(c, pin); };
    host.appendChild(pin);
  }

  function renderAll() {
    var n = document.querySelectorAll('.cpin');
    for (var i = 0; i < n.length; i++) n[i].remove();
    items.forEach(renderPin);
    listBtn.textContent = 'Комментарии (' + items.length + ')';
    listBtn.hidden = items.length === 0;
  }

  function closePopovers() {
    var n = document.querySelectorAll('.cthread,.cform,.clist');
    for (var i = 0; i < n.length; i++) n[i].remove();
  }

  function clamp(pop) {
    var r = pop.getBoundingClientRect(), pad = 10;
    if (r.right > innerWidth - pad) pop.style.left = (scrollX + innerWidth - r.width - pad) + 'px';
    if (r.left < pad) pop.style.left = (scrollX + pad) + 'px';
    if (r.bottom > innerHeight - pad) pop.style.top = (scrollY + innerHeight - r.height - pad) + 'px';
    if (r.top < pad) pop.style.top = (scrollY + pad) + 'px';
  }

  function openForm(cx, cy, px, py) {
    closePopovers();
    var loc = locate(cx, cy);
    var f = el('div', 'cform');
    f.innerHTML =
      '<div class="cthead"><b>Новый комментарий</b><span class="cx">&times;</span></div>' +
      '<div class="cwho">' + esc(loc.block) + '</div>' +
      '<textarea placeholder="Что поправить в этом месте?"></textarea>' +
      '<button class="csend" type="button">Отправить</button>';
    f.style.left = px + 'px';
    f.style.top = py + 'px';
    document.body.appendChild(f);
    clamp(f);
    var ta = f.querySelector('textarea'); ta.focus();
    f.querySelector('.cx').onclick = function () { f.remove(); setPlacing(false); };
    f.querySelector('.csend').onclick = function () {
      var t = ta.value.trim();
      if (!t) { ta.focus(); return; }
      var btn = f.querySelector('.csend'); btn.disabled = true; btn.textContent = '…';
      var rec = { action: 'add', page: PAGE, bi: loc.bi, block: loc.block, rx: loc.rx, ry: loc.ry, text: t };
      api('POST', rec)
        .then(reload).then(function () { f.remove(); setPlacing(false); })
        .catch(function () {
          lsAdd({ page: PAGE, bi: loc.bi, block: loc.block, rx: loc.rx, ry: loc.ry, text: t, author: 'client', ts: Date.now() });
          reload().then(function () { f.remove(); setPlacing(false); });
        });
    };
  }

  function openThread(c, anchorEl) {
    closePopovers();
    var pop = el('div', 'cthread');
    var h = '<div class="cthead"><b>Комментарий</b>'
      + '<span class="cactions"><span class="cdel" title="Удалить весь комментарий">Удалить</span>'
      + '<span class="cx">&times;</span></span></div>';
    h += '<div class="cmsg"><span class="cwho">Клиент · ' + fmt(c.ts) + '</span><p>' + esc(c.text) + '</p></div>';
    (c.replies || []).forEach(function (r, ri) {
      var who = r.author === 'client' ? 'Клиент' : 'Глеб';
      h += '<div class="cmsg reply"><span class="cwho">' + who + ' · ' + fmt(r.ts)
        + '<span class="crdel" data-ri="' + ri + '" title="Удалить ответ">×</span></span><p>' + esc(r.text) + '</p></div>';
    });
    h += '<textarea placeholder="Ответить…"></textarea><button class="csend" type="button">Ответить</button>';
    pop.innerHTML = h;
    var r = anchorEl.getBoundingClientRect();
    pop.style.left = (scrollX + r.left + 22) + 'px';
    pop.style.top = (scrollY + r.top - 6) + 'px';
    document.body.appendChild(pop);
    clamp(pop);
    pop.querySelector('.cx').onclick = closePopovers;
    pop.querySelector('.cdel').onclick = function () {
      if (confirm('Удалить этот комментарий?')) removeComment(c.id).then(closePopovers);
    };
    var rdels = pop.querySelectorAll('.crdel');
    for (var k = 0; k < rdels.length; k++) {
      rdels[k].onclick = function () {
        if (confirm('Удалить этот ответ?')) removeReply(c.id, parseInt(this.dataset.ri, 10)).then(closePopovers);
      };
    }
    pop.querySelector('.csend').onclick = function () {
      var t = pop.querySelector('textarea').value.trim();
      if (!t) return;
      var btn = pop.querySelector('.csend'); btn.disabled = true; btn.textContent = '…';
      api('POST', { action: 'reply', id: c.id, text: t }).then(reload).then(closePopovers)
        .catch(function () { lsReply(c.id, t); reload().then(closePopovers); });
    };
  }

  function openList() {
    closePopovers();
    var p = el('div', 'clist');
    var h = '<div class="cthead"><b>Комментарии</b><span class="cx">&times;</span></div>';
    if (!items.length) h += '<p class="cempty">Пока пусто</p>';
    items.forEach(function (c, i) {
      h += '<div class="clrow" data-id="' + c.id + '"><span class="cltxt"><b>' + (i + 1) + '.</b> ' + esc(c.text.slice(0, 90)) +
        '<span class="cwho">' + esc(c.block || '') + ' · ' + fmt(c.ts) + ((c.replies || []).length ? ' · ответов: ' + c.replies.length : '') + '</span></span>' +
        '<span class="cldel" title="Удалить">&times;</span></div>';
    });
    p.innerHTML = h;
    document.body.appendChild(p);
    p.querySelector('.cx').onclick = function () { p.remove(); };

    var rows = p.querySelectorAll('.clrow');
    for (var i = 0; i < rows.length; i++) {
      rows[i].querySelector('.cltxt').onclick = function () {
        var id = this.parentNode.dataset.id;
        var pin = document.querySelector('.cpin[data-id="' + id + '"]');
        if (pin) {
          pin.scrollIntoView({ behavior: 'smooth', block: 'center' });
          pin.classList.add('flash');
          setTimeout(function () { pin.classList.remove('flash'); }, 1500);
        }
        p.remove();
      };
      rows[i].querySelector('.cldel').onclick = function (e) {
        e.stopPropagation();
        var id = this.parentNode.dataset.id;
        if (confirm('Удалить этот комментарий?')) { removeComment(id); this.parentNode.remove(); }
      };
    }
  }

  function reload() {
    return api('GET').then(function (all) {
      var server = (all || []).filter(function (c) { return c.page === PAGE; });
      items = server.concat(lsGet());
      renderAll();
    }).catch(function () {
      items = lsGet();
      renderAll();
    });
  }

  function setPlacing(on) {
    placing = on;
    document.body.classList.toggle('cplacing', on);
    fab.classList.toggle('on', on);
    fab.innerHTML = on ? '&times; Отмена' : '&#128172; Комментировать';
  }

  function init() {
    sections = Array.prototype.slice.call(document.querySelectorAll('main section'));

    fab = el('button', 'cfab', '&#128172; Комментировать');
    fab.type = 'button';
    fab.onclick = function () { setPlacing(!placing); };
    document.body.appendChild(fab);

    listBtn = el('button', 'clistbtn', 'Комментарии (0)');
    listBtn.type = 'button';
    listBtn.hidden = true;
    listBtn.onclick = openList;
    document.body.appendChild(listBtn);

    document.addEventListener('click', function (e) {
      if (!placing) return;
      if (e.target.closest('.cfab,.clistbtn,.cform,.cthread,.clist,.cpin')) return;
      e.preventDefault();
      e.stopPropagation();
      openForm(e.clientX, e.clientY, e.pageX, e.pageY);
    }, true);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { closePopovers(); setPlacing(false); }
    });

    reload();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  var css = document.createElement('style');
  css.textContent = [
    '.cfab,.clistbtn{position:fixed;right:14px;z-index:9999;border:0;border-radius:999px;',
    'font:600 13.5px/1 -apple-system,Segoe UI,Roboto,Arial,sans-serif;cursor:pointer}',
    '.cfab{bottom:14px;background:#111;color:#fff;padding:12px 17px;box-shadow:0 6px 22px rgba(0,0,0,.28)}',
    '.cfab.on{background:#b3261e}',
    '.clistbtn{bottom:64px;background:#fff;color:#333;border:1px solid #ddd;padding:9px 14px;box-shadow:0 4px 16px rgba(0,0,0,.16)}',
    'body.cplacing,body.cplacing *{cursor:crosshair!important}',
    '.cpin{position:absolute;transform:translate(-50%,-50%);width:26px;height:26px;',
    'border-radius:50% 50% 50% 3px;background:#b3261e;color:#fff;border:2px solid #fff;',
    'font:700 12px/1 sans-serif;cursor:pointer;z-index:45;box-shadow:0 2px 8px rgba(0,0,0,.35)}',
    '.cpin.answered{background:#1f7a3d}',
    '.cpin.flash{animation:cflash 1.4s ease}',
    '@keyframes cflash{0%,100%{box-shadow:0 2px 8px rgba(0,0,0,.35)}40%{box-shadow:0 0 0 9px rgba(179,38,30,.35)}}',
    '.cform,.cthread{position:absolute;z-index:9998;background:#fff;border:1px solid #ccc;',
    'border-radius:12px;box-shadow:0 14px 44px rgba(0,0,0,.24);padding:13px;width:290px;',
    'font:14px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#111}',
    '.clist{position:fixed;right:14px;bottom:110px;z-index:9998;background:#fff;border:1px solid #ccc;',
    'border-radius:12px;box-shadow:0 14px 44px rgba(0,0,0,.24);padding:13px;width:330px;max-height:62vh;overflow:auto;',
    'font:14px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#111}',
    '.cthead{display:flex;justify-content:space-between;align-items:center;margin:0 0 8px;font-size:13px}',
    '.cactions{display:flex;align-items:center;gap:10px}',
    '.cx{cursor:pointer;color:#999;font-size:18px;line-height:1;padding:0 2px}.cx:hover{color:#111}',
    '.cdel{cursor:pointer;color:#b3261e;font-size:11.5px;font-weight:600}.cdel:hover{text-decoration:underline}',
    '.cwho{display:block;font-size:11px;color:#999;margin:0 0 4px}',
    '.cmsg{background:#f5f5f5;border-radius:8px;padding:8px 10px;margin:0 0 7px}',
    '.cmsg.reply{background:#eef3ff}.cmsg p{margin:0;font-size:13.5px}',
    '.crdel{float:right;cursor:pointer;color:#b3261e;font-size:14px;line-height:1;padding:0 2px}',
    '.crdel:hover{color:#7a1a15}',
    '.cform textarea,.cthread textarea{width:100%;min-height:62px;border:1px solid #d5d5d5;',
    'border-radius:8px;padding:8px;font:inherit;font-size:13.5px;resize:vertical;box-sizing:border-box}',
    '.csend{margin-top:8px;width:100%;background:#111;color:#fff;border:0;border-radius:8px;',
    'padding:9px;font:600 13px/1 -apple-system,Segoe UI,Roboto,Arial,sans-serif;cursor:pointer}',
    '.csend:disabled{opacity:.6}',
    '.clrow{padding:9px 4px;border-top:1px solid #eee;font-size:13px;display:flex;gap:8px;align-items:flex-start}',
    '.clrow:first-of-type{border-top:0}.clrow:hover{background:#f6f6f6}',
    '.cltxt{flex:1;cursor:pointer;min-width:0}',
    '.cldel{cursor:pointer;color:#b3261e;font-size:16px;line-height:1;padding:0 2px;flex:none}',
    '.cldel:hover{color:#7a1a15}',
    '.cempty{color:#999;font-size:13px;text-align:center;padding:14px 0}',
    '@media(max-width:640px){',
    '.cform,.cthread{position:fixed;left:8px!important;right:8px;top:auto!important;bottom:8px;width:auto}',
    '.clist{left:8px;right:8px;width:auto;bottom:116px}',
    '.cfab{right:8px;bottom:8px}.clistbtn{right:8px;bottom:58px}',
    '.cform textarea,.cthread textarea{font-size:16px}}'
  ].join('');
  document.head.appendChild(css);
})();
