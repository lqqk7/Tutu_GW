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

    def test_only_relay_or_9929_nodes_are_included(self):
        pattern = re.compile(SYNC.INCLUDE_REMARKS_FILTER)

        for name in (
            "US-9929v3-TUTUGW",
            "US-9929v4-TUTUGW",
            "US-relay-TUTUGW",
            "🇺🇸 Premium-RELAY-01",
        ):
            self.assertIsNotNone(pattern.fullmatch(name), name)

        for name in ("US-4837v2-TUTUGW", "美国-专线-AI", "机场节点"):
            self.assertIsNone(pattern.fullmatch(name), name)

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
