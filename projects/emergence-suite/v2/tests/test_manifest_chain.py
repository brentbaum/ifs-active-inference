import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ref.manifest_chain import verify_manifest_chain


class ManifestChainTests(unittest.TestCase):
    def test_ordered_addendum_overlays_base_and_records_custody(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("base-a", encoding="utf-8")
            (root / "b.txt").write_text("repaired-b", encoding="utf-8")
            (root / "c.txt").write_text("added-c", encoding="utf-8")

            def digest(name):
                return hashlib.sha256((root / name).read_bytes()).hexdigest()

            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "files": {
                            "a.txt": digest("a.txt"),
                            "b.txt": hashlib.sha256(b"old-b").hexdigest(),
                        }
                    }
                ),
                encoding="utf-8",
            )
            (root / "manifest-addendum.json").write_text(
                json.dumps(
                    {
                        "addendum_to": "manifest.json",
                        "files": {
                            "b.txt": digest("b.txt"),
                            "c.txt": digest("c.txt"),
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = verify_manifest_chain(
                root,
                "manifest.json",
                ("manifest-addendum.json",),
            )

        self.assertTrue(result["passed"])
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["base_manifest_file_count"], 2)
        self.assertEqual(result["effective_manifest_file_count"], 3)
        self.assertEqual(result["overlaid_entries"], ["b.txt", "c.txt"])
        self.assertEqual(
            [item["file"] for item in result["custody_files"]["addenda"]],
            ["manifest-addendum.json"],
        )


if __name__ == "__main__":
    unittest.main()
