# Suite v2 — sealed stage-challenge hashes (first milestone)

Committed before any v2 implementation exists (2026-07-27). Plaintext held by the evaluator outside the repository. Each challenge is revealed verbatim (hash-matched) only after its stage's freeze is committed, and must run on the frozen stage with zero new code. Escrowed seeds released per stage at freeze; development seeds stay below 800000.

```
cb49f7601a51bcc1b82cce84804766646911faf76f96504654a8f78723e2c9ef  C-V20-kernel-challenge.md
94446e2ab02e89e97e9736696945619ac21928beb04ed55db6380e5dc8a311ba  C-V21-precision-challenge.md
0e998bfe9971d230bb5b133ae8999676c5389389c8cf55f2ca4ed6cec6c16c5a  C-V22-seam-challenge.md
672f9d4799855c8d60f0c50c80e913f23d56724d83c0d29f8ea2f7085609c845  seed-escrow-v2.md
```

Added after C-V22 FAIL, before V2.2.1 development (2026-07-27):

```
90fb712dfcba82c9e0456de3f40c5d27bc6504da5dcd8226537b63d596c0e88e  C-V22b-seam-challenge.md
```

Added before V2.3 development (2026-07-27):

```
c8413557dc628fabd1487cc12a1e829a31a09d5b034cb36e394b0570a4f69e89  C-V23-formation-challenge.md
```
Escrow: C-V23 seeds 807203:807502; V23-regression 808110:808409.

Added after C-V23 FAIL, before V2.3.1 development (2026-07-27):

```
db2d3111dce1ea78d51b05bf39a97571bf32d788a91e3e737cde2a74d04b79c6  C-V23b-formation-challenge.md
```
Escrow: C-V23b seeds 809301:809900.

Added after the V2.3.2 contract/plan freeze (fdbbf52), before implementation (2026-07-27):

```
5867a92ec3ee8800beedcb17d63832dd1c73f7c80d0bbde019eac00a9d5fed55  C-V23c-F-formation-challenge.md
320b45dba8bc726e4aaf6cd037350f373ffcd9250587880128dd717075cf6b80  C-V23c-M-maintenance-challenge.md
```
Escrow: C-V23c-F seeds 810401:810900; C-V23c-M seeds 811501:812100.

Disposition note (2026-07-27, per `suite-v2-c1-restructure-plan.md`): C-V23c-M is SET ASIDE UNOPENED — never revealed, never run; no maintenance challenge burns on a formation-starved model. C-V23c-F is SUPERSEDED unopened by the formation re-foundation; replaced by C-V232-F below.

Added with the C1 restructure plan, before the V2.3.2 formation contract exists (2026-07-27):

```
0d578fda4fe1097e3d3f681e1499935d0ecb797b3efabd000d94b66ba98e6a09  C-V232-F-formation-challenge.md
```
Escrow: C-V232-F seeds 813101:813700.

Added after the empirical-bound addendum, before the F2 run (2026-07-28):

```
1944f31a48576a03cd455b1327099a45c7b6a0e84e804d8e713009950691f491  C-V232-F2-continuity-challenge.md
```
Seeds: 813301:813400 (escrow remainder).

Added after the V2.3.3 phase-1 public artifacts, before implementation (2026-07-28):

```
a27310d7c6a6bc2396bc85ad93a8ace978c546ec6e3f5ecf7cdc249ac70db2b7  C-V233-M-bank-challenge.md
8b1847339374314d291ce380e44ca5a483128ef2578635a6d6b1e6a6be658edf  C-V233-M-challenge.md
```
Escrow: bank candidates 815001:815800; maintenance 816001:816900. Bank qualification gates the maintenance seeds. Pre-seal linter applied to both (records inside the sealed files).

Added after the bank2 adjudication/attestation/sampling plan, before the retry (2026-07-28):

```
4596ab4218758aa02fc425e5a6d57508125de6a4ea538fac238f0a20fa7109ff  C-V233-M-bank2-challenge.md
```
Escrow: bank2 candidates 820001:825504 (5,504). Maintenance seal and escrow unchanged. One-retry stop rule in force.

Added after the V2.4 phase-1 public artifacts, before implementation (2026-07-28):

```
574131ce32bf45a72e3163c91df0e924c84478b39c3c07691dfc216dc1b34665  C-V24-redescription-challenge.md
```
Escrow: C-V24 seeds 830001:830600.

## C-V24 escrow retirement (2026-07-29)
Block 830001:830600: RETIRED_UNCONSUMED_AFTER_CHALLENGE_REVEAL (round-8 adjudication). Zero seeds consumed by the sealed run; the plaintext is public; the block may not be reassigned. The original C-V24 prospection-failure verdict is the final V2.4 challenge result.

## C-V2G0 seal (2026-07-29)
```
c9b2d5c0dd8e1b468fccf99493e0400a43b05672c0ff1f15c3c341e7dbe3b90c  C-V2G0-apparatus-challenge.md
```
Escrow: C-V2G0 seeds 2000000:2000499 (Epoch B). Pre-seal linter record committed first at results/R0/c-v2g0-preseal-linter-record.md.

## C-V2G0-B seal (2026-07-29)
```
cbf0736763f54ac155328145a74fbe17f1401b563c4a05eaf181332634085129  C-V2G0B-apparatus-challenge.md
```
Escrow: C-V2G0-B seeds 2001000:2001499 (fresh). Block 2000000:2000499 RETIRED_UNCONSUMED after the two sealed stops (both verdicts retained). Linter amendment: dry-runs now execute on the exact sealed artifact after its declared parse instruction (ast.literal_eval round-trip verified before sealing).
