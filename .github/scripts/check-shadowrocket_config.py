#!/usr/bin/env python3
from __future__ import annotations

import sys
from ipaddress import IPv6Network, ip_network
from pathlib import Path


CONFIG = Path("rules/Tutu-GW.conf")
IPV6_RULE_LISTS = (
    Path("rules/AI-All.list"),
    Path("rules/Anthropic.list"),
)
IPV6_SAFE_MODULES = (
    Path("modules/AI-All.sgmodule"),
    Path("modules/Anthropic.sgmodule"),
)
CHINA_DOMAIN_SET = (
    "DOMAIN-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"
    "rule/Shadowrocket/ChinaMaxNoIP/ChinaMaxNoIP_Domain.list,DIRECT"
)
CHINA_RULE_SET = (
    "RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"
    "rule/Shadowrocket/ChinaMaxNoIP/ChinaMaxNoIP.list,DIRECT"
)
LOCAL_RULE_PREFIX = (
    "DOMAIN,localhost,DIRECT",
    "DOMAIN-SUFFIX,local,DIRECT",
    "DOMAIN-SUFFIX,lan,DIRECT",
    "DOMAIN-SUFFIX,internal,DIRECT",
    "DOMAIN,captive.apple.com,DIRECT",
    "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve",
    "IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,169.254.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
    "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,224.0.0.0/4,DIRECT,no-resolve",
    "IP-CIDR,255.255.255.255/32,DIRECT,no-resolve",
)
LOCAL_IPV6_RULES = (
    "IP-CIDR6,::1/128,DIRECT,no-resolve",
    "IP-CIDR6,fc00::/7,DIRECT,no-resolve",
    "IP-CIDR6,fe80::/10,DIRECT,no-resolve",
)
FLASHFORGE_DIRECT_RULES = (
    "DOMAIN-SUFFIX,flashforge.com,DIRECT",
    "DOMAIN-SUFFIX,fdmcloud.flashforge.com,DIRECT",
    "DOMAIN-SUFFIX,voxelshare.com,DIRECT",
    "DOMAIN,flashforge.oss-us-east-1.aliyuncs.com,DIRECT",
    "DOMAIN-SUFFIX,netease.im,DIRECT",
    "DOMAIN,httpdns.n.netease.com,DIRECT",
    "DOMAIN,nos.netease.com,DIRECT",
    "DOMAIN-SUFFIX,chatnos.com,DIRECT",
)
PUBLIC_IPV6_REJECT = "IP-CIDR6,::/0,REJECT,no-resolve"
MANAGED_START = "# BEGIN UPSTREAM SR_CNIP MANAGED RULES"
MANAGED_END = "# END UPSTREAM SR_CNIP MANAGED RULES"
PROXY_POLICY = "fallback"
FINAL_RULE = f"FINAL,{PROXY_POLICY}"
EXPECTED_DOH = (
    "https://cloudflare-dns.com/dns-query#proxy=fallback,"
    "https://dns.google/dns-query#proxy=fallback"
)
EXPECTED_PROXY_GROUP = (
    "fallback = fallback,US-9929V3-TUTU,US-4837V2-TUTU,US-9929V4-TUTU,"
    "专线A1-美国7-家宽静态IP-适合AI-CLAUDE等TIKTOK数据好银行全解锁-3倍率,"
    "专线A1-美国7A-家宽静态IP-适合AI-CLAUDE等TIKTOK数据好银行全解锁-3倍率,"
    "专线A1-美国8-双ISP家宽IP-适合AI-CLAUDE等-3倍率,"
    "专线A1-美国9-双ISP家宽IP-适合AI-CLAUDE等-3倍率,"
    "专线A1-美国6-家宽住宅IP-适合AI-CLAUDE等TIKTOK数据好银行全解锁-3倍率,"
    "D美国8-3倍率-双ISP家宽IP适合AI-CLAUDE等TIKTOK数据好银行全解锁,"
    "D美国4-双ISP家宽IP-适合AI-CLAUDE等-3倍率,"
    "D美国6-4倍率-家宽住宅IP适合AI-CLAUDE等TIKTOK数据好银行全解锁,"
    "D美国7-4倍率-家宽住宅IP适合AI-CLAUDE等TIKTOK数据好银行全解锁,"
    "D美国9-4倍率-双ISP家宽IP适合AI-CLAUDE等TIKTOK数据好银行全解锁,"
    "D美国7A-4倍率-家宽住宅IP适合AI-CLAUDE等TIKTOK数据好银行全解锁,"
    "timeout=5,interval=600,url=http://www.gstatic.com/generate_204"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def section(lines: list[str], name: str) -> list[str]:
    start = lines.index(name)
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("[")),
        len(lines),
    )
    return lines[start + 1 : end]


def ipv6_cidr_rules(lines: list[str]) -> list[str]:
    matches: list[str] = []
    for line in lines:
        if not line.startswith(("IP-CIDR,", "IP-CIDR6,")):
            continue
        parts = line.split(",")
        if len(parts) < 2:
            continue
        network = ip_network(parts[1], strict=False)
        if isinstance(network, IPv6Network):
            matches.append(line)
    return matches


def rule_policy(rule: str) -> str:
    parts = rule.split(",")
    return parts[-2] if parts[-1].lower() == "no-resolve" else parts[-1]


def main() -> int:
    lines = [line.strip() for line in CONFIG.read_text(encoding="utf-8").splitlines()]
    general = section(lines, "[General]")
    require(
        lines.count("[Proxy Group]") == 1,
        "[Proxy Group] section header must occur exactly once",
    )
    proxy_groups = section(lines, "[Proxy Group]")
    rules = section(lines, "[Rule]")
    require(
        proxy_groups.count(EXPECTED_PROXY_GROUP) == 1
        and lines.count(EXPECTED_PROXY_GROUP) == 1,
        "[Proxy Group] must contain exactly one canonical fallback definition",
    )
    fallback_parts = [part.strip() for part in EXPECTED_PROXY_GROUP.split(" = ", 1)[1].split(",")]
    require(fallback_parts[0] == "fallback", "fallback group must use the fallback type")
    require(
        fallback_parts[1:4] == ["US-9929V3-TUTU", "US-4837V2-TUTU", "US-9929V4-TUTU"],
        "the three self-hosted nodes must be first in the fallback group",
    )
    options = fallback_parts[-3:]
    require(len(fallback_parts[1:-3]) == 14, "fallback group must contain exactly 14 nodes")
    require(
        options == ["timeout=5", "interval=600", "url=http://www.gstatic.com/generate_204"],
        "fallback health-check options must be timeout=5, interval=600, and the expected URL",
    )
    require(
        general.count(f"dns-server = {EXPECTED_DOH}") == 1,
        "dns-server DoH endpoints must use #proxy=fallback",
    )
    require(
        general.count(f"fallback-dns-server = {EXPECTED_DOH}") == 1,
        "fallback-dns-server DoH endpoints must use #proxy=fallback",
    )
    require(
        general.count("always-ip-address = true") == 1
        and lines.count("always-ip-address = true") == 1,
        "[General] must contain exactly one always-ip-address = true",
    )
    effective_rules = [line for line in rules if line and not line.startswith("#")]
    require(
        all(rule_policy(rule) != "PROXY" for rule in effective_rules),
        "[Rule] must not contain the unbound PROXY policy",
    )
    require(
        all(rule_policy(rule) in {"DIRECT", "REJECT", PROXY_POLICY} for rule in effective_rules),
        "[Rule] contains a policy other than DIRECT, REJECT, or fallback",
    )
    flashforge_targets = {
        tuple(rule.split(",")[:2]) for rule in FLASHFORGE_DIRECT_RULES
    }
    flashforge_rules = [
        rule
        for rule in effective_rules
        if tuple(rule.split(",")[:2]) in flashforge_targets
    ]
    require(
        flashforge_rules == list(FLASHFORGE_DIRECT_RULES),
        "Flashforge cloud and MQTT rules must occur exactly once and remain DIRECT",
    )

    require("ipv6 = false" in lines, "missing ipv6 = false")
    require("prefer-ipv6 = false" in lines, "missing prefer-ipv6 = false")
    bypass_tun = next((line for line in lines if line.startswith("bypass-tun = ")), "")
    require(bypass_tun, "missing bypass-tun")
    require(":" not in bypass_tun, "IPv6 network must not bypass TUN")
    require(rules.count(PUBLIC_IPV6_REJECT) == 1, "public IPv6 reject must occur exactly once")

    reject_index = effective_rules.index(PUBLIC_IPV6_REJECT)
    for rule in LOCAL_IPV6_RULES:
        require(rule in effective_rules, f"missing local IPv6 exception: {rule}")
    require(
        effective_rules[:reject_index] == [*LOCAL_RULE_PREFIX, *LOCAL_IPV6_RULES],
        "public IPv6 reject must immediately follow the local network rules and IPv6 exceptions",
    )

    ipv6_routes = [rule for rule in rules if rule.startswith("IP-CIDR6,")]
    require(
        set(ipv6_routes) == set(LOCAL_IPV6_RULES) | {PUBLIC_IPV6_REJECT},
        f"unexpected IPv6 route bypasses the public reject: {ipv6_routes}",
    )
    require(
        not any(rule.startswith("IP-CIDR,") and ":" in rule.split(",", 2)[1] for rule in rules),
        "public IPv6 route expressed with IP-CIDR bypasses the reject policy",
    )

    for rule_list in IPV6_RULE_LISTS:
        list_lines = [
            line.strip() for line in rule_list.read_text(encoding="utf-8").splitlines()
        ]
        ipv6_routes = ipv6_cidr_rules(list_lines)
        require(
            not ipv6_routes,
            f"{rule_list} must not contain IPv6 CIDR rules: {ipv6_routes}",
        )

    for module in IPV6_SAFE_MODULES:
        module_lines = [
            line.strip() for line in module.read_text(encoding="utf-8").splitlines()
        ]
        module_rules = [
            line for line in section(module_lines, "[Rule]") if line and not line.startswith("#")
        ]
        require(
            module_rules.count(PUBLIC_IPV6_REJECT) == 1,
            f"{module} must contain exactly one public IPv6 reject",
        )
        expected_ipv6_prefix = [*LOCAL_IPV6_RULES, PUBLIC_IPV6_REJECT]
        require(
            module_rules[: len(expected_ipv6_prefix)] == expected_ipv6_prefix,
            f"{module} must start with local IPv6 exceptions followed by the public reject",
        )
        module_ipv6_routes = ipv6_cidr_rules(module_rules)
        require(
            module_ipv6_routes == expected_ipv6_prefix,
            f"{module} must not contain other IPv6 DIRECT/PROXY rules: {module_ipv6_routes}",
        )
        proxy_rule_set_indices = [
            index
            for index, rule in enumerate(module_rules)
            if rule.startswith("RULE-SET,") and rule.endswith(",PROXY")
        ]
        require(proxy_rule_set_indices, f"{module} must contain a PROXY RULE-SET")
        require(
            proxy_rule_set_indices[0] == len(expected_ipv6_prefix),
            f"{module} first PROXY RULE-SET must immediately follow the IPv6 safety prefix",
        )
        require(
            module_rules.index(PUBLIC_IPV6_REJECT) < min(proxy_rule_set_indices),
            f"{module} public IPv6 reject must precede every PROXY RULE-SET",
        )
    china_domain_set_rules = [
        rule for rule in effective_rules if "ChinaMaxNoIP_Domain.list" in rule
    ]
    require(
        china_domain_set_rules == [CHINA_DOMAIN_SET],
        "ChinaMaxNoIP_Domain.list must appear exactly once as the DIRECT DOMAIN-SET",
    )
    china_rule_set_rules = [
        rule for rule in effective_rules if "ChinaMaxNoIP.list" in rule
    ]
    require(
        china_rule_set_rules == [CHINA_RULE_SET],
        "ChinaMaxNoIP.list must appear exactly once as the DIRECT RULE-SET",
    )
    require(
        rules.count(MANAGED_START) == 1 and rules.count(MANAGED_END) == 1,
        "managed upstream markers must each occur exactly once",
    )
    china_domain_index = rules.index(CHINA_DOMAIN_SET)
    china_rule_index = rules.index(CHINA_RULE_SET)
    managed_index = rules.index(MANAGED_START)
    local_proxy_indices = [
        index
        for index, rule in enumerate(rules[:managed_index])
        if not rule.startswith("#") and rule_policy(rule) == PROXY_POLICY
    ]
    require(local_proxy_indices, "missing local explicit fallback rules")
    require(
        max(local_proxy_indices) < min(china_domain_index, china_rule_index),
        "China mainland DIRECT sets must follow all local explicit fallback rules",
    )
    require(
        max(china_domain_index, china_rule_index) < managed_index,
        "China mainland DIRECT sets must precede the upstream fallback snapshot",
    )
    require(managed_index < rules.index(MANAGED_END), "managed upstream markers are out of order")
    managed_rules = rules[managed_index + 1 : rules.index(MANAGED_END)]
    require(
        all(",PROXY" not in rule for rule in managed_rules),
        "managed upstream block must not contain PROXY",
    )
    china_domain_effective_index = effective_rules.index(CHINA_DOMAIN_SET)
    china_rule_effective_index = effective_rules.index(CHINA_RULE_SET)
    require(
        abs(china_domain_effective_index - china_rule_effective_index) == 1,
        "ChinaMaxNoIP DOMAIN-SET and RULE-SET must be adjacent",
    )
    for rule in (
        "DOMAIN-SUFFIX,cn,DIRECT",
        "DOMAIN-SUFFIX,xn--fiqs8s,DIRECT",
        "DOMAIN-SUFFIX,xn--fiqz9s,DIRECT",
        "GEOIP,CN,DIRECT",
    ):
        require(rule in rules, f"missing China DIRECT fallback: {rule}")
        require(rules.index(rule) < rules.index(FINAL_RULE), f"China DIRECT fallback must precede FINAL: {rule}")

    require(effective_rules[-1] == FINAL_RULE, "FINAL,fallback must be the last rule")

    print("Shadowrocket config checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
