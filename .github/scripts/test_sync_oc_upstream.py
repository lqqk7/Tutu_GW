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


class UsNodeFilterTest(unittest.TestCase):
    def test_only_keeps_requested_us_nodes(self):
        pattern = re.compile(SYNC.US_NODE_FILTER)

        for name in (
            "美国-家宽-专线",
            "US-AIGC-9929v3-TUTUGW",
            "US-AIGC-9929v4-TUTUGW",
            "US-General-4837v2-TUTUGW",
        ):
            self.assertIsNotNone(pattern.fullmatch(name), name)

        for name in ("美国-家宽-小白", "US-AIGC-9929v3-小白", "US-General-4837v1"):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_excludes_cf_acceleration_and_hy2_nodes(self):
        pattern = re.compile(SYNC.US_NODE_FILTER)

        for name in ("美国-家宽-cf加速", "US-AIGC-9929v3-HY2"):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_excludes_d_us5_nodes(self):
        pattern = re.compile(SYNC.US_NODE_FILTER)

        for name in ("D美国5-家宽", "D美国5-9929v3"):
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_local_config_uses_the_shared_filter(self):
        config = (ROOT / "OC_Rules/Custom_Clash_Lite.ini").read_text()

        self.assertIn(SYNC.INCLUDE_REMARKS, config)
        self.assertIn(
            f"custom_proxy_group=🚀 手动选择`select`[]♻️ 自动选择`[]🎯 全球直连`{SYNC.US_NODE_FILTER}",
            config,
        )
        self.assertIn(f"custom_proxy_group=🇺🇸 美国节点`select`{SYNC.US_NODE_FILTER}", config)
        self.assertIn(
            f"custom_proxy_group=♻️ 自动选择`url-test`{SYNC.US_NODE_FILTER}`https://cp.cloudflare.com/generate_204`300,,50",
            config,
        )


if __name__ == "__main__":
    unittest.main()
