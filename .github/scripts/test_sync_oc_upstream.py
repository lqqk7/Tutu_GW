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

    def test_airport_filter_requires_all_keywords_in_any_order(self):
        pattern = re.compile(SYNC.AIRPORT_NODE_FILTER)

        for name in (
            "美国-专线-AI",
            "美国-AI-专线",
            "专线-美国-AI",
            "专线-AI-美国",
            "AI-美国-专线",
            "AI-专线-美国",
        ):
            self.assertIsNotNone(pattern.fullmatch(name), name)

        for name in (
            "美国-专线",
            "美国-AI",
            "专线-AI",
            "新加坡-专线-AI",
            "US-AIGC-9929v3-TUTUGW",
            "US-AIGC-9929v4-TUTUGW",
            "US-General-4837v2-TUTUGW",
        ):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_compatibility_filters_do_not_use_lookaround(self):
        for node_filter in (
            SYNC.AIRPORT_NODE_FILTER,
            SYNC.INCLUDE_REMARKS_FILTER,
            SYNC.EXCLUDE_REMARKS_FILTER,
        ):
            self.assertNotIn("(?=", node_filter)
            self.assertNotIn("(?!", node_filter)

    def test_excludes_cf_acceleration_and_hy2_nodes(self):
        pattern = re.compile(SYNC.EXCLUDE_REMARKS_FILTER)

        for name in ("美国-专线-AI-cf加速", "美国-专线-AI-HY2"):
            self.assertIsNotNone(pattern.search(name), name)

    def test_excludes_d_us5_nodes(self):
        pattern = re.compile(SYNC.EXCLUDE_REMARKS_FILTER)

        for name in ("D美国5-专线-AI",):
            self.assertIsNotNone(pattern.search(name), name)

    def test_local_config_uses_the_shared_filter(self):
        config = (ROOT / "OC_Rules/Custom_Clash_Lite.ini").read_text()

        self.assertIn(SYNC.INCLUDE_REMARKS, config)
        self.assertIn(SYNC.EXCLUDE_REMARKS, config)
        self.assertIn(
            SYNC.MANUAL_GROUP,
            config,
        )
        self.assertIn(SYNC.SELF_HOSTED_FALLBACK_GROUP, config)
        self.assertIn(SYNC.AIRPORT_AUTO_GROUP, config)


if __name__ == "__main__":
    unittest.main()
