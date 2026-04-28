# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

Tutu_GW（突突网关）— OpenWrt x86_64 自编译固件，面向 R86S 软路由，通过 GitHub Actions 每周自动构建并发布 Release。

- **OpenWrt 版本:** 24.10（openwrt-24.10 分支）
- **架构:** x86_64
- **触发:** 每周五 18:00 CST（cron `0 10 * * 5`）+ 手动 workflow_dispatch

## 仓库结构

```
.github/workflows/build.yml   — CI/CD 构建工作流
config/.config                — OpenWrt 包选择和 target 配置（defconfig 格式）
scripts/diy-part1.sh          — feeds update 前：clone 第三方包到 package/
scripts/diy-part2.sh          — feeds install 后：覆盖 files/ 目录
files/etc/uci-defaults/
  └── 99-tutu-defaults        — 首次启动：网络、密码、IPv6 自动配置脚本
```

## 关键配置

### 网络预设（99-tutu-defaults）
- LAN: `192.168.5.1/24`，br-lan 桥接 eth0–eth3
- WAN: PPPoE，设备 `eth4.3961`（VLAN 3961）
- 默认密码: 空（`passwd -d root`）
- IPv6: 全部禁用

### 内置插件及来源

| 插件 | 来源 |
|---|---|
| luci-app-openclash | vernesong/OpenClash |
| luci-app-ddns-go | sirpdboy/luci-app-ddns-go |
| luci-app-advancedplus | sirpdboy/luci-app-advancedplus |
| luci-app-autoupdate | soapmancn/luci-app-autoupdate |
| luci-app-turboacc | chenmozhijin/turboacc (branch: luci) |
| luci-app-vlmcsd | openwrt-develop/luci-app-vlmcsd |
| luci-app-upnp | OpenWrt 官方 luci feed |

### R86S 网卡驱动
`kmod-igc` `kmod-mlx4-core` `kmod-mlx4-en` `kmod-e1000e` 均在 `.config` 中显式选中。

## 重要约束

- **miniupnpd-nftables**（不是 miniupnpd-iptables）— OpenWrt 24.10 使用 firewall4/nftables
- **dnsmasq-full** 替换 dnsmasq — OpenClash DNS 劫持需要
- **vlmcsd**: cokebar 原版 2024-04 已归档，使用 openwrt-develop fork
- autoupdate 检测 URL: `https://api.github.com/repos/lqqk7/Tutu_GW/releases/latest`

## 修改 .config

只写与默认值不同的行（defconfig 格式）。修改后无需本地构建验证，提交后 workflow 自动跑 `make defconfig` 补全。

添加/删除包的格式：
```
CONFIG_PACKAGE_<pkgname>=y    # 添加
# CONFIG_PACKAGE_<pkgname> is not set  # 排除
```

## 添加新第三方插件

1. 在 `scripts/diy-part1.sh` 末尾添加 `git clone` 命令
2. 在 `config/.config` 添加对应 `CONFIG_PACKAGE_` 行
3. 提交，等下次 workflow 触发
