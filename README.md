# Tutu_GW

OpenWrt x86_64 自用固件，面向 R86S 软路由，每周五自动构建发布。

---

## 固件信息

| 项目 | 内容 |
|---|---|
| 基础版本 | OpenWrt 24.10 |
| 架构 | x86_64 |
| 目标设备 | R86S |
| 构建频率 | 每周五 18:00 CST |

## 内置插件

- **OpenClash** — 代理分流
- **MosDNS** — DNS 分流与转发
- **PassWall** — 代理分流
- **SSR Plus** — SS/SSR/Xray 代理
- **ddns-go** — 动态 DNS
- **TurboACC** — 硬件加速
- **vlmcsd** — KMS 激活服务器
- **autoupdate** — 固件自动更新
- **upnp** — UPnP

## 默认网络

| 项目 | 值 |
|---|---|
| LAN IP | `192.168.5.1` |
| WAN | PPPoE（eth4.3961，VLAN 3961）|
| 密码 | 空 |
| IPv6 | 禁用 |

## 刷机

从 [Releases](../../releases) 下载 `*-combined-efi.img.gz`，写盘即可。
