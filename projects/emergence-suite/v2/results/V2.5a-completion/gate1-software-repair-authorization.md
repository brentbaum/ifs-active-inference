# V2.5a-completion gate-1 software-repair authorization (evaluator, 2026-07-29)

Classification: pure software error (verdict-encoding class, precedents R0 gate-3 polarity and both manifest-chain verifiers). Proofs 6 and 8 used `numpy.array_equal` — an undeclared bit-identity criterion — against analytically neutral posteriors whose deviations (1.1e-16, 4.4e-16) sit five orders inside the frozen 1e-10 semantic tolerance. All nontrivial numerical obligations passed (worst 8.9e-15).

Authorized repair, narrowly: proofs 6 and 8 compare within the declared frozen tolerance 1e-10 (same comparator the other proofs use). Nothing else changes. Original FAIL record retained; repaired execution recorded separately; regression test pinning the tolerance-comparator convention for neutrality proofs; full suite green.
