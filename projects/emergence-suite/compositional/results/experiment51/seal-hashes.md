# Experiment 51 pre-implementation seal

**Seal status:** complete; private plaintext withheld  
**Contract:** `ifs-ai-experiment-51-contract@1.0.1`  
**Contract commit:** `47ac7688d051b569f1d50f1ea14fff5cfdb8408c`  
**Public-contract manifest SHA-256:** `d0d4b3b5f01c500ae991f6b48f4a0cb661b408eb435b99f6e875bb44b4ddbb90`  
**Public-contract manifest bytes:** `3980`  
**Archive convention:** `ustar-51-v1`  
**RNG convention:** `rng-51-v1`  
**Contract review:** Fable `APPROVED`

The four challenge archives and exact seed escrow were authored only after the
contract commit above. Each plaintext bundle passed the authoritative contract
validator and each canonical archive passed independent Python reconstruction.
The encrypted custody objects were then decrypted to a temporary directory and
compared byte-for-byte with the originals before plaintext custody was closed.

## Prospective challenge commitments

| Challenge | Canonical archive SHA-256 | Archive bytes | Encrypted custody SHA-256 | Encrypted bytes |
|---|---|---:|---|---:|
| `51-P-01` | `089802e45bfc50ba8299462f6fec611f6c292bba6f9f156355ef8ea4a27027f1` | 27136 | `a08af52946b5597a1658d308ca5580503f9c288f65d9f8f90a7eb2ceacacf049` | 4609 |
| `51-P-02` | `ee02f01eb3872d2d3e9af2738d69d8456d4688e1d1ede5bcfe6a0ef2feff522c` | 25600 | `baeb070dad3374bf539747a4ad8172ae02e3e64ed48964d8f40ae277a2a3f9ea` | 4399 |
| `51-P-03` | `eb186e61b29df87f60c0af572470462908b65aa0c42804636379231dad1f5f68` | 26624 | `d824bc19d36b8ab2213bf4f37aace4627fa8121dfd7b31e93bb62fcf4d9270cc` | 4609 |
| `51-P-04` | `c8f017e68f5cf133e8b23f27134dfce90e27c2c708751480f5e1b25a4071013a` | 26624 | `0162b81b98a1da8a449a81486fe529f675022c4155d34569c8824fc12252f081` | 4446 |

Across the sealed set, the public §12 requirements are represented: a novel
topology with at least three protectors, cross-timescale composition, an
ambiguous or switching world, and a selective negative control. The exact
mapping, protocols, thresholds, and interpretations remain private until
Stage D.

## Seed-escrow commitment

**Exact escrow SHA-256:** `d56d4f4090fdf87d6833fd022ff3eaf2c1c6d0068a65ef425b3c778480189b89`  
**Exact escrow bytes:** `1374`  
**Encrypted custody SHA-256:** `fde29c41aef75badf24249ab286f66f916f33e109a734db2cfd47164d7bd828d`  
**Encrypted custody bytes:** `642`

| Block ID | Class | Count | Release order | Commitment |
|---|---|---:|---:|---|
| `block-ember` | H | 512 | 1 | `a71cc95a31df1c14685bd4155e842ac83aa8e256a9725f17ce160625a0e355c8` |
| `block-flint` | H | 512 | 2 | `ee54316dde6999b63ee22e4a5fec26d4b4f9b55b284602a871684ee14c7350b7` |
| `block-garnet` | H | 512 | 3 | `3a5868b1dddb1aa3c12f1c22d11fde47df188bd7f52f1f6c31109e59e021bce7` |
| `block-harbor` | C | 320 | 4 | `d41b84e56411a29965e028665c0ebb75d4cb7b3b08bbd793c8e3b806703e0901` |
| `block-iris` | P | 384 | 5 | `ad03cbc5d0a4c66179b5bdd98bc2371e0971e57bd17c41d6a721ebf77a5b2e74` |
| `block-juniper` | L | 512 | 6 | `34005acd04ef7f2fe456d12747e9d4b966e10321bd42b8257f4ca20e3ed19b6c` |

The escrow contains 2,752 expanded seeds. Validation expanded every block and
found no collision. Block purposes and all master/expanded seeds remain
private. The custody objects are AES-256 encrypted outside the repository; the
recovery secret is held in the user's macOS Keychain entry
`ifs-active-inference-exp51-47ac768`.

## Stage boundary

The repository contains no challenge plaintext, private threshold, block
purpose, master seed, or expanded seed. Stage A may use only public dummy,
development, and pilot material. Challenge archives may be decrypted only at
Stage D after the reference-strain freeze; H/C/P/L blocks may be released only
in their declared stage order.
