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

## C-V2G0-C seal (2026-07-29)
```
6ab872b9aef3e8001e26dcbefb4c62e09fe37a76e997c144d7ab454259f10777  C-V2G0C-apparatus-challenge.md
```
Escrow: C-V2G0-C seeds 2000000:2000499 — retirement of this block is REVERSED by this record (zero seeds ever consumed; apparatus criteria not gameable by plaintext knowledge; the frozen SEALED_ESCROW range admits only this block). The 2001000:2001499 release is withdrawn. Pre-seal checks now include: exact-artifact dry-run after the declared parse instruction; release-record validation through the frozen parser; escrow-containment check against SEALED_ESCROW.

## C-V25A seal (2026-07-29)
```
2aa8fec708d5446ceef83a590946791c8398a54d40539532e863ae7691a57a15  C-V25A-configural-challenge.md
```
Escrow: C-V25A seeds 2010000:2010999, released by this record through the amended released_block parameter (authorization: escrow-threading amendment + this ledger entry). EVALUATOR DISCLOSURE: one pre-seal threading check constructed (never scored) a world from escrow seed 2010000 before the correct dev-seed method was adopted; recorded here for custody completeness; the block assignment predates the event (committed seed map).

## C-V25B seal (2026-07-29)
```
e556e08eb23fe8fef14daad11735fb8066e9ce43e6558ca5520fef4710a65c36  C-V25B-reduction-challenge.md
```
Escrow: C-V25B seeds 2020000:2021999, released by this record through the frozen released_block parameter. Pre-seal: exact-artifact dry-run, arm-vocabulary validation, dev-seed threading check, containment check.

## C-V25B-B seal (2026-07-29)
```
d781130feb9c675f3e476788a0d103cd99a0e1588b70eff1de9c95fccf602c32  C-V25BB-reduction-challenge.md
```
Escrow: C-V25B-B seeds 2020000:2021999 (unconsumed by the retained C-V25B stop; release record stands). Pre-seal adds score-vocabulary validation against frozen gate3_row fields.

## C-V25B-C seal (2026-07-29)
```
f90dbb800bf98f58d9ce1b916a5d9d218faee40b7e16f773dfa6fe12ce31b17e  C-V25BC-reduction-challenge.md
```
Escrow: C-V25B-C seeds 2022000:2023999 (fresh; 2020000:2021999 consumed by the retained C-V25B-B FAIL and closed). Pre-seal adds the criterion-direction check (reduction demands only on 000 truth).

## C-V26A seal (2026-07-29)
```
cba6d516516401c05f00cc0586e57e750964f3f8128d3b541eb3352823e56621  C-V26A-partner-challenge.md
```
Escrow: C-V26A seeds 2030000:2031999, released by this record via the frozen released_block parameter. Full accumulated pre-seal linter applied.

## C-V234 seal (2026-07-29)
```
1d9329bafd15fdc5e2c987bb4fa9105146d8740f05fefdd675f1fab61764cdd7  C-V234-attribution-challenge.md
```
Escrow: C-V234 seeds 2040000:2041999, released by this record via the frozen released_block parameter. Full accumulated pre-seal linter applied.

## C-V234-B seal (2026-07-29)
```
c4f6f72e14c83c2191b9724f43094736cad1b437cc9260d941b371a51146c336  C-V234B-attribution-challenge.md
```
Escrow: C-V234-B seeds 2042000:2043999 (fresh; 2040000:2041999 consumed by the retained C-V234 FAIL and closed). Pilot blocks 1330000:1331199 BARRED (attainability pilot, 300 worlds per rate, non-criterion). Floors corrected to pilot-derived attainable values; all else verbatim.

## C-V26B seal (2026-07-29)
```
c7e00412c7f06cbead6f03152b0be4fc70da013a00fd1de0780b3cb0e62e4abf  C-V26B-protector-challenge.md
```
Escrow: C-V26B seeds 2050000:2052999, released by this record via the frozen released_block parameter. Pilot block 1332000:1332599 BARRED (permission-profile attainability pilot, non-criterion). Full accumulated linter applied.

## C-V27 seal (2026-07-29)
```
2b68bd3f39d2add80ac89ce6f54b779af1083b5e0e64dd227383391ff875593f  C-V27-multiprotector-challenge.md
```
Escrow: C-V27 seeds 2060000:2064999, released by this record. Pilot blocks 1333000:1334199 BARRED. Full accumulated linter with scenario-profile and recovery-rate pilots.

## C-V27-B seal (2026-07-29)
```
a6ba705baab940a3d830236fd17e28f6063ed003322f3281d10ca27d3aa3b60e  C-V27B-multiprotector-challenge.md
```
Escrow: C-V27-B seeds 2065000:2069599 (fresh; 2060000:2064999 consumed by the retained C-V27 FAIL and closed). Cell 4 corrected to same-seed paired arms; dev-seed identity verified pre-seal.

## C-V28A-D seals (2026-07-29)
```
d784f47ec8a0c5b2a2017198542891f519edc0a2e87b8410bdb1ccabd0bc5c5e  C-V28A-challenge.md
c59b907bc9ede68ce489a0b4cc6ad12184e25d2952420879542a214c3004d133  C-V28B-challenge.md
be1cbb5885a94af380e48b9fb3c4e83b043f63d3584f0601e44c21f8e0f60c68  C-V28C-challenge.md
dcfdf3990aa1fd1e6b41265f478825053dc14df016a5fa0f5a7348e7c915ee4f  C-V28D-challenge.md
```
Escrows: C-V28A 2100000:2100599, C-V28B 2110000:2110599, C-V28C 2120000:2120599, C-V28D 2130000:2130599 — each the declared prefix of its assigned 10000-seed block, released by this record; remainders unconsumed and closed at verdict. Floors from the committed stage-0 attainability pilot and gate-3 profiles (pilot blocks 1680000:1689999 barred). Same-seed pairing throughout. Each bundle verdicts independently; no aggregate pass count required.

## C-V28D-B seal (2026-07-29)
```
7d25943eb3d22198fb3380537a619cc5a5daa5aa9a9d759af0d7331026258c17  C-V28DB-challenge.md
```
Escrow: C-V28D-B seeds 2130600:2131199 (fresh prefix; the never-opened 2130000:2130599 prefix closed). Ordering criterion corrected to the frozen first_times vocabulary (root < reduction), validated on a dev-seed trajectory pre-seal.

## C-V30 seal (2026-07-30)
```
fdc8b516379048f7d2b1e5fde40c647de76bab02f060119339118debd4cdff73  C-V30-grammar-challenge.md
```
Escrow: C-V30 seeds 4000000:4001999 (Epoch C), released by this record via the frozen released_block parameter. Full accumulated pre-seal linter; dry-run on the exact constructor arguments sealed.
