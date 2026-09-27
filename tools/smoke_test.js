// 商店页面运行时冒烟测试（jsdom）
// 验证: JS 无运行时错误 / 卡片渲染 / 搜索 / 分类筛选 / 详情弹窗 / 帮助弹窗 / 下载链接
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const file = process.argv[2] || path.join(__dirname, '..', 'Store', 'index.html');
const html = fs.readFileSync(file, 'utf8');

const errors = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://jiankujidu.github.io/Store/',
  virtualConsole: new (require('jsdom').VirtualConsole)()
    .on('jsdomError', e => errors.push('jsdomError: ' + e.message))
    .on('error', (...a) => errors.push('console.error: ' + a.join(' '))),
});

const w = dom.window;
const d = w.document;
const q = s => d.querySelector(s);
const qa = s => Array.from(d.querySelectorAll(s));

const results = [];
const check = (name, cond, extra = '') =>
  results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? '  → ' + extra : ''}`);

// 1. 卡片渲染（期望数量从页面内联数据取，避免硬编码）
const _m = html.match(/const DATA = (\{[\s\S]*?\});\s*\nconst SRC/);
const EXPECT = _m ? JSON.parse(_m[1]).apps.length : 0;
const cards = qa('.card');
check('应用卡片渲染', EXPECT > 0 && cards.length === EXPECT, `${cards.length}/${EXPECT} 张`);

// 2. 卡片内容完整（名称/版本/大小）
const first = cards[0];
check('卡片含名称', !!first && !!first.querySelector('.c-name'));
check('卡片含版本号', !!first && /^v\d/.test(first.querySelector('.ver')?.textContent || ''));

// 3. 分类 chips
const chips = qa('.chip');
check('分类筛选渲染', chips.length >= 3, `${chips.length} 个: ${chips.map(c => c.textContent).join('/')}`);

// 4. 搜索筛选
const before = qa('.card').length;
q('#q').value = '下载';
w.render();
const after = qa('.card').length;
check('搜索生效', after > 0 && after < before, `"下载" → ${after}/${before}`);
q('#q').value = 'zzz-不存在的东西';
w.render();
check('无结果时显示空态', q('#empty').style.display === 'block');
q('#q').value = '';
w.render();

// 5. 详情弹窗
w.openApp('fnlogpush');
const modal = q('#modal');
check('详情弹窗打开', q('#mask').classList.contains('on'));
check('弹窗含应用名', /日志哨兵/.test(modal.textContent));
check('弹窗含更新日志', /SHA256/.test(modal.textContent));
const dls = qa('#modal .m-ft a').map(a => a.getAttribute('href'));
check('弹窗含下载链接', dls.some(h => h && h.endsWith('.fpk')), dls.filter(Boolean)[0]);
check('下载链接已 URL 编码', dls.every(h => !h || !/\s/.test(h)));

// 6. 关闭弹窗
w.closeModal();
check('弹窗可关闭', !q('#mask').classList.contains('on'));

// 7. 帮助弹窗
w.help();
const helpTxt = q('#modal').textContent;
check('帮助弹窗打开', q('#mask').classList.contains('on'));
check('帮助含源地址', /fnpack\.json/.test(helpTxt));
check('帮助含加速地址', /gh-proxy\.com/.test(helpTxt));
check('帮助含手动安装说明', /手动安装/.test(helpTxt));
w.closeModal();

// 8. 顶部源地址
const srcurl = q('#srcurl');
check('顶部源地址正确', /raw\.githubusercontent\.com\/jiankujidu\/Store\/main\/fnpack\.json/.test(srcurl.textContent));

// 9. 运行期错误
check('无 JS 运行时错误', errors.length === 0, errors.join(' | '));

console.log('\n=== 冒烟测试 ===');
results.forEach(r => console.log('  ' + r));
const failed = results.filter(r => r.startsWith('FAIL'));
console.log(`\n${results.length - failed.length}/${results.length} 通过`);
process.exit(failed.length ? 1 : 0);
