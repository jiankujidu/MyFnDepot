#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 fnstore-src/ 打包成 fnstore.fpk

fpk 结构（gzip(tar)）：
    fpk
    ├── app.tgz          gzip(tar{ ui/, config/ })     ← 应用本体
    ├── cmd/             *.sh 生命周期脚本（0755）
    ├── config/          privilege / resource
    ├── wizard/          install / uninstall
    ├── manifest         关键：checksum = md5(app.tgz)
    ├── ICON.PNG         64x64
    └── ICON_256.PNG     256x256
"""
import io, os, sys, gzip, tarfile, hashlib, time

sys.stdout.reconfigure(encoding='utf-8')

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fnstore-src')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
APPNAME = 'fnstore'
VERSION = '0.1.0'
DISPLAY = '应用商店'
DESC = ('飞牛NAS第三方应用商店：浏览、搜索、筛选应用源中的应用，'
        '一键下载 fpk 并调用系统 appcenter-cli 自动安装，支持更新检测与多源管理')


def add_tree(tf, base, prefix, mode_files=0o644, mode_dirs=0o755, exe=()):
    """把 base 目录内容加入 tar，路径前缀 prefix"""
    if not os.path.isdir(base):
        return
    ti = tarfile.TarInfo(prefix.rstrip('/') if prefix else '.')
    ti.type = tarfile.DIRTYPE
    ti.mode = mode_dirs
    ti.mtime = int(time.time())
    if prefix:
        tf.addfile(ti)
    for root, dirs, files in os.walk(base):
        dirs.sort(); files.sort()
        rel = os.path.relpath(root, base).replace('\\', '/')
        arc = (prefix + rel if rel != '.' else prefix.rstrip('/')).rstrip('/')
        if arc:
            d = tarfile.TarInfo(arc); d.type = tarfile.DIRTYPE
            d.mode = mode_dirs; d.mtime = int(time.time())
            tf.addfile(d)
        for f in files:
            fp = os.path.join(root, f)
            a = (arc + '/' + f) if arc else f
            info = tarfile.TarInfo(a)
            info.size = os.path.getsize(fp)
            info.mtime = int(os.path.getmtime(fp))
            info.mode = 0o755 if (f in exe or f.endswith('.sh')) else mode_files
            info.uid = info.gid = 0
            info.uname = info.gname = 'root'
            with open(fp, 'rb') as fh:
                tf.addfile(info, fh)


def make_tar(entries, out_path, gzip_it=True):
    """entries: list of (base_dir_or_file, prefix, is_dir)"""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.GNU_FORMAT) as tf:
        for base, prefix, is_dir, exe in entries:
            if is_dir:
                add_tree(tf, base, prefix, exe=exe)
            else:
                info = tarfile.TarInfo(prefix)
                info.size = os.path.getsize(base)
                info.mtime = int(time.time())
                info.mode = 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = 'root'
                with open(base, 'rb') as fh:
                    tf.addfile(info, fh)
    data = raw.getvalue()
    if gzip_it:
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0) as g:
            g.write(data)
        data = buf.getvalue()
    with open(out_path, 'wb') as f:
        f.write(data)
    return data


def main():
    os.makedirs(OUT, exist_ok=True)

    # ── 1. app.tgz = tar.gz{ ui/, config/ }
    app_entries = [
        (os.path.join(SRC, 'app', 'ui'), 'ui', True, ()),
        (os.path.join(SRC, 'config'), 'config', True, ()),
    ]
    app_tgz = os.path.join(OUT, 'app.tgz')
    make_tar(app_entries, app_tgz)
    checksum = hashlib.md5(open(app_tgz, 'rb').read()).hexdigest()
    print(f'app.tgz       {os.path.getsize(app_tgz)/1024:8.1f} KB   md5={checksum}')

    # ── 2. manifest
    man = f"""appname               = {APPNAME}
version               = {VERSION}
display_name          = {DISPLAY}
desc                  = {DESC}
platform              = all
source                = thirdparty
desktop_uidir         = ui
desktop_applaunchname = {APPNAME}.Application
install_dep_apps      = nodejs_v24
maintainer              = 一起瞎折腾
maintainer_url          = https://github.com/jiankujidu/Store
distributor              = 一起瞎折腾
distributor_url          = https://github.com/jiankujidu/Store
checksum              = {checksum}
"""
    man_path = os.path.join(OUT, 'manifest')
    with io.open(man_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(man)
    print('manifest      已生成')

    # ── 3. 顶层 fpk
    top_entries = [
        (os.path.join(SRC, 'cmd'), 'cmd', True, ()),
        (os.path.join(SRC, 'config'), 'config', True, ()),
        (os.path.join(SRC, 'wizard'), 'wizard', True, ()),
        (app_tgz, 'app.tgz', False, ()),
        (man_path, 'manifest', False, ()),
        (os.path.join(SRC, 'ICON.PNG'), 'ICON.PNG', False, ()),
        (os.path.join(SRC, 'ICON_256.PNG'), 'ICON_256.PNG', False, ()),
    ]
    fpk = os.path.join(OUT, f'{APPNAME}.fpk')
    make_tar(top_entries, fpk)
    size = os.path.getsize(fpk)
    print(f'\n✅ {fpk}')
    print(f'   {size/1024:.1f} KB   sha256={hashlib.sha256(open(fpk,"rb").read()).hexdigest()}')

    # ── 4. 自检
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(open(fpk, 'rb').read()))) as tf:
        names = tf.getnames()
        assert 'app.tgz' in names and 'manifest' in names
        assert hashlib.md5(tf.extractfile('app.tgz').read()).hexdigest() == checksum
        print('\n自检通过：')
        for n in sorted(names):
            print('   ', n)


if __name__ == '__main__':
    main()
