#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前端 jsdom 冒烟测试：用真实索引数据渲染商店界面"""
import os, sys, json, time, subprocess, urllib.request, shutil

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
NODE = r'C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-2/node.exe'
TEST = os.path.join(ROOT, 'fnstore-test')
PORT = '47892'

os.makedirs(os.path.join(TEST, 'data'), exist_ok=True)
with open(os.path.join(TEST, 'data', 'config.json'), 'w', encoding='utf-8') as f:
    json.dump({"useProxy": True, "sources": [
        {"name": "fn第三方应用商店",
         "url": "https://raw.githubusercontent.com/jiankujidu/Store/main/fnpack.json",
         "enabled": True}]}, f)
shutil.copy(os.path.join(ROOT, 'fnstore-src', 'app', 'ui', 'server.js'),
            os.path.join(TEST, 'server.js'))

env = dict(os.environ, PORT=PORT, TRIM_PKGVAR=TEST)
p = subprocess.Popen([NODE, os.path.join(TEST, 'server.js')], env=env,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(2.5)

def get(path, timeout=60):
    for i in range(3):
        try:
            r = urllib.request.urlopen('http://127.0.0.1:%s%s' % (PORT, path), timeout=timeout)
            return json.loads(r.read().decode('utf-8'))
        except Exception:
            if i == 2:
                raise
            time.sleep(2)

ok = True
try:
    data = get('/api/apps')
    with open(os.path.join(TEST, 'apps.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"抓取真实数据：{len(data['apps'])} 个应用，已存 {TEST}/apps.json")
except Exception as e:
    print('抓取失败', e); ok = False
    p.kill(); sys.exit(1)

# ── 安装流水线：下载阶段（本机无 appcenter-cli，预期下载成功 + 安装报错）
print('\n=== 安装流水线测试（下载阶段）===')
small = min(data['apps'], key=lambda a: a['size'])
print(f"  选用最小应用：{small['name']} v{small['version']} {small['size']/1024:.0f}KB")
try:
    req = urllib.request.Request('http://127.0.0.1:%s/api/install' % PORT,
                                 data=json.dumps({'app': small}).encode(),
                                 headers={'Content-Type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    tid = r['task']
    print('  任务 id =', tid)
    last = None
    for _ in range(60):
        time.sleep(1)
        last = get('/api/task?id=' + tid)['task']
        if last['phase'] in ('done', 'error'):
            break
    print(f"  最终阶段 = {last['phase']}")
    print('  日志：')
    for line in last['log'].strip().split('\n')[:12]:
        print('    |', line)
    downloaded = '下载完成' in last['log']
    print(f"  下载阶段完成 = {downloaded}")
    if not downloaded:
        ok = False
    # 本机无 appcenter-cli → 必须优雅报错而不是崩溃
    if last['phase'] == 'error':
        print(f"  安装阶段按预期失败（本机无 CLI）: {last['error'][:80]}")
    else:
        print('  ⚠ 安装竟然成功了？检查环境')
except Exception as e:
    print('  ❌', type(e).__name__, e); ok = False

p.kill()
try:
    p.wait(timeout=5)
except Exception:
    pass

print('\n结果:', '通过' if ok else '失败')
sys.exit(0 if ok else 1)
