#!/bin/bash
# diy-part1.sh — 在 feeds update/install 之前执行
# 将第三方软件包克隆到 package/ 目录，供 feeds install 和 make menuconfig 发现

set -e

echo ">>> [diy-part1] 克隆第三方软件包..."

# OpenClash (vernesong 官方唯一权威源)
git clone --depth=1 https://github.com/vernesong/OpenClash.git package/OpenClash

# ddns-go LuCI 界面
git clone --depth=1 https://github.com/sirpdboy/luci-app-ddns-go.git package/luci-app-ddns-go

# Advanced Plus
git clone --depth=1 https://github.com/sirpdboy/luci-app-advancedplus.git package/luci-app-advancedplus

# Autoupdate (固件自动更新，指向本仓库 releases)
git clone --depth=1 https://github.com/soapmancn/luci-app-autoupdate.git package/luci-app-autoupdate

# TurboAcc (chenmozhijin fork，支持 firewall4/nftables)
git clone --depth=1 -b luci https://github.com/chenmozhijin/turboacc.git package/turboacc

# vlmcsd KMS Server (openwrt-develop 活跃 fork，cokebar 原版已归档)
git clone --depth=1 https://github.com/openwrt-develop/luci-app-vlmcsd.git package/luci-app-vlmcsd

echo ">>> [diy-part1] 完成"
