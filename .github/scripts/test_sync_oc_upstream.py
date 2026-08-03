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
    def test_self_hosted_nodes_are_exact_and_in_priority_order(self):
        self.assertEqual(
            SYNC.SELF_HOSTED_NODES,
            (
                "US-9929v3-TUTUGW",
                "US-4837v2-TUTUGW",
                "US-9929v4-TUTUGW",
            ),
        )

        pattern = re.compile(SYNC.SELF_HOSTED_NODE_FILTER)
        for name in SYNC.SELF_HOSTED_NODES:
            self.assertIsNotNone(pattern.fullmatch(name), name)
            self.assertIsNotNone(pattern.fullmatch(f"🇺🇸 {name}"), name)
            self.assertNotIn(f"[]{name}", SYNC.MANUAL_GROUP)
            self.assertNotIn(f"[]{name}", SYNC.SELF_HOSTED_FALLBACK_GROUP)

        self.assertIsNone(pattern.fullmatch("🇺🇸 US-4837v1-TUTUGW"))

        expected_rules = tuple(
            rf"(?i)^(?:🇺🇸\s*)?{name}$" for name in SYNC.SELF_HOSTED_NODES
        )
        self.assertEqual(SYNC.SELF_HOSTED_GROUP_RULES, "`".join(expected_rules))
        for group in (SYNC.MANUAL_GROUP, SYNC.SELF_HOSTED_FALLBACK_GROUP):
            positions = [group.index(rule) for rule in expected_rules]
            self.assertEqual(positions, sorted(positions), group)

    def test_only_self_hosted_nodes_are_included(self):
        pattern = re.compile(SYNC.INCLUDE_REMARKS_FILTER)

        for name in SYNC.SELF_HOSTED_NODES:
            self.assertIsNotNone(pattern.fullmatch(name), name)

        for name in ("美国-专线-AI", "D美国5-专线-AI", "机场节点"):
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
