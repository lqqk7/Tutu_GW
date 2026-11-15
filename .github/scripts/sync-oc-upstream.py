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
BASE_CONFIG = Path("OC_Rules/Custom_Clash_Base.yaml")
CLIENT_TARGET = Path("OC_Rules/Custom_Clash_Client.ini")
CLIENT_BASE_CONFIG = Path("OC_Rules/Custom_Clash_Client_Base.yaml")
BASE_LINE = f"clash_rule_base={RAW_BASE}/{BASE_CONFIG}"
CLIENT_BASE_LINE = f"clash_rule_base={RAW_BASE}/{CLIENT_BASE_CONFIG}"
AI_PROVIDER = Path("OC_Rules/rule/AI_Classical.yaml")
AD5X_PROVIDER = Path("OC_Rules/rule/AD5X_Classical.yaml")
CN_HTTPDNS_PROVIDER = Path("OC_Rules/rule/CN_HTTPDNS_Classical.yaml")
AI_RULES = Path("OC_Rules/source/AI.list")
POLYMARKET_RULES = Path("OC_Rules/source/Polymarket.list")
POLYMARKET_PROVIDER = Path("OC_Rules/rule/Polymarket_Classical.yaml")
POLYMARKET_GROUP = "Polymarket 国际站"
POLYMARKET_RULESET = f"ruleset={POLYMARKET_GROUP},clash-classic:{RAW_BASE}/OC_Rules/rule/Polymarket_Classical.yaml,28800"
AI_RULESET = f"ruleset=🤖 AI服务,clash-classic:{RAW_BASE}/OC_Rules/rule/AI_Classical.yaml,28800"
POLYMARKET_NODE_FILTER = r"(?i)^HK-.+$"
POLYMARKET_PROXY_GROUP = f"custom_proxy_group={POLYMARKET_GROUP}`select`{POLYMARKET_NODE_FILTER}`[]REJECT"

INCLUDE_REMARKS_FILTER = r"(?i)^(?:US-RELAY|HK)-.+$"
INCLUDE_REMARKS = f"include_remarks={INCLUDE_REMARKS_FILTER}"

MANUAL_NODE_FILTER = r"(?i)^US-RELAY-.+$"
MANUAL_GROUP = f"custom_proxy_group=🚀 手动选择`select`{MANUAL_NODE_FILTER}`[]REJECT"

# api.asailor.org drops native base groups and cannot accept inline providers.
# Its converter preserves these literal rules, including the complete AND.
IPV6_BLOCK_RULESET = "ruleset=REJECT,[]IP-CIDR6,::/0,no-resolve"
QUIC_BLOCK_RULESET = "ruleset=REJECT,[]AND,((NETWORK,UDP),(DST-PORT,443))"

CUSTOM_RULESETS = [
    f"ruleset=🖨️ AD5X切片,clash-classic:{RAW_BASE}/OC_Rules/rule/AD5X_Classical.yaml,28800",
    # WeChat picks upload servers via its HTTPDNS; resolving it abroad breaks image sends.
    f"ruleset=🎯 全球直连,clash-classic:{RAW_BASE}/OC_Rules/rule/CN_HTTPDNS_Classical.yaml,28800",
    "ruleset=🚀 手动选择,clash-domain:https://testingcf.jsdelivr.net/gh/Aethersailor/Custom_OpenClash_Rules@main/rule/Encrypted_DNS_Domain.yaml,28800",
    "ruleset=🚀 手动选择,clash-classic:https://testingcf.jsdelivr.net/gh/Aethersailor/Custom_OpenClash_Rules@main/rule/Encrypted_DNS_Classical_IP.yaml,28800",
]

CUSTOM_PROXY_GROUPS = [
    POLYMARKET_PROXY_GROUP,
    MANUAL_GROUP,
    "custom_proxy_group=🤖 AI服务`select`[]🚀 手动选择",
    "custom_proxy_group=🖨️ AD5X切片`select`[]🎯 全球直连`[]🚀 手动选择",
    "custom_proxy_group=🚀 GitHub`select`[]🚀 手动选择`[]🎯 全球直连",
    "custom_proxy_group=📢 谷歌FCM`select`[]🚀 手动选择`[]🎯 全球直连",
    "custom_proxy_group=🇬 谷歌服务`select`[]🚀 手动选择`[]🎯 全球直连",
    "custom_proxy_group=🍎 苹果服务`select`[]🎯 全球直连`[]🚀 手动选择",
    "custom_proxy_group=Ⓜ️ 微软服务`select`[]🎯 全球直连`[]🚀 手动选择",
    "custom_proxy_group=🎮 游戏平台`select`[]🎯 全球直连`[]🚀 手动选择",
    "custom_proxy_group=🎮 Steam`select`[]🎯 全球直连`[]🚀 手动选择",
    "custom_proxy_group=🚀 测速工具`select`[]🎯 全球直连`[]🚀 手动选择",
    "custom_proxy_group=🐟 漏网之鱼`select`[]🚀 手动选择`[]🎯 全球直连",
    "custom_proxy_group=🔀 非标端口`select`[]🐟 漏网之鱼`[]🎯 全球直连",
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

CN_HTTPDNS_RULES = [
    "DOMAIN-SUFFIX,dns.weixin.qq.com",
    "DOMAIN-SUFFIX,dns.weixin.qq.com.cn",
    "DOMAIN-SUFFIX,udns.weixin.qq.com",
    "DOMAIN-SUFFIX,dns.wechat.com",
    "DOMAIN-SUFFIX,paydns.weixin.qq.com",
    "DOMAIN-SUFFIX,paydns.wechatpay.cn",
    "DOMAIN-SUFFIX,dns.qq.com",
]

BASE_CONFIG_TEXT = """\
mixed-port: 7893
allow-lan: true
mode: rule
log-level: info
ipv6: false
unified-delay: true
tcp-concurrent: true

profile:
  store-selected: true
  store-fake-ip: true

sniffer:
  enable: true
  override-destination: true
  sniff:
    TLS:
      ports:
        - 443
        - 8443
    HTTP:
      ports:
        - 80
        - 8080-8880
      override-destination: true
  skip-domain:
    - "+.apple.com"
    - "+.flashforge.com"
    - "+.fdmcloud.flashforge.com"
    - "+.voxelshare.com"
    - "+.netease.im"
    - "+.chatnos.com"
  parse-pure-ip: true
  force-dns-mapping: true

dns:
  enable: true
  cache-algorithm: arc
  use-hosts: true
  use-system-hosts: false
  listen: 0.0.0.0:7874
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  fake-ip-filter:
    - "*.lan"
    - "*.local"
    - "localhost.ptlogin2.qq.com"
    - "+.flashforge.com"
    - "+.fdmcloud.flashforge.com"
    - "+.voxelshare.com"
    - "+.netease.im"
    - "+.chatnos.com"
    - "geosite:cn"
  fake-ip-filter-mode: blacklist
  respect-rules: true
  default-nameserver:
    - tls://1.1.1.1:853
    - tls://8.8.8.8:853
  proxy-server-nameserver:
    - tls://1.1.1.1:853
    - tls://8.8.8.8:853
  nameserver:
    - https://cloudflare-dns.com/dns-query#🚀 手动选择
    - https://dns.google/dns-query#🚀 手动选择
    - https://dns.quad9.net/dns-query#🚀 手动选择
  nameserver-policy:
    "geosite:cn":
      - https://dns.alidns.com/dns-query
      - https://doh.pub/dns-query
"""

# Desktop/mobile clients share the router rules; only the gateway-specific base differs.
CLIENT_TUN_TEXT = """\
tun:
  enable: true
  stack: mixed
  auto-route: true
  auto-detect-interface: true
  strict-route: true
  dns-mode: hijack
  inet6-address:
    - fdfe:dcba:9876::1/126
  dns-hijack:
    - any:53
    - tcp://any:53

"""


def build_client_base_config() -> str:
    replacements = [
        # Capture native IPv6 into TUN and reject it before all routing rules.
        # dns.ipv6 stays false: enabling IPv6 ingress is not enabling IPv6 egress.
        ("\nipv6: false\n", "\nipv6: true\n"),
        ("allow-lan: true\n", "allow-lan: false\n"),
        ("  listen: 0.0.0.0:7874\n", ""),
        ("\nsniffer:\n", f"\n{CLIENT_TUN_TEXT}sniffer:\n"),
    ]
    text = BASE_CONFIG_TEXT
    for old, new in replacements:
        if text.count(old) != 1:
            raise RuntimeError(f"Client base anchor not found exactly once: {old!r}")
        text = text.replace(old, new)
    return text


CLIENT_BASE_CONFIG_TEXT = build_client_base_config()

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
    # Match the resource identity while allowing the upstream CDN host to change.
    anchors = [line for line in lines if re.fullmatch(
        r"ruleset=🚀 手动选择,clash-classic:https://[^/]+/gh/"
        r"Aethersailor/Custom_OpenClash_Rules@main/rule/"
        r"Custom_Proxy_Classical_IP\.yaml,\d+", line
    )]
    if len(anchors) != 1:
        raise RuntimeError(f"Expected one upstream proxy ruleset anchor, found {len(anchors)}")
    anchor = anchors[0]

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


def insert_priority_rulesets(lines: list[str]) -> list[str]:
    # Private networks keep priority; service routing precedes every general rule.
    anchor = "ruleset=🎯 全球直连,[]GEOIP,private,no-resolve"
    if lines.count(anchor) != 1:
        raise RuntimeError("Expected one private-network ruleset anchor")
    index = lines.index(anchor) + 1
    output = [*lines[:index], QUIC_BLOCK_RULESET, POLYMARKET_RULESET, AI_RULESET, *lines[index:]]
    # IPv6 must be blocked even when its destination belongs to a private range.
    first_rule = next(i for i, line in enumerate(output) if line.startswith("ruleset="))
    output.insert(first_rule, IPV6_BLOCK_RULESET)
    return output


def insert_fail_closed_guards(lines: list[str]) -> list[str]:
    # Mihomo skips a rule when its selected proxy cannot carry UDP. Repeat the
    # same match with REJECT so it cannot fall through to a later direct rule.
    output: list[str] = []
    for line in lines:
        output.append(line)
        if line.startswith("ruleset="):
            group, match = line.removeprefix("ruleset=").split(",", 1)
            if group not in {"REJECT", "🎯 全球直连"}:
                output.append(f"ruleset=REJECT,{match}")
    return output


def insert_base_config(lines: list[str]) -> list[str]:
    base_line = BASE_LINE
    without_existing = [
        line
        for line in lines
        if not line.startswith(("clash_rule_base=", "include_remarks=", "exclude_remarks="))
    ]

    try:
        custom_index = without_existing.index("[custom]")
    except ValueError as error:
        raise RuntimeError("Upstream [custom] section not found") from error

    return [
        *without_existing[: custom_index + 1],
        base_line,
        INCLUDE_REMARKS,
        *without_existing[custom_index + 1 :],
    ]


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


def normalize_list_rule(line: str) -> str | None:
    line = re.split(r"\s+#", line.strip(), maxsplit=1)[0].strip()
    if not line or line.startswith("#"):
        return None

    parts = [part.strip() for part in line.split(",")]
    if parts[0] not in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6"}:
        return None
    if len(parts) < 2:
        return None

    # Classical providers support no-resolve on IP rules; keep the source option.
    if parts[0] in {"IP-CIDR", "IP-CIDR6"} and "no-resolve" in parts[2:]:
        return ",".join([*parts[:2], "no-resolve"])
    return ",".join(parts[:2])


def write_classical_provider(path: Path, rules: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = ["payload:"]
    payload.extend(f"  - {rule}" for rule in rules)
    path.write_text("\n".join(payload) + "\n", encoding="utf-8")


def write_custom_providers() -> None:
    ai_rules: list[str] = []
    seen: set[str] = set()
    for line in AI_RULES.read_text(encoding="utf-8").splitlines():
        rule = normalize_list_rule(line)
        if rule and rule not in seen:
            ai_rules.append(rule)
            seen.add(rule)

    if not ai_rules:
        raise RuntimeError("No AI rules generated")

    write_classical_provider(AI_PROVIDER, ai_rules)
    write_classical_provider(AD5X_PROVIDER, AD5X_RULES)
    write_classical_provider(CN_HTTPDNS_PROVIDER, CN_HTTPDNS_RULES)
    polymarket_rules = [
        rule for line in POLYMARKET_RULES.read_text(encoding="utf-8").splitlines()
        if (rule := normalize_list_rule(line))
    ]
    if not polymarket_rules:
        raise RuntimeError("No Polymarket rules generated")
    write_classical_provider(POLYMARKET_PROVIDER, polymarket_rules)


def write_base_config() -> None:
    BASE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    BASE_CONFIG.write_text(BASE_CONFIG_TEXT, encoding="utf-8")
    CLIENT_BASE_CONFIG.write_text(CLIENT_BASE_CONFIG_TEXT, encoding="utf-8")


# Node filters use the shared US-RELAY-/HK- prefixes on both platforms.
CLIENT_REPLACEMENTS = [
    (BASE_LINE, CLIENT_BASE_LINE),
]


def build_client_config(text: str) -> str:
    for old, new in CLIENT_REPLACEMENTS:
        if text.count(old) != 1:
            raise RuntimeError(f"Client config anchor not found exactly once: {old}")
        text = text.replace(old, new)
    return text


def validate_generated(text: str, replacements: list[tuple[str, str]] = []) -> None:
    required = [
        "[custom]",
        BASE_LINE,
        INCLUDE_REMARKS,
        *CUSTOM_RULESETS,
        POLYMARKET_RULESET,
        AI_RULESET,
        POLYMARKET_PROXY_GROUP,
        MANUAL_GROUP,
        IPV6_BLOCK_RULESET,
        QUIC_BLOCK_RULESET,
        "ruleset=🤖 AI服务,clash-classic:",
        "ruleset=🖨️ AD5X切片,clash-classic:",
        "enable_rule_generator=true",
        "overwrite_original_rules=true",
    ]
    replaced = dict(replacements)
    required = [replaced.get(item, item) for item in required]
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

    # Only our explicit security guards may reject. Upstream ad filtering is
    # still removed before guards are inserted.
    if any(is_forbidden_line(line) for line in text.splitlines()
           if not line.startswith("ruleset=REJECT,")
           and line not in {MANUAL_GROUP, POLYMARKET_PROXY_GROUP}):
        raise RuntimeError("Forbidden ad-block/reject content remains")

    if "全部节点" in text:
        raise RuntimeError("Redundant all-nodes group remains")

    if "机场自动" in text:
        raise RuntimeError("Airport proxy group remains")

    if any(legacy in text for legacy in ("自建优先", "🔒 RELAY", "9929", "`fallback`")):
        raise RuntimeError("Retired proxy groups remain")


def main() -> int:
    upstream = fetch_text(UPSTREAM_URL)
    lines = [line.rstrip() for line in upstream.replace("\r\n", "\n").splitlines()]
    lines = insert_base_config(lines)
    lines = insert_custom_rulesets(lines)
    lines = insert_priority_rulesets(lines)
    lines = insert_fail_closed_guards(lines)
    lines = replace_proxy_groups(lines)
    output = "\n".join(lines).rstrip() + "\n"
    validate_generated(output)
    client_output = build_client_config(output)
    validate_generated(client_output, CLIENT_REPLACEMENTS)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(output, encoding="utf-8")
    CLIENT_TARGET.write_text(client_output, encoding="utf-8")
    write_base_config()
    write_custom_providers()
    print(f"Synced OpenClash Lite config into {TARGET} and {CLIENT_TARGET}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
