#!/bin/bash
# diy-part2.sh — 在 feeds install 之后执行
# 将 files/ 目录内容覆盖到 OpenWrt 构建树，实现首次启动自动配置

set -e

echo ">>> [diy-part2] 复制自定义文件..."
cp -r "$GITHUB_WORKSPACE/files/." ./

echo ">>> [diy-part2] 完成"
