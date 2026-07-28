import json
import unittest
from pathlib import Path

from ref.rng import component_rng
from ref.v233 import canonical_state_hash, construct_bank_state


class EvaluatorSeedAuthorizationTests(unittest.TestCase):
    def test_development_guard_remains_default(self):
        with self.assertRaisesRegex(
            ValueError, "development seeds must be in"
        ):
            component_rng(800000, "still-development")
        with self.assertRaisesRegex(
            ValueError, "development seeds must be in"
        ):
            construct_bank_state(815001)

    def test_explicit_released_block_is_narrow(self):
        left = component_rng(
            815001,
            "authorized",
            released_block=(815001, 815800),
        ).random(4)
        right = component_rng(
            815001,
            "authorized",
            released_block=(815001, 815800),
        ).random(4)
        self.assertTrue((left == right).all())
        with self.assertRaisesRegex(
            ValueError, "outside the evaluator-released block"
        ):
            component_rng(
                815001,
                "wrong-block",
                released_block=(816001, 816900),
            )

    def test_open_development_state_is_byte_identical(self):
        frozen = json.loads(
            Path("results/V2.3.3/open-development-bank.json").read_text()
        )
        expected = next(
            row["state_sha256"]
            for row in frozen["ledger"]
            if row["seed"] == 760000
        )
        self.assertEqual(
            canonical_state_hash(construct_bank_state(760000)),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
