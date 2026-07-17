#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


CONFIG = Path("rules/Tutu-GW.conf")
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
PUBLIC_IPV6_REJECT = "IP-CIDR6,::/0,REJECT,no-resolve"
MANAGED_START = "# BEGIN UPSTREAM SR_CNIP MANAGED RULES"
FINAL_RULE = "FINAL,PROXY"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    lines = [line.strip() for line in CONFIG.read_text(encoding="utf-8").splitlines()]
    rule_start = lines.index("[Rule]")
    rule_end = next(
        (index for index in range(rule_start + 1, len(lines)) if lines[index].startswith("[")),
        len(lines),
    )
    rules = lines[rule_start + 1 : rule_end]
    effective_rules = [line for line in rules if line and not line.startswith("#")]

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

    require(CHINA_RULE_SET in rules, "missing ChinaMaxNoIP DIRECT rule set")
    require(MANAGED_START in rules, "missing managed upstream marker")
    china_index = rules.index(CHINA_RULE_SET)
    managed_index = rules.index(MANAGED_START)
    local_proxy_indices = [
        index
        for index, rule in enumerate(rules[:managed_index])
        if ",PROXY" in rule and not rule.startswith("#")
    ]
    require(local_proxy_indices, "missing local explicit PROXY rules")
    require(
        max(local_proxy_indices) < china_index,
        "China mainland DIRECT rule set must follow all local explicit PROXY rules",
    )
    require(
        china_index < managed_index,
        "China mainland DIRECT rule set must precede the upstream PROXY snapshot",
    )
    for rule in (
        "DOMAIN-SUFFIX,cn,DIRECT",
        "DOMAIN-SUFFIX,xn--fiqs8s,DIRECT",
        "DOMAIN-SUFFIX,xn--fiqz9s,DIRECT",
        "GEOIP,CN,DIRECT",
    ):
        require(rule in rules, f"missing China DIRECT fallback: {rule}")
        require(rules.index(rule) < rules.index(FINAL_RULE), f"China DIRECT fallback must precede FINAL: {rule}")

    require(effective_rules[-1] == FINAL_RULE, "FINAL,PROXY must be the last rule")

    print("Shadowrocket config checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
