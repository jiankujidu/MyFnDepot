# fn第三方应用商店

> 飞牛NAS（FnOS）第三方应用源 · 收录自研和收集的飞牛NAS应用插件

[![Platform](https://img.shields.io/badge/platform-FNOS-blue)](https://www.fnnas.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Maintainer](https://img.shields.io/badge/maintainer-%E4%B8%80%E8%B5%B7%E7%9E%8E%E6%8A%98%E8%85%BE-green)](https://github.com/jiankujidu/Store)

- **源名称**：fn第三方应用商店
- **源作者 / 维护者**：一起瞎折腾
- **主页**：https://github.com/jiankujidu/Store
- **联系开发者**：https://jiankujidu.github.io

## 添加应用源

在飞牛NAS **应用中心 → 设置（或右上角）→ 添加第三方应用源**，填入下面地址：

### 主地址

```
https://raw.githubusercontent.com/jiankujidu/Store/main/fnpack.json
```

### 国内加速（实测可用）

在前面套一层加速前缀，路径不变：

```
https://gh-proxy.com/https://raw.githubusercontent.com/jiankujidu/Store/main/fnpack.json
```

> 已实测：`gh-proxy.com` 能正常拉取索引并完整下载 fpk（含 6.6MB 的包，校验一致）。
> `ghfast.top` 实测不可用（502），别用。
> jsDelivr（`cdn.jsdelivr.net/gh/...`）能取索引，但对单文件有 20MB 限制，**80MB 的视频下载器会下不动**，不建议整源走它。

> 添加后若列表不刷新，重启应用中心或等待几分钟缓存过期。

## 应用列表

| 应用 | 版本 | 说明 |
|------|------|------|
| [日志哨兵](fnlogpush/) | v1.5.3 | 日志监控 + 多渠道推送 + 事件管理 |
| [USB自动同步](usbrsync/) | v0.4.2 | USB存储设备自动同步工具 |
| [清理精灵](fnclearup/) | v0.11.0 | 扫描FnOS所有vol目录，找出已卸载应用（含关联系统用户）、已删除网盘挂载、已删除docker残余卷的残留目录，一键清理 |
| [m3u8下载器](fnm3u8/README.md) | v0.1.0 | m3u8视频下载，支持多线程/断点续传/AES解密/批量下载/直播录制 |
| [m3u8DL 专业下载器](fnm3u8dl/README.md) | v0.9.0 | N_m3u8DL-RE 完整 Node.js 重写，HLS+DASH+MSS 三协议、AES-128 解密、批量添加、直播录制、速度显示、493 个 TDD 测试 |
| [视频下载器](fnytdlp/README.md) | v0.7.2 | 集成 yt-dlp (1872+ 站点)，AI 视频总结 / 缩略图代理 / 字幕提取 / 速度曲线 / 频道订阅 / 自适应架构 |
| [Cookie 提取器](fngetcookie/README.md) | v0.2.1 | 通过代理方式自动捕获网站 Cookie，多格式导出，直连模式绕过 CSP 反代理站点 |
| [网络监控](netwatch/README.md) | v0.6.2 | 实时网络流量监控，pktstat-BPF 引擎 + 进程级流量归因 |

## 安装说明

### 日志哨兵 (fnlogpush)

飞牛NAS日志监控与多渠道推送工具

**下载地址**: [fnlogpush.fpk](fnlogpush/fnlogpush.fpk)

**功能**：
- 实时监控系统日志和备份进度
- 支持企业微信、钉钉、飞书、Bark、PushPlus、MeoW等推送渠道
- Web界面管理、事件订阅、免打扰和告警聚合
- **事件管理功能** - 添加/编辑/删除自定义事件
- **事件查询** - 可查询数据库中事件的最新记录
- **5分钟无操作自动退出登录**

**界面特性**：
- 6个精选主题（深色/深海蓝/清新绿/暮色橙/科技感霓虹）
- 加载动画、骨架屏、卡片悬浮动效
- 科技感霓虹主题（Cyber）
- 状态指示器脉冲发光
- 自定义滚动条、输入框增强效果

**更新日志 (v1.5.3)**：
- 修复 Bark/PushPlus 推送配置无法保存

### USB自动同步 (usbrsync)

USB存储设备自动同步工具，检测到USB设备插入后自动同步指定目录。

**下载地址**: [usbrsync.fpk](usbrsync/usbrsync.fpk) (USBRsyncCgi)

**功能**：
- 单向同步 - 从源目录同步到目标目录
- 双向同步 - 源目录和目标目录双向同步
- 插入自动同步 - 检测到USB设备插入时自动执行同步任务
- 手动同步 - 随时手动触发同步任务
- 实时显示同步进度

**界面特性**：
- 全新深色主题设计（渐变背景 + 毛玻璃效果）
- 响应式布局（自动适配桌面端和移动端）
- 流畅动画（卡片淡入、悬停变换）
- 实时日志刷新

### 清理精灵 (fnclearup)

扫描FnOS所有vol目录，找出已卸载应用（含关联系统用户）、已删除网盘挂载、已删除docker残余卷的残留目录，一键清理。

**下载地址**: [fnclearup.fpk](fnclearup/fnclearup.fpk)

**功能**：
- 自动扫描 `/mnt/vol*` 下所有 `@app*` 目录
- 与已安装应用列表对比，找出孤立目录
- 支持多选批量删除，可预览完整路径
- 直接打开即可使用，无需注册或登录

**界面特性**：
- Tab 切换：网盘挂载目录 / data/vol02 未挂载目录独立展示
- KPI 卡片：卷总数、已挂载数量、未挂载数量
- 主题按钮与赞助按钮风格统一
- 响应式布局，适配桌面端和移动端
- 纯 Bash CGI 实现，轻量无依赖

### m3u8下载器 (fnm3u8)

**下载地址**: [fnm3u8.fpk](fnm3u8/fnm3u8.fpk)

支持多线程、多任务、断点续传的m3u8视频下载器，支持AES解密、批量下载、直播录制。

### m3u8DL 专业下载器 (fnm3u8dl)

**下载地址**: [fnm3u8dl.fpk](fnm3u8dl/fnm3u8dl.fpk)

N_m3u8DL-RE 的 Node.js 完整重写版，HLS + DASH + MSS 三协议、AES-128 自动解密、批量添加、直播录制、实时速度与 ETA 显示。

### 视频下载器 (fnytdlp)

**下载地址**: [fnytdlp.fpk](fnytdlp/fnytdlp.fpk)

集成 yt-dlp（1872+ 站点），支持 AI 视频总结、缩略图代理、字幕提取、速度曲线、频道订阅。

### Cookie 提取器 (fngetcookie)

**下载地址**: [fngetcookie.fpk](fngetcookie/fngetcookie.fpk)

通过代理方式自动捕获网站 Cookie，多格式导出，直连模式绕过 CSP 反代理站点。

### 网络监控 (netwatch)

**下载地址**: [netwatch.fpk](netwatch/netwatch.fpk)

实时网络流量监控，pktstat-BPF 引擎 + 进程级流量归因，支持历史时间段查看与导出。

## 自己加应用

1. 在仓库根目录建一个以应用 ID 命名的文件夹
2. 放入 `xxx.fpk`、`ICON_256.PNG`、`Preview/*.jpg`、`README.md`
3. 在 `fnpack.json` 的 `apps` 下新增条目，版本号按 `releases.主.次.修` 嵌套，填好 `download_url`、`sha256`、`size`
4. 提交推送，NAS 端刷新应用源即可看到

`sha256` 和 `size` 获取：

```bash
sha256sum xxx.fpk
stat -c %s xxx.fpk
```

## 来源与致谢

- 全部应用由原作者 **Wyf841015（再见一零一二）** 开发，功能代码版权归原作者所有
- 上游仓库：[Wyf841015/FnDepot](https://github.com/Wyf841015/FnDepot)（MIT License）
- 本仓库已替换的部分：索引与文档署名、`manifest` 的 maintainer/distributor、应用内页脚署名与「联系作者」入口（原 QQ 群号改为开发者联系页）
- 未替换的部分：应用内赞助收款二维码图片，仍指向原作者

## 改包须知

`fpk` = `gzip( tar{ app.tgz, cmd/, config/, ICON.PNG, manifest, wizard/ } )`，`app.tgz` 又是 `gzip(tar{ ui/ })`。

**manifest 里的 `checksum` 是 `md5(app.tgz)`**，改动 `app.tgz` 内任何文件后必须重算并写回，否则飞牛应用中心会校验失败、装不上。改完包记得同步更新 `fnpack.json` 里的 `sha256` 与 `size`。

## 维护者

- 作者 / 维护者 / 发布者：一起瞎折腾
- 主页：https://github.com/jiankujidu/Store
- 联系开发者（问题反馈）：https://jiankujidu.github.io

> 应用内「联系作者」按钮、以及索引里的 `bug_report_url` 均指向开发者联系页。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。应用包（fpk）版权归各自原作者所有。
