let APPS = [], SOURCES = [], USEPROXY = false, FILTER = 'all', CAT = '', CUR = null, TASK = null, POLL = null;

const $ = s => document.querySelector(s);
const el = (id) => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fmt = b => b > 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';

function toast(m) {
  const t = el('toast'); t.textContent = m; t.classList.add('on');
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('on'), 2200);
}

async function api(path, opt) {
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

async function load(force) {
  el('loading').style.display = 'block';
  el('grid').style.display = 'none';
  el('empty').style.display = 'none';
  try {
    const d = await api('/api/apps' + (force ? '?t=' + Date.now() : ''));
    APPS = d.apps || []; SOURCES = d.sources || []; USEPROXY = !!d.useProxy;
    el('ver').textContent = 'v' + (d.version || '');
    el('pxbtn').textContent = '加速：' + (USEPROXY ? '开' : '关');
    renderSources(); renderCats(); renderCounts(); render();
    el('loading').style.display = 'none';
    el('grid').style.display = 'grid';
  } catch (e) {
    el('loading').innerHTML = '⚠️ 获取失败：' + esc(e.message) +
      '<div style="margin-top:12px"><button class="btn btn-p" onclick="load(true)">重试</button></div>';
  }
}

function renderSources() {
  el('srcbar').innerHTML = SOURCES.map(s =>
    `<span class="dot ${s.ok ? '' : 'err'}"></span><b>${esc(s.name)}</b>
     <span style="color:#8b949e">${s.ok ? s.appCount + ' 个应用' : '不可用：' + esc(s.error || '')}</span>`
  ).join('<span style="color:#d0d7de">|</span>') || '<span style="color:#8b949e">未配置应用源</span>';
}

function allCats() {
  const m = {};
  APPS.forEach(a => (a.cats || []).forEach(c => m[c] = (m[c] || 0) + 1));
  return m;
}
function renderCats() {
  const m = allCats();
  el('cats').innerHTML = Object.entries(m).map(([c, n]) =>
    `<div class="nav-i ${CAT === c ? 'on' : ''}" data-cat="${esc(c)}">
       <span class="n">${esc(c)}</span><span class="c">${n}</span></div>`).join('');
  el('cats').querySelectorAll('.nav-i').forEach(i =>
    i.onclick = () => { CAT = (CAT === i.dataset.cat ? '' : i.dataset.cat); FILTER = 'all'; renderCats(); render(); });
}
function renderCounts() {
  el('c-all').textContent = APPS.length;
  el('c-in').textContent = APPS.filter(a => a.installed).length;
  el('c-up').textContent = APPS.filter(a => a.canUpdate).length;
}

function match(a) {
  if (CAT && !(a.cats || []).includes(CAT)) return false;
  if (FILTER === 'installed' && !a.installed) return false;
  if (FILTER === 'update' && !a.canUpdate) return false;
  const q = el('q').value.trim().toLowerCase();
  if (q && !(a.name + a.id + a.desc).toLowerCase().includes(q)) return false;
  return true;
}

function actionBtn(a) {
  if (a.canUpdate) return `<button class="btn btn-p btn-s" onclick="event.stopPropagation();install('${a.id}')">更新</button>
    ${a.openUrl ? `<a class="btn btn-s" href="${a.openUrl}" target="_blank" onclick="event.stopPropagation()">打开</a>` : ''}`;
  if (a.installed) return (a.openUrl ? `<a class="btn btn-p btn-s" href="${a.openUrl}" target="_blank" onclick="event.stopPropagation()">打开</a>` :
    `<span class="tag tag-in" style="padding:5px 10px">已安装</span>`) +
    `<button class="btn btn-s" onclick="event.stopPropagation();install('${a.id}')">重装</button>`;
  return `<button class="btn btn-p btn-s" onclick="event.stopPropagation();install('${a.id}')">安装</button>`;
}

function render() {
  const list = APPS.filter(match);
  el('empty').style.display = list.length ? 'none' : 'block';
  el('grid').innerHTML = list.map(a => `
    <div class="card" onclick="detail('${a.id}')">
      <img class="ic" src="${esc(a.icon)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">
      <div class="ci">
        <div class="cn">${esc(a.name)}
          ${a.installed ? (a.canUpdate ? '<span class="tag tag-up">可更新</span>' : '<span class="tag tag-in">已安装</span>') : ''}</div>
        <div class="cd">${esc(a.desc)}</div>
        <div class="cm">
          <span class="v">v${esc(a.version)}</span><span>${fmt(a.size)}</span>
          ${a.updated ? '<span>' + esc(a.updated) + '</span>' : ''}
          ${a.source ? '<span style="margin-left:auto">' + esc(a.source) + '</span>' : ''}
        </div>
        <div class="cact">${actionBtn(a)}</div>
      </div>
    </div>`).join('');
}

function detail(id) {
  const a = APPS.find(x => x.id === id); if (!a) return;
  const shots = (a.previews || []).length
    ? `<div class="shots">${a.previews.map(p => `<img src="${esc(p)}" loading="lazy">`).join('')}</div>` : '';
  el('modal').innerHTML = `
    <div class="mh">
      <img src="${esc(a.icon)}" alt="">
      <div><h2>${esc(a.name)}</h2>
        <div class="ms">${esc((a.cats || []).join(' · '))} · v${esc(a.version)} · ${fmt(a.size)}
          ${a.installed ? ' · 已安装 ' + esc(a.installedVersion || '') : ''}</div></div>
      <button class="x" onclick="closeM()">&times;</button>
    </div>
    <div class="mb">
      ${shots}
      <div class="st">简介</div><div class="desc">${esc(a.desc)}</div>
      ${a.changelog ? `<div class="st">更新日志 v${esc(a.version)}</div><div class="log">${esc(a.changelog)}</div>` : ''}
      <div class="st">信息</div>
      <div class="kv">
        <b>包名</b><span>${esc(a.id)}</span>
        <b>来源</b><span>${esc(a.source)}</span>
        <b>更新</b><span>${esc(a.updated || '-')}</span>
        <b>大小</b><span>${fmt(a.size)}</span>
      </div>
      <div class="mf">${actionBtn(a)}
        <button class="btn btn-s" onclick="copy('${esc(a.downloadRaw)}')">复制下载地址</button>
      </div>
    </div>`;
  el('mask').classList.add('on');
}
function closeM() { el('mask').classList.remove('on'); }
function copy(t) {
  navigator.clipboard.writeText(t).then(() => toast('已复制下载地址'), () => toast('复制失败'));
}

async function install(id) {
  const a = APPS.find(x => x.id === id); if (!a) return;
  if (CUR) return toast('有安装任务正在进行');
  closeM();
  CUR = a;
  el('prog').classList.add('on');
  el('p-name').textContent = '安装 ' + a.name;
  el('p-bar').style.width = '0%'; el('p-pct').textContent = '0%'; el('p-log').textContent = '';
  try {
    const r = await api('/api/install', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app: a })
    });
    TASK = r.task;
    clearInterval(POLL); POLL = setInterval(poll, 800); poll();
  } catch (e) { toast('安装请求失败：' + e.message); el('prog').classList.remove('on'); CUR = null; }
}

async function poll() {
  if (!TASK) return;
  try {
    const d = await api('/api/task?id=' + TASK);
    const t = d.task; if (!t) return;
    el('p-pct').textContent = t.phase === 'done' ? '完成' : (t.percent || 0) + '%';
    el('p-bar').style.width = (t.phase === 'done' ? 100 : (t.percent || 0)) + '%';
    const lines = (t.log || '').trim().split('\n');
    el('p-log').textContent = lines.slice(-6).join('\n');
    el('p-log').scrollTop = el('p-log').scrollHeight;
    if (t.phase === 'done') {
      clearInterval(POLL); TASK = null; CUR = null;
      setTimeout(() => el('prog').classList.remove('on'), 1500);
      toast('安装完成');
      load(true);
    } else if (t.phase === 'error') {
      clearInterval(POLL); TASK = null; CUR = null;
      el('p-log').textContent = (t.log || '') + '\n错误：' + (t.error || '');
      el('p-pct').textContent = '失败';
      setTimeout(() => el('prog').classList.remove('on'), 6000);
      toast('安装失败：' + (t.error || '').slice(0, 60));
    }
  } catch (e) {}
}

async function toggleProxy() {
  try {
    await api('/api/config', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ useProxy: !USEPROXY })
    });
    toast(USEPROXY ? '已关闭加速' : '已开启加速');
    load(true);
  } catch (e) { toast('设置失败'); }
}

function srcMgr() {
  el('modal').innerHTML = `
    <div class="mh"><div><h2>应用源管理</h2>
      <div class="ms">索引地址指向一个 fnpack.json</div></div>
      <button class="x" onclick="closeM()">&times;</button></div>
    <div class="mb">
      ${SOURCES.map((s, i) => `
        <div style="display:flex;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid #eef0f3">
          <span class="dot ${s.ok ? '' : 'err'}"></span>
          <div style="flex:1;min-width:0">
            <div style="font-size:13.5px;font-weight:600">${esc(s.name)}</div>
            <div style="font-size:11.5px;color:#8b949e;word-break:break-all">${esc(s.url)}</div>
          </div>
          <button class="btn btn-s" onclick="delSrc(${i})">删除</button>
        </div>`).join('')}
      <div class="st">添加应用源</div>
      <input id="sn" placeholder="名称，如：XX应用源" style="width:100%;padding:8px 10px;border:1px solid #e6e8eb;border-radius:8px;margin-bottom:8px;font-family:inherit">
      <input id="su" placeholder="https://…/fnpack.json" style="width:100%;padding:8px 10px;border:1px solid #e6e8eb;border-radius:8px;font-family:inherit">
      <div class="mf"><button class="btn btn-p" onclick="addSrc()">添加</button></div>
    </div>`;
  el('mask').classList.add('on');
}

async function addSrc() {
  const name = el('sn').value.trim(), url = el('su').value.trim();
  if (!url) return toast('请填写地址');
  const sources = SOURCES.map(s => ({ name: s.name, url: s.url, enabled: true }));
  sources.push({ name: name || '自定义源', url, enabled: true });
  try {
    await api('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sources }) });
    toast('已添加'); closeM(); load(true);
  } catch (e) { toast('添加失败'); }
}
async function delSrc(i) {
  const sources = SOURCES.filter((_, k) => k !== i).map(s => ({ name: s.name, url: s.url, enabled: true }));
  await api('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sources }) });
  toast('已删除'); closeM(); load(true);
}

document.querySelectorAll('.nav-i[data-f]').forEach(i => {
  i.onclick = () => {
    FILTER = i.dataset.f; CAT = '';
    document.querySelectorAll('.nav-i[data-f]').forEach(x => x.classList.toggle('on', x === i));
    el('title').textContent = i.querySelector('.n').textContent;
    renderCats(); render();
  };
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeM(); });
load();
