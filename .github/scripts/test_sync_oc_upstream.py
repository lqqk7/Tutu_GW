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
    def test_self_hosted_filters_are_in_priority_order(self):
        self.assertEqual(
            SYNC.SELF_HOSTED_NODE_FILTERS,
            (
                r"(?i)^(?!.*(?:小白|cf加速|hy2|D美国5)).*9929v3.*$",
                r"(?i)^(?!.*(?:小白|cf加速|hy2|D美国5)).*4837v2.*$",
                r"(?i)^(?!.*(?:小白|cf加速|hy2|D美国5)).*9929v4.*$",
            ),
        )

    def test_airport_filter_keeps_home_broadband_and_dedicated_line_nodes(self):
        pattern = re.compile(SYNC.AIRPORT_NODE_FILTER)

        for name in (
            "美国-家宽-机场",
            "专线A1-美国7-家宽静态IP",
            "新加坡-专线",
        ):
            self.assertIsNotNone(pattern.fullmatch(name), name)

        for name in (
            "普通美国节点",
            "US-AIGC-9929v3-TUTUGW",
            "US-AIGC-9929v4-TUTUGW",
            "US-General-4837v2-TUTUGW",
        ):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_excludes_cf_acceleration_and_hy2_nodes(self):
        pattern = re.compile(SYNC.AIRPORT_NODE_FILTER)

        for name in ("美国-家宽-cf加速", "美国-专线-HY2"):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_excludes_d_us5_nodes(self):
        pattern = re.compile(SYNC.AIRPORT_NODE_FILTER)

        for name in ("D美国5-家宽", "D美国5-专线"):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_local_config_uses_the_shared_filter(self):
        config = (ROOT / "OC_Rules/Custom_Clash_Lite.ini").read_text()

        self.assertIn(SYNC.INCLUDE_REMARKS, config)
        self.assertIn(
            SYNC.MANUAL_GROUP,
            config,
        )
        self.assertIn(SYNC.SELF_HOSTED_FALLBACK_GROUP, config)
        self.assertIn(SYNC.AIRPORT_AUTO_GROUP, config)


if __name__ == "__main__":
    unittest.main()
