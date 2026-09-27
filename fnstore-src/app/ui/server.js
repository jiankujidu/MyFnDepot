import { createServer } from 'node:http';
import { readFileSync, existsSync, mkdirSync, writeFileSync, readdirSync,
         statSync, rmSync, createWriteStream, createReadStream } from 'node:fs';
import { join, extname, dirname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { Readable } from 'node:stream';

const UI_DIR = dirname(fileURLToPath(import.meta.url));
const PKGVAR = process.env.TRIM_PKGVAR || process.env.TRM_PKGVAR || join(UI_DIR, '..', 'data');
const DATA_DIR = join(PKGVAR, 'data');
const TMP_DIR = join(DATA_DIR, 'tmp');
const CONF_FILE = join(DATA_DIR, 'config.json');
const CACHE_DIR = join(DATA_DIR, 'cache');
const PORT = parseInt(process.env.PORT || '47890', 10);
const VERSION = '0.1.0';
const APPS_ROOT = '/var/apps';

for (const d of [DATA_DIR, TMP_DIR, CACHE_DIR]) {
  if (!existsSync(d)) { try { mkdirSync(d, { recursive: true }); } catch {} }
}

const DEFAULT_SOURCES = [
  { name: 'fn第三方应用商店', url: 'https://raw.githubusercontent.com/jiankujidu/Store/main/fnpack.json', enabled: true }
];

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8'
};

// ───────── config ─────────
function loadConf() {
  try {
    const c = JSON.parse(readFileSync(CONF_FILE, 'utf8'));
    return { useProxy: !!c.useProxy, sources: Array.isArray(c.sources) && c.sources.length ? c.sources : DEFAULT_SOURCES };
  } catch {
    return { useProxy: false, sources: DEFAULT_SOURCES };
  }
}
function saveConf(c) {
  try { writeFileSync(CONF_FILE, JSON.stringify(c, null, 2)); } catch {}
}
let CONF = loadConf();

// ───────── helpers ─────────
function sendJSON(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(body);
}
async function parseBody(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  if (!chunks.length) return {};
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { return {}; }
}
function proxyUrl(u) {
  if (!CONF.useProxy) return u;
  if (u.includes('gh-proxy.com') || u.includes('jsdelivr')) return u;
  return 'https://gh-proxy.com/' + u;
}
function baseOf(indexUrl) {
  return indexUrl.replace(/\/[^/]*$/, '/');
}

// ───────── installed apps (/var/apps/*/manifest) ─────────
function parseManifest(txt) {
  const o = {};
  for (const line of txt.split('\n')) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (m) o[m[1]] = m[2].trim();
  }
  return o;
}
function listInstalled() {
  const out = {};
  try {
    if (!existsSync(APPS_ROOT)) return out;
    for (const d of readdirSync(APPS_ROOT)) {
      const mf = join(APPS_ROOT, d, 'manifest');
      try {
        if (!existsSync(mf)) continue;
        const m = parseManifest(readFileSync(mf, 'utf8'));
        if (!m.appname) continue;
        out[m.appname] = { version: m.version || '', dir: d, displayName: m.display_name || m.appname };
      } catch {}
    }
  } catch {}
  return out;
}

// ───────── fetch index ─────────
async function fetchIndex(src) {
  const url = proxyUrl(src.url);
  const res = await fetch(url, { headers: { 'User-Agent': 'fnstore/0.1' }, signal: AbortSignal.timeout(25000) });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return await res.json();
}

async function buildApps() {
  const installed = listInstalled();
  const sources = [];
  const apps = [];
  for (const s of CONF.sources.filter(x => x.enabled !== false)) {
    let raw = null, err = null;
    try { raw = await fetchIndex(s); } catch (e) { err = String(e.message || e); }
    sources.push({ name: s.name, url: s.url, ok: !!raw, error: err,
                   sourceName: raw?.source_info?.name || '', appCount: raw ? Object.keys(raw.apps || {}).length : 0 });
    if (!raw) continue;
    const base = baseOf(s.url);
    const proxyBase = baseOf(proxyUrl(s.url));
    for (const [id, a] of Object.entries(raw.apps || {})) {
      const versions = Object.keys(a.releases || {}).sort(cmpVer);
      const ver = versions[versions.length - 1];
      if (!ver) continue;
      const rel = a.releases[ver];
      const pkg = (rel.packages || {}).all || Object.values(rel.packages || {})[0];
      if (!pkg) continue;
      apps.push({
        id, source: s.name,
        name: a.display_name || id,
        desc: a.desc || '',
        cats: a.categories || [],
        icon: pkg && a.icon_url ? proxyBase + a.icon_url.replace(/^\.?\//, '') : '',
        previews: (a.preview_urls || []).map(p => proxyBase + String(p).replace(/^\.?\//, '')),
        version: ver,
        size: pkg.size || 0,
        updated: rel.updated_at || '',
        changelog: rel.changelog || '',
        download: proxyBase + String(pkg.download_url).replace(/^\.?\//, ''),
        downloadRaw: base + String(pkg.download_url).replace(/^\.?\//, ''),
        installed: !!installed[id],
        installedVersion: installed[id]?.version || '',
        canUpdate: !!installed[id] && installed[id].version && cmpVer(ver, installed[id].version) > 0,
        openUrl: installed[id] ? '/app/' + id : ''
      });
    }
  }
  return { sources, apps, installed };
}

function cmpVer(a, b) {
  const pa = String(a).split('.').map(Number); const pb = String(b).split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const x = pa[i] || 0, y = pb[i] || 0;
    if (x !== y) return x - y;
  }
  return 0;
}

// ───────── install tasks ─────────
const tasks = new Map();
let taskSeq = 1;
let queue = Promise.resolve();

function newTask(app) {
  const id = 't' + (taskSeq++);
  const t = { id, app: app.name, appId: app.id, phase: 'queued', percent: 0,
              log: '', error: '', started: Date.now(), finished: 0 };
  tasks.set(id, t);
  if (tasks.size > 50) { const k = tasks.keys().next().value; tasks.delete(k); }
  return t;
}

async function runInstall(t, app) {
  const file = join(TMP_DIR, `${app.id}-${app.version}.fpk`);
  try {
    // 1. download
    t.phase = 'downloading'; t.percent = 0;
    log(t, `下载 ${app.name} v${app.version} …`);
    await download(app.download, file, t);
    const st = statSync(file);
    log(t, `下载完成 ${(st.size / 1048576).toFixed(1)} MB`);

    // 2. install via appcenter-cli
    t.phase = 'installing'; t.percent = 100;
    log(t, '调用 appcenter-cli install-fpk …');
    const r = await exec('appcenter-cli', ['install-fpk', file], 10 * 60 * 1000, line => log(t, line));
    if (r.code !== 0) throw new Error(r.stderr || r.stdout || 'exit ' + r.code);
    log(t, '安装完成');
    t.phase = 'done';
  } catch (e) {
    t.phase = 'error'; t.error = String(e.message || e);
    log(t, '失败: ' + t.error);
  } finally {
    t.finished = Date.now();
    try { if (existsSync(file)) rmSync(file); } catch {}
  }
}
function log(t, line) { t.log += line + '\n'; if (t.log.length > 20000) t.log = t.log.slice(-20000); }

function exec(cmd, args, timeout, onLine) {
  return new Promise(resolve => {
    let out = '', err = '';
    const p = spawn(cmd, args, { env: { ...process.env, PATH: '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:' + (process.env.PATH || '') } });
    const timer = setTimeout(() => { try { p.kill('SIGKILL'); } catch {} }, timeout);
    const push = s => s.split('\n').filter(Boolean).forEach(l => { try { onLine && onLine(l); } catch {} });
    p.stdout.on('data', d => { const s = d.toString(); out += s; push(s); });
    p.stderr.on('data', d => { const s = d.toString(); err += s; push(s); });
    p.on('error', e => { clearTimeout(timer); resolve({ code: -1, stdout: out, stderr: String(e.message || e) }); });
    p.on('close', code => { clearTimeout(timer); resolve({ code, stdout: out, stderr: err }); });
  });
}

async function download(url, dest, t) {
  const res = await fetch(url, { headers: { 'User-Agent': 'fnstore/0.1' }, signal: AbortSignal.timeout(30 * 60 * 1000) });
  if (!res.ok) throw new Error('下载失败 HTTP ' + res.status);
  const total = Number(res.headers.get('content-length') || 0);
  const ws = createWriteStream(dest);
  let got = 0;
  const reader = Readable.fromWeb(res.body);
  for await (const chunk of reader) {
    ws.write(chunk); got += chunk.length;
    if (total) t.percent = Math.min(99, Math.round(got / total * 100));
    else t.percent = Math.min(99, Math.round(Math.min(got / 1048576, 60) / 60 * 100));
  }
  await new Promise((r, j) => { ws.end(err => err ? j(err) : r()); });
}

// ───────── server ─────────
const server = createServer(async (req, res) => {
  let path = decodeURIComponent((req.url || '/').split('?')[0]);
  const method = req.method || 'GET';

  try {
    if (path.startsWith('/api/')) {
      if (path === '/api/version') return sendJSON(res, 200, { version: VERSION, success: true });
      if (path === '/api/ping') return sendJSON(res, 200, { ok: true });
      if (path === '/api/apps') {
        const data = await buildApps();
        return sendJSON(res, 200, { ...data, version: VERSION, useProxy: CONF.useProxy });
      }
      if (path === '/api/config' && method === 'GET') return sendJSON(res, 200, CONF);
      if (path === '/api/config' && method === 'POST') {
        const b = await parseBody(req);
        if (typeof b.useProxy === 'boolean') CONF.useProxy = b.useProxy;
        if (Array.isArray(b.sources)) CONF.sources = b.sources;
        saveConf(CONF);
        return sendJSON(res, 200, { ok: true, config: CONF });
      }
      if (path === '/api/installed') return sendJSON(res, 200, { installed: listInstalled() });
      if (path === '/api/install' && method === 'POST') {
        const b = await parseBody(req);
        if (!b.app) return sendJSON(res, 400, { error: 'missing app' });
        const t = newTask(b.app);
        queue = queue.then(() => runInstall(t, b.app)).catch(() => {});
        return sendJSON(res, 200, { task: t.id });
      }
      if (path.startsWith('/api/task')) {
        const id = path.split('/')[3] || new URL(req.url, 'http://x').searchParams.get('id');
        const t = tasks.get(id);
        return sendJSON(res, 200, { task: t || null });
      }
      if (path === '/api/logs' && method === 'GET') {
        return sendJSON(res, 200, { logs: [...tasks.values()].slice(-20).map(t => ({ id: t.id, app: t.app, phase: t.phase, percent: t.percent, error: t.error, log: t.log.slice(-4000) })) });
      }
      return sendJSON(res, 404, { error: 'unknown api' });
    }

    // static
    if (path === '/' || path === '') path = '/index.html';
    const rel = normalize(path).replace(/^(\.\.[/\\])+/, '');
    const fp = join(UI_DIR, rel);
    if (!fp.startsWith(UI_DIR) || !existsSync(fp) || !statSync(fp).isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('404');
    }
    const ext = extname(fp).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    if (req.method === 'HEAD') return res.end();
    createReadStream(fp).pipe(res);
  } catch (e) {
    try { sendJSON(res, 500, { error: String(e.message || e) }); } catch {}
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[fnstore] listening on ${PORT}, data=${DATA_DIR}`);
});
