#!/usr/bin/env python3
import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / ".github/scripts/sync-oc-upstream.py"
SPEC = importlib.util.spec_from_file_location("sync_oc_upstream", SCRIPT_PATH)
assert SPEC and SPEC.loader
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class RulesetAnchorTest(unittest.TestCase):
    def test_cdn_host_change_preserves_custom_rules(self):
        for host in ("testingcf.jsdelivr.net", "cdn.jsdelivr.net"):
            with self.subTest(host=host):
                anchor = (
                    f"ruleset=🚀 手动选择,clash-classic:https://{host}/gh/"
                    "Aethersailor/Custom_OpenClash_Rules@main/rule/"
                    "Custom_Proxy_Classical_IP.yaml,28800"
                )
                result = SYNC.insert_custom_rulesets([anchor])
                self.assertEqual(result[0], anchor)
                for rule in SYNC.CUSTOM_RULESETS:
                    self.assertEqual(result.count(rule), 1)
                with self.assertRaises(RuntimeError):
                    SYNC.insert_custom_rulesets([anchor, anchor])

    def test_cn_httpdns_direct_precedes_encrypted_dns_proxy(self):
        config = (ROOT / SYNC.TARGET).read_text().splitlines()
        direct = next(i for i, line in enumerate(config) if "CN_HTTPDNS_Classical.yaml" in line)
        encrypted = next(i for i, line in enumerate(config) if "Encrypted_DNS_Domain.yaml" in line)
        self.assertLess(direct, encrypted)
        self.assertTrue(config[direct].startswith("ruleset=🎯 全球直连,"))
        provider = (ROOT / SYNC.CN_HTTPDNS_PROVIDER).read_text()
        self.assertIn("DOMAIN-SUFFIX,dns.weixin.qq.com", provider)

    def test_missing_anchor_fails_closed(self):
        with self.assertRaises(RuntimeError):
            SYNC.insert_custom_rulesets(["[custom]"])


class NodeFilterTest(unittest.TestCase):
    def test_only_relay_and_hk_prefixes_are_included(self):
        pattern = re.compile(SYNC.INCLUDE_REMARKS_FILTER)
        for suffix in ("TUTUGW", "TUTU", "xxxx", "new-node-2"):
            for prefix in ("US-RELAY", "HK"):
                node = f"{prefix}-{suffix}"
                self.assertIsNotNone(pattern.search(node), node)
        self.assertIsNotNone(pattern.search("us-relay-example"))
        for node in ("US-9929-TUTUGW", "US-4837-TUTU", "Premium-RELAY-01",
                     "XHK-TUTU", "RELAY-TUTU", "HK-", "US-RELAY-", "机场节点"):
            self.assertIsNone(pattern.search(node), node)

    def test_hk_is_exclusive_to_polymarket(self):
        for suffix in ("TUTUGW", "TUTU", "xxxx", "new-node-2"):
            for prefix, expected in (("HK", SYNC.POLYMARKET_GROUP),
                                     ("US-RELAY", "🚀 手动选择")):
                node = f"{prefix}-{suffix}"
                matched = []
                for group in SYNC.CUSTOM_PROXY_GROUPS:
                    filters = [part for part in group.split("`")[2:]
                               if part.startswith(("(?i)", "^"))]
                    if any(re.search(pattern, node) for pattern in filters):
                        matched.append(group.split("`")[0].removeprefix("custom_proxy_group="))
                self.assertEqual(matched, [expected], node)
        self.assertNotIn(f"[]{SYNC.POLYMARKET_GROUP}", "\n".join(SYNC.CUSTOM_PROXY_GROUPS))

    def test_legacy_groups_are_removed_and_references_resolve(self):
        groups = SYNC.CUSTOM_PROXY_GROUPS
        text = "\n".join(groups)
        for legacy in ("自建优先", "9929", "🔒 RELAY", "`fallback`", "机场自动"):
            self.assertNotIn(legacy, text)
        names = {line.split("`")[0].removeprefix("custom_proxy_group=") for line in groups}
        for line in groups:
            for part in line.split("`")[2:]:
                if part.startswith("[]"):
                    self.assertIn(part[2:], names | {"DIRECT"})
        self.assertTrue(SYNC.MANUAL_GROUP.endswith("`[]🎯 全球直连"))

    def test_service_rules_precede_general_rules(self):
        anchor = "ruleset=🎯 全球直连,[]GEOIP,private,no-resolve"
        general = "ruleset=🚀 手动选择,[]GEOSITE,gfw"
        result = SYNC.insert_priority_rulesets([anchor, general])
        self.assertEqual(result, [anchor, SYNC.POLYMARKET_RULESET, SYNC.AI_RULESET, general])
        with self.assertRaises(RuntimeError):
            SYNC.insert_priority_rulesets([general])
        with self.assertRaises(RuntimeError):
            SYNC.insert_priority_rulesets([anchor, anchor])
        config = (ROOT / "OC_Rules/Custom_Clash_Lite.ini").read_text()
        rulesets = [line for line in config.splitlines() if line.startswith("ruleset=")]
        self.assertEqual(rulesets[2:4], [SYNC.POLYMARKET_RULESET, SYNC.AI_RULESET])
        self.assertIn(SYNC.POLYMARKET_PROXY_GROUP, config)

    def test_polymarket_provider_matches_source(self):
        source = [line for line in SYNC.POLYMARKET_RULES.read_text().splitlines()
                  if line and not line.startswith("#")]
        provider = [line.removeprefix("  - ") for line in SYNC.POLYMARKET_PROVIDER.read_text().splitlines()[1:]]
        self.assertEqual(provider, source)
        self.assertTrue(all(rule.startswith(("DOMAIN,", "DOMAIN-SUFFIX,")) for rule in source))
        def matches(host):
            for rule in source:
                kind, domain = rule.split(",")
                if host == domain or (kind == "DOMAIN-SUFFIX" and host.endswith("." + domain)):
                    return True
            return False
        for host in ("polymarket.com", "clob.polymarket.com", "ws-live-v2.polymarket.com",
                     "bridge.polymarket.com", "new-service.polymarket.com", "poly.market",
                     "combos-rfq-api.polymarket.sh", "polymarket-upload.s3.us-east-2.amazonaws.com"):
            self.assertTrue(matches(host), host)
        for host in ("polymarket.us", "api.polymarket.us", "notpolymarket.com",
                     "polymarket.com.example.org", "accounts.google.com", "auth.magic.link",
                     "other.s3.us-east-2.amazonaws.com", "preview.polymarket.sh"):
            self.assertFalse(matches(host), host)

    def test_local_config_uses_shared_groups(self):
        config = (ROOT / SYNC.TARGET).read_text()
        self.assertIn(SYNC.INCLUDE_REMARKS, config)
        for group in SYNC.CUSTOM_PROXY_GROUPS:
            self.assertIn(group, config)
        SYNC.validate_generated(config)


class AIProviderTest(unittest.TestCase):
    def test_provider_preserves_source_rules_and_no_resolve(self):
        source = list(dict.fromkeys(rule for line in (ROOT / SYNC.AI_RULES).read_text().splitlines()
                                   if (rule := SYNC.normalize_list_rule(line))))
        provider = (ROOT / SYNC.AI_PROVIDER).read_text().splitlines()[1:]
        self.assertEqual(provider, [f"  - {rule}" for rule in source])
        for rule in ("DOMAIN-SUFFIX,claudemcpcontent.com",
                     "DOMAIN,http-intake.logs.us5.datadoghq.com",
                     "DOMAIN-SUFFIX,withpersona.com", "DOMAIN-SUFFIX,frompersona.com",
                     "IP-CIDR,160.79.104.0/23,no-resolve",
                     "IP-CIDR,153.61.224.0/22,no-resolve",
                     "IP-CIDR6,2607:6bc0::/48,no-resolve"):
            self.assertIn(rule, source)
        self.assertFalse(any("160.79.104.0/21" in rule or "2607:6bc0::/32" in rule for rule in source))
        self.assertFalse(any(rule.startswith("DOMAIN-KEYWORD," + keyword)
                             for rule in source for keyword in ("sentry", "sift", "datadog")))

    def test_ip_options_survive_normalization(self):
        for rule in ("IP-CIDR,160.79.104.0/23,no-resolve",
                     "IP-CIDR6,2607:6bc0::/48,no-resolve"):
            self.assertEqual(SYNC.normalize_list_rule(rule + " # note"), rule)
        self.assertIsNone(SYNC.normalize_list_rule("# comment"))



class ClientConfigTest(unittest.TestCase):
    def test_client_config_differs_only_by_base(self):
        router = (ROOT / SYNC.TARGET).read_text()
        client = (ROOT / SYNC.CLIENT_TARGET).read_text()
        self.assertEqual(client, SYNC.build_client_config(router))
        self.assertIn(SYNC.CLIENT_BASE_LINE, client)
        self.assertNotIn(SYNC.BASE_LINE, client)

    def test_client_and_router_use_identical_node_filters(self):
        for path in (SYNC.TARGET, SYNC.CLIENT_TARGET):
            config = (ROOT / path).read_text().splitlines()
            include = next(line for line in config if line.startswith("include_remarks="))
            groups = [line for line in config if line.startswith("custom_proxy_group=")]
            self.assertEqual(include, SYNC.INCLUDE_REMARKS)
            self.assertEqual(groups, SYNC.CUSTOM_PROXY_GROUPS)

    def test_client_base_drops_gateway_settings(self):
        text = SYNC.CLIENT_BASE_CONFIG_TEXT
        self.assertIn("allow-lan: false", text)
        self.assertNotIn("listen: 0.0.0.0", text)
        self.assertIn("tun:\n  enable: true", text)
        self.assertIn("    - any:53", text)
        self.assertEqual((ROOT / SYNC.CLIENT_BASE_CONFIG).read_text(), text)
        router_dns = SYNC.BASE_CONFIG_TEXT.split("\ndns:\n", 1)[1]
        client_dns = text.split("\ndns:\n", 1)[1]
        self.assertEqual(client_dns, router_dns.replace("  listen: 0.0.0.0:7874\n", ""))


if __name__ == "__main__":
    unittest.main()
