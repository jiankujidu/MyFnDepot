#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本机冒烟测试：启动 fnstore 后端，验证 /api/apps 能正确解析真实索引"""
import os, sys, json, time, subprocess, urllib.request, signal

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
NODE = r'C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-2/node.exe'
TEST = os.path.join(ROOT, 'fnstore-test')
PORT = '47891'

os.makedirs(os.path.join(TEST, 'data'), exist_ok=True)
conf = {
    "useProxy": True,
    "sources": [{"name": "fn第三方应用商店",
                 "url": "https://raw.githubusercontent.com/jiankujidu/Store/main/fnpack.json",
                 "enabled": True}]
}
with open(os.path.join(TEST, 'data', 'config.json'), 'w', encoding='utf-8') as f:
    json.dump(conf, f)
import shutil
shutil.copy(os.path.join(ROOT, 'fnstore-src', 'app', 'ui', 'server.js'),
            os.path.join(TEST, 'server.js'))

env = dict(os.environ, PORT=PORT, TRIM_PKGVAR=TEST)
p = subprocess.Popen([NODE, os.path.join(TEST, 'server.js')], env=env,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print('启动后端 pid=', p.pid)
time.sleep(2.5)

def get(path):
    for i in range(3):
        try:
            r = urllib.request.urlopen('http://127.0.0.1:%s%s' % (PORT, path), timeout=40)
            return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            if i == 2:
                raise
            time.sleep(2)

fail = 0
try:
    print('\n=== /api/version ===')
    v = get('/api/version'); print('  ', v)
    assert v.get('version')

    print('\n=== /api/apps ===')
    d = get('/api/apps')
    print('  源状态:')
    for s in d.get('sources', []):
        print(f"    {'OK ' if s['ok'] else 'ERR'} {s['name']}  {s['appCount']} 个应用  {s.get('error') or ''}")
        if not s['ok']:
            fail += 1
    apps = d.get('apps', [])
    print(f'\n  应用 {len(apps)} 个:')
    for a in apps:
        print(f"    {a['name']:<16} v{a['version']:<8} {a['size']/1e6:6.2f}MB  "
              f"分类={','.join(a['cats']) or '-':<10} 图标={'有' if a['icon'] else '无':<3} "
              f"预览={len(a['previews'])}  下载={'有' if a['download'] else '无'}")
    assert len(apps) > 0, '应用列表为空'
    for a in apps:
        assert a['download'].startswith('http'), '下载地址无效: ' + a['name']
        assert a['icon'].startswith('http'), '图标地址无效: ' + a['name']
    print('\n  ✅ 索引解析正常，地址均为绝对 URL')
except Exception as e:
    fail += 1
    print('\n  ❌', type(e).__name__, e)
finally:
    p.kill()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    try:
        out = p.stdout.read()
        if out.strip():
            print('\n--- 后端输出 ---\n' + out.strip()[:2000])
    except Exception:
        pass

print('\n结果:', '通过' if fail == 0 else '失败')
sys.exit(1 if fail else 0)
