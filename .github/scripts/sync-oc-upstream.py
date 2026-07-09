#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
import urllib.request
from pathlib import Path


UPSTREAM_URL = os.environ.get(
    "UPSTREAM_OC_LITE_URL",
    "https://raw.githubusercontent.com/Aethersailor/Custom_OpenClash_Rules/main/cfg/Custom_Clash_Lite.ini",
)
RAW_BASE = os.environ.get(
    "TUTU_GW_RAW_BASE",
    "https://raw.githubusercontent.com/lqqk7/Tutu_GW/main",
)
TARGET = Path("OC_Rules/Custom_Clash_Lite.ini")
AI_PROVIDER = Path("OC_Rules/rule/AI_Classical.yaml")
AD5X_PROVIDER = Path("OC_Rules/rule/AD5X_Classical.yaml")
SHADOWROCKET_AI_RULES = Path("rules/AI-All.list")

US_NODE_FILTER = r"(?i)^(?:.*9929v3.*|(?=.*AI)(?=.*美国)(?=.*家宽).*)$"

CUSTOM_RULESETS = [
    f"ruleset=🤖 AI服务,clash-classic:{RAW_BASE}/OC_Rules/rule/AI_Classical.yaml,28800",
    f"ruleset=🖨️ AD5X切片,clash-classic:{RAW_BASE}/OC_Rules/rule/AD5X_Classical.yaml,28800",
]

CUSTOM_PROXY_GROUPS = [
    "custom_proxy_group=🚀 手动选择`select`[]♻️ 自动选择`[]🇺🇸 美国节点`[]🎯 全球直连",
    f"custom_proxy_group=♻️ 自动选择`url-test`{US_NODE_FILTER}`https://cp.cloudflare.com/generate_204`300,,50",
    "custom_proxy_group=🤖 AI服务`select`[]🚀 手动选择`[]♻️ 自动选择`[]🇺🇸 美国节点",
    "custom_proxy_group=🖨️ AD5X切片`select`[]🎯 全球直连`[]🚀 手动选择`[]♻️ 自动选择`[]🇺🇸 美国节点",
    "custom_proxy_group=🚀 GitHub`select`[]🚀 手动选择`[]♻️ 自动选择`[]🎯 全球直连`[]🇺🇸 美国节点",
    "custom_proxy_group=📢 谷歌FCM`select`[]🚀 手动选择`[]♻️ 自动选择`[]🎯 全球直连`[]🇺🇸 美国节点",
    "custom_proxy_group=🇬 谷歌服务`select`[]🚀 手动选择`[]♻️ 自动选择`[]🎯 全球直连`[]🇺🇸 美国节点",
    "custom_proxy_group=🍎 苹果服务`select`[]🎯 全球直连`[]🚀 手动选择`[]♻️ 自动选择`[]🇺🇸 美国节点",
    "custom_proxy_group=Ⓜ️ 微软服务`select`[]🎯 全球直连`[]🚀 手动选择`[]♻️ 自动选择`[]🇺🇸 美国节点",
    "custom_proxy_group=🎮 游戏平台`select`[]🎯 全球直连`[]🚀 手动选择`[]♻️ 自动选择`[]🇺🇸 美国节点",
    "custom_proxy_group=🎮 Steam`select`[]🎯 全球直连`[]🚀 手动选择`[]♻️ 自动选择`[]🇺🇸 美国节点",
    "custom_proxy_group=🚀 测速工具`select`[]🎯 全球直连`[]🚀 手动选择`[]♻️ 自动选择`[]🇺🇸 美国节点",
    "custom_proxy_group=🐟 漏网之鱼`select`[]🚀 手动选择`[]♻️ 自动选择`[]🎯 全球直连`[]🇺🇸 美国节点",
    "custom_proxy_group=🔀 非标端口`select`[]🐟 漏网之鱼`[]🎯 全球直连",
    f"custom_proxy_group=🇺🇸 美国节点`url-test`{US_NODE_FILTER}`https://cp.cloudflare.com/generate_204`300,,50",
    "custom_proxy_group=🎯 全球直连`select`[]DIRECT",
]

AD5X_RULES = [
    "DOMAIN-SUFFIX,flashforge.com",
    "DOMAIN-SUFFIX,fdmcloud.flashforge.com",
    "DOMAIN-SUFFIX,voxelshare.com",
    "DOMAIN,flashforge.oss-us-east-1.aliyuncs.com",
    "DOMAIN-SUFFIX,netease.im",
    "DOMAIN,httpdns.n.netease.com",
    "DOMAIN,nos.netease.com",
    "DOMAIN-SUFFIX,chatnos.com",
]

FORBIDDEN_RULE_HINTS = ("广告", "去广告", "拦截", "adblock", "reject")
FORBIDDEN_REGION_GROUPS = ("🇭🇰", "🇯🇵", "🇸🇬", "🇼🇸", "🇰🇷", "香港节点", "日本节点", "新加坡节点", "台湾节点", "韩国节点")


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Tutu-GW-oc-sync"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def is_forbidden_line(line: str) -> bool:
    lowered = line.lower()
    return any(hint in lowered for hint in FORBIDDEN_RULE_HINTS)


def insert_custom_rulesets(lines: list[str]) -> list[str]:
    anchor = "ruleset=🚀 手动选择,clash-classic:https://testingcf.jsdelivr.net/gh/Aethersailor/Custom_OpenClash_Rules@main/rule/Custom_Proxy_Classical_IP.yaml,28800"
    if anchor not in lines:
        raise RuntimeError("Upstream proxy ruleset anchor not found")

    output: list[str] = []
    inserted = False
    for line in lines:
        if is_forbidden_line(line):
            continue
        output.append(line)
        if line == anchor and not inserted:
            output.append(";本仓库自定义规则")
            output.extend(CUSTOM_RULESETS)
            inserted = True

    return output


def replace_proxy_groups(lines: list[str]) -> list[str]:
    start_marker = ";设置节点分组标志位"
    end_marker = ";设置分组标志位"
    try:
        start = lines.index(start_marker)
        end = lines.index(end_marker)
    except ValueError as error:
        raise RuntimeError("Upstream proxy group markers not found") from error

    if start >= end:
        raise RuntimeError("Invalid upstream proxy group marker order")

    replacement = [
        start_marker,
        *CUSTOM_PROXY_GROUPS,
        end_marker,
    ]
    return [*lines[:start], *replacement, *lines[end + 1 :]]


def normalize_shadowrocket_rule(line: str) -> str | None:
    line = re.split(r"\s+#", line.strip(), maxsplit=1)[0].strip()
    if not line or line.startswith("#"):
        return None

    parts = [part.strip() for part in line.split(",")]
    if parts[0] not in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6"}:
        return None
    if len(parts) < 2:
        return None

    return ",".join(parts[:2])


def write_classical_provider(path: Path, rules: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = ["payload:"]
    payload.extend(f"  - {rule}" for rule in rules)
    path.write_text("\n".join(payload) + "\n", encoding="utf-8")


def write_custom_providers() -> None:
    ai_rules: list[str] = []
    seen: set[str] = set()
    for line in SHADOWROCKET_AI_RULES.read_text(encoding="utf-8").splitlines():
        rule = normalize_shadowrocket_rule(line)
        if rule and rule not in seen:
            ai_rules.append(rule)
            seen.add(rule)

    if not ai_rules:
        raise RuntimeError("No AI rules generated")

    write_classical_provider(AI_PROVIDER, ai_rules)
    write_classical_provider(AD5X_PROVIDER, AD5X_RULES)


def validate_generated(text: str) -> None:
    required = [
        "[custom]",
        *CUSTOM_RULESETS,
        f"custom_proxy_group=🇺🇸 美国节点`url-test`{US_NODE_FILTER}`https://cp.cloudflare.com/generate_204`300,,50",
        "ruleset=🤖 AI服务,clash-classic:",
        "ruleset=🖨️ AD5X切片,clash-classic:",
        "enable_rule_generator=true",
        "overwrite_original_rules=true",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(f"Generated config missing required content: {missing}")

    custom_group_lines = [line for line in text.splitlines() if line.startswith("custom_proxy_group=")]
    forbidden = [
        line
        for line in custom_group_lines
        if any(region in line for region in FORBIDDEN_REGION_GROUPS)
    ]
    if forbidden:
        raise RuntimeError(f"Forbidden non-US proxy groups remain: {forbidden}")

    if any(is_forbidden_line(line) for line in text.splitlines()):
        raise RuntimeError("Forbidden ad-block/reject content remains")


def main() -> int:
    upstream = fetch_text(UPSTREAM_URL)
    lines = [line.rstrip() for line in upstream.replace("\r\n", "\n").splitlines()]
    lines = insert_custom_rulesets(lines)
    lines = replace_proxy_groups(lines)
    output = "\n".join(lines).rstrip() + "\n"
    validate_generated(output)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(output, encoding="utf-8")
    write_custom_providers()
    print(f"Synced OpenClash Lite config into {TARGET}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
