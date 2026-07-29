# V2.5a-completion escrow-threading amendment (evaluator, 2026-07-29)

Classification: pre-seal apparatus amendment (same class as R0's escrow-authorization amendment). `ref/v25a_completion.py::_development_rng` pins `released_block=EPOCH_B_DEVELOPMENT_BLOCK`, so C-V25A escrow seeds (2010000:2010999) cannot generate worlds through the frozen entry points; sealing now would produce a guaranteed post-reveal stop.

Authorized, narrowly: add an optional `released_block` parameter to `generate_world` (and any sibling public generation/scoring entry points that draw seed-keyed RNG), threaded to `component_rng`, DEFAULTING to the Epoch-B development block. No default behavior changes; dev-seed outputs must be byte-identical (regression test on two dev seeds); escrow acceptance requires the caller to pass the evaluator-released block explicitly, with the release recorded in the seal ledger. Full fast suite green. Nothing else changes.
