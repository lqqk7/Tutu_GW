#!/bin/bash
# diy-part2.sh — 在 feeds install 之后执行
# 将 files/ 目录内容覆盖到 OpenWrt 构建树，实现首次启动自动配置

set -e

echo ">>> [diy-part2] 复制自定义文件..."
mkdir -p files
cp -r "$GITHUB_WORKSPACE/files/." ./files/

echo ">>> [diy-part2] 移除 feeds 中与第三方代理插件冲突的旧包..."
rm -rf feeds/packages/net/{chinadns-ng,dns2socks,hysteria,ipt2socks,microsocks,mosdns,naiveproxy,shadow-tls,shadowsocks-libev,shadowsocks-rust,shadowsocksr-libev,simple-obfs,sing-box,tcping,trojan-plus,tuic-client,v2ray-core,v2ray-geodata,v2ray-plugin,xray-core,xray-plugin,geoview}
rm -rf feeds/luci/applications/luci-app-passwall

echo ">>> [diy-part2] 完成"
