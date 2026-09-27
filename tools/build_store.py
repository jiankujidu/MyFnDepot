# -*- coding: utf-8 -*-
"""
从 fnpack.json 生成应用商店静态页面 index.html
用法: python build_store.py [仓库目录] [输出文件]
页面内图片/fpk 均使用仓库相对路径，因此部署到 GitHub Pages 后可直接显示与下载。
"""
import json, os, sys, io
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')

def enc(p):
    """仓库路径转 URL 安全路径：文件名可能含空格/中文（如 'USB Rsync.png'），必须编码"""
    return quote(p, safe='/')

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, 'index.html')

d = json.load(io.open(os.path.join(REPO, 'fnpack.json'), encoding='utf-8'))
src = d['source_info']
BASE = 'https://raw.githubusercontent.com/jiankujidu/Store/main/'
PROXY = 'https://gh-proxy.com/' + BASE

apps = []
for app_id, a in d['apps'].items():
    ver = sorted(a['releases'].keys())[-1]
    rel = a['releases'][ver]
    pkg = rel['packages']['all']
    apps.append({
        'id': app_id,
        'name': a['display_name'],
        'desc': a['desc'],
        'cats': a.get('categories') or ['其他'],
        'icon': enc(a['icon_url']),
        'previews': [enc(x) for x in (a.get('preview_urls') or [])],
        'version': ver,
        'size': pkg['size'],
        'updated': rel.get('updated_at', ''),
        'changelog': rel.get('changelog', ''),
        'file': enc(pkg['download_url']),
        'sha': pkg['sha256'],
        'maintainer': a.get('maintainer', ''),
        'bug': a.get('bug_report_url', ''),
    })

apps.sort(key=lambda x: x['name'])
total = sum(a['size'] for a in apps)
cats = []
for a in apps:
    for c in a['cats']:
        if c not in cats:
            cats.append(c)

DATA = json.dumps({'apps': apps, 'cats': cats}, ensure_ascii=False)
SRC = json.dumps(src, ensure_ascii=False)

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · 飞牛NAS应用商店</title>
<meta name="description" content="__DESC__">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#f5f6f8; --card:#fff; --bd:#e4e6eb; --tx:#1f2328; --tx2:#5a6470;
  --pri:#1a73e8; --pri-d:#1558b0; --pri-l:#e8f1fe;
  --ok:#1a7f37; --shadow:0 1px 3px rgba(16,24,40,.06),0 1px 2px rgba(16,24,40,.04);
  --shadow-h:0 8px 24px rgba(16,24,40,.12);
}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  background:var(--bg); color:var(--tx); line-height:1.6; -webkit-font-smoothing:antialiased;
}
a{color:var(--pri);text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}

/* ---------- header ---------- */
header{background:linear-gradient(135deg,#1a73e8 0%,#0d47a1 100%);color:#fff;padding:38px 0 30px}
.hd{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.logo{width:58px;height:58px;border-radius:15px;background:rgba(255,255,255,.18);
  display:flex;align-items:center;justify-content:center;font-size:30px;flex:0 0 auto;
  border:1px solid rgba(255,255,255,.25)}
h1{font-size:26px;font-weight:700;letter-spacing:.5px}
.sub{font-size:14px;opacity:.85;margin-top:2px}
.stats{display:flex;gap:26px;margin-top:22px;flex-wrap:wrap}
.stat b{display:block;font-size:21px;font-weight:700;line-height:1.2}
.stat span{font-size:12px;opacity:.8}

.srcbox{margin-top:22px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.22);
  border-radius:10px;padding:12px 14px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.srcbox code{flex:1;min-width:260px;font-size:13px;font-family:ui-monospace,Menlo,Consolas,monospace;
  word-break:break-all;opacity:.95}
.btn{border:0;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;
  font-family:inherit;transition:.15s;white-space:nowrap}
.btn-w{background:#fff;color:var(--pri-d)}
.btn-w:hover{background:#f0f4ff}
.btn-p{background:var(--pri);color:#fff}
.btn-p:hover{background:var(--pri-d)}
.btn-g{background:#fff;color:var(--tx);border:1px solid var(--bd)}
.btn-g:hover{border-color:var(--pri);color:var(--pri)}

/* ---------- toolbar ---------- */
.bar{position:sticky;top:0;z-index:20;background:rgba(245,246,248,.92);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--bd);padding:14px 0}
.bar-in{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.search{flex:1;min-width:200px;position:relative}
.search input{width:100%;padding:9px 14px 9px 36px;border:1px solid var(--bd);border-radius:9px;
  font-size:14px;font-family:inherit;background:#fff;outline:0;transition:.15s}
.search input:focus{border-color:var(--pri);box-shadow:0 0 0 3px var(--pri-l)}
.search svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);opacity:.45}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{padding:6px 14px;border-radius:20px;background:#fff;border:1px solid var(--bd);
  font-size:13px;cursor:pointer;transition:.15s;user-select:none;color:var(--tx2)}
.chip:hover{border-color:var(--pri);color:var(--pri)}
.chip.on{background:var(--pri);border-color:var(--pri);color:#fff}

/* ---------- grid ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));gap:16px;padding:22px 0 40px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px;
  cursor:pointer;transition:.18s;display:flex;flex-direction:column;position:relative}
.card:hover{box-shadow:var(--shadow-h);border-color:#c9d6ea;transform:translateY(-2px)}
.c-top{display:flex;gap:13px;align-items:flex-start}
.c-icon{width:50px;height:50px;border-radius:12px;object-fit:contain;background:#f7f8fa;
  border:1px solid #eef0f3;flex:0 0 auto;padding:3px}
.c-name{font-size:16px;font-weight:650;line-height:1.35}
.c-cat{font-size:11.5px;color:var(--tx2);margin-top:3px}
.c-desc{font-size:13px;color:var(--tx2);margin:12px 0 14px;flex:1;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.c-meta{display:flex;justify-content:space-between;align-items:center;
  font-size:12px;color:#7a8794;border-top:1px solid #f0f1f4;padding-top:11px}
.ver{background:var(--pri-l);color:var(--pri-d);padding:2px 8px;border-radius:5px;
  font-weight:600;font-size:11.5px}
.empty{text-align:center;padding:70px 20px;color:var(--tx2)}
.empty div:first-child{font-size:44px;margin-bottom:12px;opacity:.35}

/* ---------- modal ---------- */
.mask{position:fixed;inset:0;background:rgba(16,24,40,.5);z-index:100;display:none;
  align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(3px)}
.mask.on{display:flex}
.modal{background:#fff;border-radius:16px;max-width:760px;width:100%;max-height:88vh;
  overflow-y:auto;box-shadow:0 24px 60px rgba(0,0,0,.28)}
.m-hd{padding:24px 26px 18px;border-bottom:1px solid var(--bd);display:flex;gap:16px;align-items:flex-start}
.m-hd img{width:64px;height:64px;border-radius:14px;border:1px solid #eef0f3;padding:3px;flex:0 0 auto}
.m-hd h2{font-size:20px;font-weight:700}
.m-sub{font-size:13px;color:var(--tx2);margin-top:4px}
.m-close{margin-left:auto;background:none;border:0;font-size:26px;color:#98a2ad;cursor:pointer;
  line-height:1;padding:0 4px;font-family:inherit}
.m-close:hover{color:var(--tx)}
.m-body{padding:20px 26px 26px}
.shots{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px;margin-bottom:18px}
.shots img{height:290px;border-radius:10px;border:1px solid var(--bd);background:#f7f8fa;flex:0 0 auto}
.sec-t{font-size:13px;font-weight:650;color:var(--tx2);margin:18px 0 8px;
  text-transform:uppercase;letter-spacing:.6px}
.desc{font-size:14px;color:#3f4855}
.log{background:#f7f8fa;border:1px solid var(--bd);border-radius:10px;padding:14px 16px;
  font-size:13px;color:#3f4855;white-space:pre-wrap;max-height:230px;overflow-y:auto;line-height:1.65}
.kv{display:grid;grid-template-columns:auto 1fr;gap:7px 18px;font-size:13px;color:var(--tx2)}
.kv b{color:var(--tx);font-weight:600}
.m-ft{display:flex;gap:10px;flex-wrap:wrap;padding-top:20px;margin-top:20px;border-top:1px solid var(--bd)}
.sha{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:#8a94a0;
  word-break:break-all;margin-top:10px}

footer{border-top:1px solid var(--bd);padding:26px 0 40px;text-align:center;
  font-size:13px;color:var(--tx2);background:#fff}
footer a{color:var(--pri)}
.toast{position:fixed;bottom:28px;left:50%;transform:translateX(-50%) translateY(80px);
  background:#1f2328;color:#fff;padding:11px 22px;border-radius:9px;font-size:14px;
  z-index:200;opacity:0;transition:.25s;pointer-events:none}
.toast.on{opacity:1;transform:translateX(-50%) translateY(0)}
@media(max-width:640px){
  h1{font-size:21px} .stats{gap:18px} .grid{grid-template-columns:1fr}
  .m-hd,.m-body{padding-left:18px;padding-right:18px} .shots img{height:230px}
}
</style>
</head>
<body>

<header>
  <div class="wrap">
    <div class="hd">
      <div class="logo">&#128230;</div>
      <div>
        <h1>__TITLE__</h1>
        <div class="sub">飞牛NAS（FnOS）第三方应用源 · 维护者 __AUTHOR__</div>
      </div>
    </div>
    <div class="stats">
      <div class="stat"><b>__NAPP__</b><span>个应用</span></div>
      <div class="stat"><b>__NCAT__</b><span>个分类</span></div>
      <div class="stat"><b>__TOT__</b><span>总大小</span></div>
      <div class="stat"><b>__UPD__</b><span>最近更新</span></div>
    </div>
    <div class="srcbox">
      <code id="srcurl">__SRCURL__</code>
      <button class="btn btn-w" onclick="cp('__SRCURL__')">复制源地址</button>
      <button class="btn btn-w" onclick="cp('__PROXYURL__')">复制加速地址</button>
    </div>
  </div>
</header>

<div class="bar">
  <div class="wrap bar-in">
    <div class="search">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
        <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
      <input id="q" type="text" placeholder="搜索应用名称或功能…" oninput="render()">
    </div>
    <div class="chips" id="chips"></div>
    <button class="btn btn-g" onclick="help()">&#10067; 怎么装到飞牛</button>
  </div>
</div>

<main class="wrap">
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">
    <div>&#128269;</div><div>没有找到匹配的应用</div>
  </div>
</main>

<footer>
  <div class="wrap">
    __TITLE__ · 由 <a href="__HOME__" target="_blank">__AUTHOR__</a> 维护<br>
    应用本体版权归原作者所有（MIT），本页面为个人整理镜像 ·
    <a href="__HOME__" target="_blank">GitHub 仓库</a> ·
    <a href="__BUG__" target="_blank">联系开发者</a>
  </div>
</footer>

<div class="mask" id="mask" onclick="if(event.target===this)closeModal()">
  <div class="modal" id="modal"></div>
</div>
<div class="toast" id="toast"></div>

<script>
const DATA = __DATA__;
const SRC = __SRC__;
const BASE = 'https://raw.githubusercontent.com/jiankujidu/Store/main/';
const PROXY = 'https://gh-proxy.com/' + BASE;
let cur = '全部';

function fmt(b){ return b>1048576 ? (b/1048576).toFixed(1)+' MB' : (b/1024).toFixed(0)+' KB'; }

function cp(t){
  navigator.clipboard.writeText(t).then(()=>toast('已复制：'+t),()=>toast('复制失败，请手动选中'));
}
function toast(m){
  const e=document.getElementById('toast'); e.textContent=m; e.classList.add('on');
  clearTimeout(e._t); e._t=setTimeout(()=>e.classList.remove('on'),2200);
}

document.getElementById('chips').innerHTML =
  ['全部'].concat(DATA.cats).map(c=>
    `<div class="chip${c===cur?' on':''}" onclick="pick('${c}')">${c}</div>`).join('');

function pick(c){ cur=c;
  document.querySelectorAll('.chip').forEach(e=>e.classList.toggle('on',e.textContent===c));
  render();
}

function match(a){
  const q=document.getElementById('q').value.trim().toLowerCase();
  const okc = cur==='全部' || a.cats.includes(cur);
  const okq = !q || (a.name+a.desc+a.id).toLowerCase().includes(q);
  return okc && okq;
}

function render(){
  const list = DATA.apps.filter(match);
  document.getElementById('empty').style.display = list.length ? 'none':'block';
  document.getElementById('grid').innerHTML = list.map(a=>`
    <div class="card" onclick="openApp('${a.id}')">
      <div class="c-top">
        <img class="c-icon" src="${a.icon}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">
        <div>
          <div class="c-name">${a.name}</div>
          <div class="c-cat">${a.cats.join(' · ')}</div>
        </div>
      </div>
      <div class="c-desc">${a.desc}</div>
      <div class="c-meta">
        <span class="ver">v${a.version}</span>
        <span>${fmt(a.size)} · ${a.updated||''}</span>
      </div>
    </div>`).join('');
}

function openApp(id){
  const a = DATA.apps.find(x=>x.id===id); if(!a) return;
  const shots = a.previews.length
    ? `<div class="shots">${a.previews.map(p=>`<img src="${p}" alt="" loading="lazy">`).join('')}</div>`
    : '';
  document.getElementById('modal').innerHTML = `
    <div class="m-hd">
      <img src="${a.icon}" alt="">
      <div>
        <h2>${a.name}</h2>
        <div class="m-sub">${a.cats.join(' · ')} · 版本 v${a.version} · ${fmt(a.size)}</div>
      </div>
      <button class="m-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="m-body">
      ${shots}
      <div class="sec-t">应用简介</div>
      <div class="desc">${a.desc}</div>
      ${a.changelog?`<div class="sec-t">更新日志（v${a.version}）</div><div class="log">${a.changelog.replace(/</g,'&lt;')}</div>`:''}
      <div class="sec-t">详细信息</div>
      <div class="kv">
        <b>包名</b><span>${a.id}</span>
        <b>维护者</b><span>${a.maintainer}</span>
        <b>更新日期</b><span>${a.updated||'-'}</span>
        <b>文件大小</b><span>${fmt(a.size)}（${a.size} 字节）</span>
      </div>
      <div class="sha">SHA256: ${a.sha}</div>
      <div class="m-ft">
        <a class="btn btn-p" href="${a.file}" download>下载 fpk（本站）</a>
        <a class="btn btn-g" href="${BASE+a.file}" target="_blank">GitHub 直链</a>
        <a class="btn btn-g" href="${PROXY+a.file}" target="_blank">国内加速</a>
        <button class="btn btn-g" onclick="cp('${BASE+a.file}')">复制链接</button>
      </div>
    </div>`;
  document.getElementById('mask').classList.add('on');
  document.body.style.overflow='hidden';
}
function closeModal(){
  document.getElementById('mask').classList.remove('on');
  document.body.style.overflow='';
}
document.addEventListener('keydown',e=>{ if(e.key==='Escape') closeModal(); });

function help(){
  const box = u => `<div class="srcbox" style="background:#f7f8fa;border-color:var(--bd)">
      <code style="color:var(--tx)">${u}</code>
      <button class="btn btn-p" onclick="cp('${u}')">复制</button></div>`;
  document.getElementById('modal').innerHTML = `
    <div class="m-hd">
      <div style="font-size:34px">&#128268;</div>
      <div><h2>怎么装到飞牛NAS</h2>
        <div class="m-sub">两种方式，任选其一</div></div>
      <button class="m-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="m-body">
      <div class="sec-t" style="margin-top:0">方式一 · 添加应用源（推荐，可一键更新）</div>
      <div class="desc">飞牛NAS 打开 <b>应用中心 → 设置 → 添加第三方应用源</b>，粘贴下面的地址：</div>
      <div style="margin:12px 0">${box(BASE+'fnpack.json')}</div>
      <div class="desc">国内访问不畅时用加速地址：</div>
      <div style="margin:12px 0">${box(PROXY+'fnpack.json')}</div>
      <div class="desc" style="color:var(--tx2);font-size:13px">
        添加后列表不刷新就重启应用中心或等几分钟缓存过期。</div>

      <div class="sec-t">方式二 · 手动安装单个应用</div>
      <div class="desc">不想加源，就在本页面点开任意应用 → <b>下载 fpk</b>，
        然后到飞牛 <b>应用中心 → 手动安装</b> 上传该文件即可。</div>

      <div class="sec-t">关于加速地址</div>
      <div class="kv">
        <b>raw 主地址</b><span>国外 / 网络通畅时直连，最稳</span>
        <b>gh-proxy</b><span>实测可用，能完整下载大包（含 80MB 的视频下载器）</span>
        <b>jsDelivr</b><span>单文件限 20MB，<b>不能</b>用于整源，大包会失败</span>
      </div>
      <div class="m-ft">
        <a class="btn btn-p" href="${SRC.homepage}" target="_blank">打开 GitHub 仓库</a>
        <a class="btn btn-g" href="${SRC.homepage}/issues" target="_blank">反馈问题</a>
      </div>
    </div>`;
  document.getElementById('mask').classList.add('on');
  document.body.style.overflow='hidden';
}
render();
</script>
</body>
</html>
'''

latest = max(a['updated'] for a in apps)
html = (HTML
    .replace('__DATA__', DATA)
    .replace('__SRC__', SRC)
    .replace('__TITLE__', src['name'])
    .replace('__AUTHOR__', src['author'])
    .replace('__HOME__', src['homepage'])
    .replace('__DESC__', src.get('description') or ('飞牛NAS第三方应用商店，收录 %d 个应用' % len(apps)))
    .replace('__BUG__', apps[0]['bug'] or src['homepage'])
    .replace('__NAPP__', str(len(apps)))
    .replace('__NCAT__', str(len(cats)))
    .replace('__TOT__', '%.0f MB' % (total / 1048576))
    .replace('__UPD__', latest)
    .replace('__SRCURL__', BASE + 'fnpack.json')
    .replace('__PROXYURL__', PROXY + 'fnpack.json'))

io.open(OUT, 'w', encoding='utf-8', newline='').write(html)
print('生成:', OUT, '%.1f KB' % (len(html.encode('utf-8')) / 1024))
print('应用 %d 个 · 分类 %d 个 · 总计 %.1f MB · 最近更新 %s' % (len(apps), len(cats), total / 1048576, latest))
