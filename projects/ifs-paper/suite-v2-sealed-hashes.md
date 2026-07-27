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
