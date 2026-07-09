#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
import urllib.request
from pathlib import Path


UPSTREAM_URL = os.environ.get(
    "UPSTREAM_SR_CNIP_URL",
    "https://raw.githubusercontent.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/release/sr_cnip.conf",
)
TARGET = Path("rules/Tutu-GW.conf")
START_MARKER = "# BEGIN UPSTREAM SR_CNIP MANAGED RULES"
END_MARKER = "# END UPSTREAM SR_CNIP MANAGED RULES"
INSERT_ANCHOR = "# China direct, everything else proxy"
RULE_PREFIXES = ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6", "GEOIP", "FINAL")


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Tutu-GW-sync"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def strip_inline_comment(line: str) -> str:
    return re.split(r"\s+#", line, maxsplit=1)[0].strip()


def normalize_rule(line: str) -> str | None:
    line = strip_inline_comment(line)
    if not line or not line.startswith(RULE_PREFIXES):
        return None

    parts = [part.strip() for part in line.split(",")]
    rule_type = parts[0]

    if rule_type in {"FINAL", "GEOIP"}:
        return None

    if rule_type not in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6"}:
        return None

    if len(parts) < 3:
        return None

    if parts[-1].lower() == "no-resolve":
        policy_index = -2
    else:
        policy_index = -1

    policy = parts[policy_index]
    if policy.lower() == "proxy":
        parts[policy_index] = "PROXY"
    elif policy.lower() == "direct":
        parts[policy_index] = "DIRECT"
    elif policy.upper() == "REJECT":
        return None

    if rule_type in {"IP-CIDR", "IP-CIDR6"} and parts[-1].lower() != "no-resolve":
        parts.append("no-resolve")

    return ",".join(parts)


def upstream_rules(text: str) -> list[str]:
    in_rule_section = False
    rules: list[str] = []
    seen: set[str] = set()

    for raw_line in text.replace("\r\n", "\n").splitlines():
        line = raw_line.strip()
        if line == "[Rule]":
            in_rule_section = True
            continue
        if in_rule_section and line.startswith("[") and line.endswith("]"):
            break
        if not in_rule_section or not line or line.startswith("#"):
            continue

        rule = normalize_rule(line)
        if rule and rule not in seen:
            rules.append(rule)
            seen.add(rule)

    if not rules:
        raise RuntimeError("No upstream rules were extracted from sr_cnip.conf")

    return rules


def managed_rules(text: str) -> list[str]:
    rules: list[str] = []
    in_block = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == START_MARKER:
            in_block = True
            continue
        if line == END_MARKER:
            in_block = False
            continue
        if not in_block or not line or line.startswith("#"):
            continue

        rule = normalize_rule(line)
        if rule:
            rules.append(rule)

    return rules


def existing_local_rules(text: str) -> set[str]:
    rules: set[str] = set()
    in_managed_block = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == START_MARKER:
            in_managed_block = True
            continue
        if line == END_MARKER:
            in_managed_block = False
            continue
        if in_managed_block or not line or line.startswith("#"):
            continue

        rule = normalize_rule(line)
        if rule:
            rules.add(rule)

    return rules


def merged_managed_block(current_text: str, fetched_rules: list[str]) -> list[str]:
    local_rules = existing_local_rules(current_text)
    current_managed = managed_rules(current_text)
    merged: list[str] = []
    seen: set[str] = set()

    for rule in [*current_managed, *fetched_rules]:
        if rule in local_rules or rule in seen:
            continue
        merged.append(rule)
        seen.add(rule)

    return [
        START_MARKER,
        f"# Source: {UPSTREAM_URL}",
        "# Append-only upstream snapshot. Local custom rules live outside this block.",
        *merged,
        END_MARKER,
    ]


def replace_or_insert_block(current_text: str, block_lines: list[str]) -> str:
    lines = current_text.rstrip("\n").splitlines()

    try:
        start = lines.index(START_MARKER)
        end = lines.index(END_MARKER)
    except ValueError:
        start = end = -1

    if start != -1 and end != -1 and start < end:
        next_index = end + 1
        return "\n".join([*lines[:start], *block_lines, *lines[next_index:]]) + "\n"

    try:
        anchor = lines.index(INSERT_ANCHOR)
    except ValueError as error:
        raise RuntimeError(f"Insert anchor not found: {INSERT_ANCHOR}") from error

    return "\n".join([*lines[:anchor], *block_lines, "", *lines[anchor:]]) + "\n"


def main() -> int:
    current_text = TARGET.read_text(encoding="utf-8")
    fetched = upstream_rules(fetch_text(UPSTREAM_URL))
    block = merged_managed_block(current_text, fetched)
    updated_text = replace_or_insert_block(current_text, block)
    TARGET.write_text(updated_text, encoding="utf-8")

    managed_count = len([line for line in block if normalize_rule(line)])
    print(f"Synced {managed_count} managed upstream rules into {TARGET}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
