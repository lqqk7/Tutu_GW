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

    def test_missing_anchor_fails_closed(self):
        with self.assertRaises(RuntimeError):
            SYNC.insert_custom_rulesets(["[custom]"])


class NodeFilterTest(unittest.TestCase):
    def test_manual_group_uses_one_combined_filter(self):
        self.assertEqual(
            SYNC.SELF_HOSTED_GROUP_FILTER,
            r"(?i).*(?:RELAY|9929).*",
        )
        self.assertEqual(SYNC.MANUAL_GROUP.count(SYNC.SELF_HOSTED_GROUP_FILTER), 1)
        self.assertNotIn("`(?i).*9929.*`", SYNC.MANUAL_GROUP)

    def test_self_hosted_fallback_has_fixed_priority(self):
        self.assertEqual(
            SYNC.SELF_HOSTED_PRIORITY,
            (SYNC.SELF_HOSTED_RELAY_GROUP, SYNC.SELF_HOSTED_9929_GROUP),
        )
        relay = SYNC.SELF_HOSTED_FALLBACK_GROUP.index(f"[]{SYNC.SELF_HOSTED_RELAY_GROUP}")
        fallback = SYNC.SELF_HOSTED_FALLBACK_GROUP.index(f"[]{SYNC.SELF_HOSTED_9929_GROUP}")
        self.assertLess(relay, fallback)
        self.assertNotIn(SYNC.SELF_HOSTED_GROUP_FILTER, SYNC.SELF_HOSTED_FALLBACK_GROUP)
        self.assertNotIn("[]US-RELAY-TUTUGW", SYNC.SELF_HOSTED_FALLBACK_GROUP)
        self.assertNotIn("[]US-9929-TUTUGW", SYNC.SELF_HOSTED_FALLBACK_GROUP)

    def test_priority_helpers_filter_provider_nodes(self):
        self.assertIn("(?i)^US-RELAY-TUTUGW$", SYNC.SELF_HOSTED_RELAY_PROVIDER_GROUP)
        self.assertIn("(?i)^US-9929-TUTUGW$", SYNC.SELF_HOSTED_9929_PROVIDER_GROUP)
        self.assertIn(SYNC.SELF_HOSTED_RELAY_PROVIDER_GROUP, SYNC.CUSTOM_PROXY_GROUPS)
        self.assertIn(SYNC.SELF_HOSTED_9929_PROVIDER_GROUP, SYNC.CUSTOM_PROXY_GROUPS)

    def test_only_existing_self_hosted_and_exact_polymarket_node_are_included(self):
        pattern = re.compile(SYNC.INCLUDE_REMARKS_FILTER)

        for name in (
            "US-9929v3-TUTUGW",
            "US-9929v4-TUTUGW",
            "US-relay-TUTUGW",
            "🇺🇸 Premium-RELAY-01",
            "HK-TUTUGW",
        ):
            self.assertIsNotNone(pattern.fullmatch(name), name)

        for name in ("US-4837v2-TUTUGW", "美国-专线-AI", "机场节点", "HK-TUTUGW-2", "XHK-TUTUGW", "HK-TUTU"):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_polymarket_node_is_isolated(self):
        nodes = ["HK-TUTUGW", "HK-TUTU", "HK-TUTUGW-2", "US-RELAY-TUTUGW", "US-9929-TUTUGW"]
        groups = SYNC.CUSTOM_PROXY_GROUPS
        for node in nodes:
            matched = []
            for group in groups:
                filters = [part for part in group.split("`")[2:] if part.startswith(("(?i)", "^"))]
                if any(re.search(pattern, node) for pattern in filters):
                    matched.append(group.split("`")[0])
            if node == "HK-TUTUGW":
                self.assertEqual(matched, [f"custom_proxy_group={SYNC.POLYMARKET_GROUP}"])
            elif node.startswith("HK-"):
                self.assertEqual(matched, [])
        self.assertNotIn(f"[]{SYNC.POLYMARKET_GROUP}", "\n".join(groups))

    def test_polymarket_precedes_general_rules(self):
        anchor = "ruleset=🎯 全球直连,[]GEOIP,private,no-resolve"
        general = "ruleset=🚀 手动选择,[]GEOSITE,gfw"
        result = SYNC.insert_polymarket_ruleset([anchor, general])
        self.assertEqual(result, [anchor, SYNC.POLYMARKET_RULESET, general])
        with self.assertRaises(RuntimeError):
            SYNC.insert_polymarket_ruleset([general])
        with self.assertRaises(RuntimeError):
            SYNC.insert_polymarket_ruleset([anchor, anchor])
        config = (ROOT / "OC_Rules/Custom_Clash_Lite.ini").read_text()
        rulesets = [line for line in config.splitlines() if line.startswith("ruleset=")]
        self.assertEqual(rulesets[2], SYNC.POLYMARKET_RULESET)
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

    def test_airport_configuration_is_removed(self):
        self.assertFalse(hasattr(SYNC, "AIRPORT_NODE_FILTER"))
        self.assertFalse(hasattr(SYNC, "AIRPORT_AUTO_GROUP"))
        self.assertNotIn("机场自动", SYNC.MANUAL_GROUP)
        self.assertNotIn("机场自动", SYNC.SELF_HOSTED_FALLBACK_GROUP)

    def test_self_hosted_group_uses_gstatic_health_check(self):
        self.assertEqual(
            SYNC.HEALTH_CHECK_URL,
            "https://www.gstatic.com/generate_204",
        )
        self.assertIn(SYNC.HEALTH_CHECK_URL, SYNC.SELF_HOSTED_FALLBACK_GROUP)
        self.assertNotIn("cp.cloudflare.com", SYNC.SELF_HOSTED_FALLBACK_GROUP)

    def test_local_config_uses_the_shared_filter(self):
        config = (ROOT / "OC_Rules/Custom_Clash_Lite.ini").read_text()

        self.assertIn(SYNC.INCLUDE_REMARKS, config)
        self.assertIn(
            SYNC.MANUAL_GROUP,
            config,
        )
        self.assertIn(SYNC.SELF_HOSTED_FALLBACK_GROUP, config)
        self.assertNotIn("机场自动", config)


if __name__ == "__main__":
    unittest.main()
