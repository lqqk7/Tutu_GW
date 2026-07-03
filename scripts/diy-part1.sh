#!/bin/bash
# diy-part1.sh — 在 feeds update/install 之前执行
# 将第三方软件包克隆到 package/ 目录，供 feeds install 和 make menuconfig 发现

set -e

echo ">>> [diy-part1] 克隆第三方软件包..."

# OpenClash (vernesong 官方唯一权威源)
git clone --depth=1 https://github.com/vernesong/OpenClash.git package/OpenClash

# ddns-go LuCI 界面 (v6.9.4，v6.16.x 要求 Go 1.25 与 OpenWrt 24.10 不兼容)
git clone --depth=1 -b v6.9.4 https://github.com/sirpdboy/luci-app-ddns-go.git package/luci-app-ddns-go

# Advanced Plus
git clone --depth=1 https://github.com/sirpdboy/luci-app-advancedplus.git package/luci-app-advancedplus

# Autoupdate (支持 GitHub API 自动检测版本并更新)
git clone --depth=1 https://github.com/xztxy/luci-app-autoupdate.git package/luci-app-autoupdate

# MosDNS v5 + geodata
# Pin to the last known OpenWrt 24.10-compatible package: MosDNS 5.3.3 uses Go 1.22,
# while current v5 tracks MosDNS 5.3.4 which requires newer Go than openwrt-24.10.
MOSDNS_PACKAGE_COMMIT="83b370771678527d54a9d95c640431324134dd9f"
mkdir -p package/mosdns
git -C package/mosdns init
git -C package/mosdns remote add origin https://github.com/sbwml/luci-app-mosdns.git
git -C package/mosdns fetch --depth=1 origin "$MOSDNS_PACKAGE_COMMIT"
git -C package/mosdns checkout --detach FETCH_HEAD
git clone --depth=1 https://github.com/sbwml/v2ray-geodata.git package/v2ray-geodata

# PassWall (官方组织仓库：LuCI + 核心依赖)
git clone --depth=1 https://github.com/Openwrt-Passwall/openwrt-passwall-packages.git package/passwall-packages
git clone --depth=1 https://github.com/Openwrt-Passwall/openwrt-passwall.git package/passwall-luci
# 使用 sbwml/v2ray-geodata，避免与 PassWall 依赖仓库重复定义 geodata 包
rm -rf package/passwall-packages/v2ray-geodata

# SSR Plus (helloworld)
git clone --depth=1 https://github.com/fw876/helloworld.git package/helloworld
# helloworld 与 PassWall 依赖仓库有大量同名包，只保留 SSR Plus 独有包和 LuCI
rm -rf package/helloworld/{chinadns-ng,dns2socks,hysteria,ipt2socks,microsocks,mosdns,naiveproxy,shadow-tls,shadowsocks-libev,shadowsocks-rust,shadowsocksr-libev,simple-obfs,tcping,tuic-client,v2ray-plugin,xray-core,xray-plugin}

# TurboAcc LuCI 界面 (chenmozhijin fork，支持 firewall4/nftables)
git clone --depth=1 -b luci https://github.com/chenmozhijin/turboacc.git package/turboacc
# kmod-nft-fullcone (turboacc 依赖，来自 package 分支)
git clone --depth=1 -b package https://github.com/chenmozhijin/turboacc.git /tmp/turboacc-pkg
cp -r /tmp/turboacc-pkg/nft-fullcone package/nft-fullcone
rm -rf /tmp/turboacc-pkg

# vlmcsd KMS Server 二进制包 + LuCI 界面 (openwrt-develop fork，cokebar 原版已归档)
git clone --depth=1 https://github.com/openwrt-develop/openwrt-vlmcsd.git package/openwrt-vlmcsd
git clone --depth=1 https://github.com/openwrt-develop/luci-app-vlmcsd.git package/luci-app-vlmcsd

echo ">>> [diy-part1] 完成"
