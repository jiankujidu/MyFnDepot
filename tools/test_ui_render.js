/**
 * 前端渲染冒烟测试（jsdom）
 * 用真实索引数据驱动 index.html + main.js，验证渲染与交互无运行时错误
 *
 * 用法: NODE_PATH=<jsdom 路径> node test_ui_render.js
 */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const ROOT = __dirname;
const html = fs.readFileSync(path.join(ROOT, 'fnstore-src', 'app', 'ui', 'index.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'fnstore-test', 'apps.json'), 'utf8'));

let pass = 0, fail = 0;
const ok = (c, m) => { c ? (pass++, console.log('PASS  ' + m)) : (fail++, console.log('FAIL  ' + m)); };
const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push(String(e.message || e)));
vc.on('error', (...a) => errors.push(a.join(' ')));

const dom = new JSDOM(html, {
  runScripts: 'outside-only',
  url: 'http://localhost/app/fnstore/',
  pretendToBeVisual: true,
  virtualConsole: vc,
});
const { window } = dom;

// 拦截 fetch：返回真实数据
window.fetch = async (u) => {
  const url = String(u);
  if (url.startsWith('/api/apps')) return { ok: true, json: async () => data };
  if (url.startsWith('/api/install')) return { ok: true, json: async () => ({ task: 'x1' }) };
  if (url.startsWith('/api/task')) return { ok: true, json: async () => ({ task: { id: 'x1', phase: 'done', percent: 100, log: 'ok' } }) };
  return { ok: true, json: async () => ({}) };
};
window.navigator.clipboard = { writeText: async () => {} };
window.alert = () => {};

try {
  window.eval(fs.readFileSync(path.join(ROOT, 'fnstore-src', 'app', 'ui', 'main.js'), 'utf8'));
} catch (e) {
  fail++; console.log('FAIL  main.js 执行异常: ' + e.message);
}

(async () => {
  await new Promise(r => setTimeout(r, 600));
  const d = window.document;
  const N = data.apps.length;

  ok(d.querySelectorAll('#grid .card').length === N, `应用卡片渲染 → ${d.querySelectorAll('#grid .card').length}/${N}`);
  ok(d.getElementById('c-all').textContent === String(N), `计数「全部」= ${d.getElementById('c-all').textContent}`);

  // 分类导航
  const cats = d.querySelectorAll('#cats .nav-i');
  ok(cats.length >= 2, `分类导航 → ${[...cats].map(c => c.querySelector('.n').textContent).join('/')}`);

  // 搜索
  const q = d.getElementById('q');
  q.value = '下载';
  d.dispatchEvent(new window.Event('input'));
  q.dispatchEvent(new window.Event('input'));
  window.eval('render()');
  const n1 = d.querySelectorAll('#grid .card').length;
  ok(n1 > 0 && n1 < N, `搜索「下载」→ ${n1}/${N}`);
  q.value = 'zzzz不存在zzzz';
  window.eval('render()');
  ok(d.getElementById('empty').style.display === 'block', '无结果时显示空态');
  q.value = '';
  window.eval('render()');

  // 分类筛选
  const first = d.querySelector('#cats .nav-i');
  if (first) {
    first.onclick();
    const n2 = d.querySelectorAll('#grid .card').length;
    ok(n2 > 0 && n2 <= N, `分类「${first.dataset.cat}」→ ${n2} 个`);
    first.onclick();
  }

  // 详情弹窗
  window.eval(`detail('${data.apps[0].id}')`);
  const modal = d.getElementById('modal').textContent;
  ok(modal.includes(data.apps[0].name), `详情弹窗含应用名「${data.apps[0].name}」`);
  ok(d.querySelectorAll('#modal img').length >= 1, '详情弹窗含图标/预览图');
  ok(d.getElementById('mask').className.includes('on'), '弹窗已打开');
  window.eval('closeM()');
  ok(!d.getElementById('mask').className.includes('on'), '弹窗可关闭');

  // 安装按钮存在
  ok(d.getElementById('grid').innerHTML.includes('安装'), '卡片含安装按钮');

  // 安装流程不抛错
  try {
    window.eval(`install('${data.apps[0].id}')`);
    await new Promise(r => setTimeout(r, 400));
    ok(d.getElementById('prog').className.includes('on'), '安装进度条弹出');
  } catch (e) { ok(false, 'install() 异常: ' + e.message); }

  // 源管理
  try {
    window.eval('srcMgr()');
    ok(d.getElementById('modal').textContent.includes('应用源管理'), '应用源管理弹窗');
    window.eval('closeM()');
  } catch (e) { ok(false, 'srcMgr() 异常: ' + e.message); }

  ok(errors.length === 0, '无 JS 运行时错误' + (errors.length ? ': ' + errors[0].slice(0, 120) : ''));

  console.log(`\n结果: ${pass} 通过 / ${fail} 失败`);
  process.exit(fail ? 1 : 0);
})();
