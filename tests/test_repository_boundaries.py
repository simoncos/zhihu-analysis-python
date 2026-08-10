import subprocess
import unittest
from pathlib import Path


class RepositoryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_private_runtime_paths_are_ignored(self):
        paths = [
            "crawler/config.ini",
            "crawler/cookies",
            "crawler/verify.png",
            "zhihu.db",
            "data/user_Process-2",
            "csv/private.csv",
            "candidate.parquet",
            "raw.zip",
        ]
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--stdin"],
            cwd=self.root,
            input="\n".join(paths) + "\n",
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(set(result.stdout.splitlines()), set(paths))

    def test_only_blank_configuration_example_is_versioned(self):
        self.assertFalse((self.root / "crawler" / "config.ini").exists())
        example = (self.root / "crawler" / "config.example.ini").read_text(
            encoding="utf-8"
        )
        self.assertIn("email =\n", example)
        self.assertIn("password =\n", example)

    def test_readme_has_no_legacy_raw_download_link(self):
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("pan.baidu.com", readme)
        self.assertIn("本分支不再提供原始数据下载入口", readme)


if __name__ == "__main__":
    unittest.main()
