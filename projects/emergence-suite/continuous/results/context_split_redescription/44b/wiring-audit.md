# Experiment 44a root-evidence wiring audit

The 44a identity posterior was not literally arm-independent. In
`infer_root_trajectory`, each bundle-channel Gaussian likelihood ratio was
multiplied by that arm's field precision, and contact had a separate
arm-specific precision and sign. No code assigned the identity posterior to an
arm-specific target.

The effective result was nevertheless non-discriminating. Every arm received
the same strongly positive four-channel bundle for 18 sessions. Positive
likelihood ratios accumulated even under the weakest field. Across the ten
44b pilot seeds, replaying the 44a equations produced:

| Arm | Mean bundle LLR | Mean contact LLR | Mean total LLR | Mean final root |
|---|---:|---:|---:|---:|
| witnessing | 222.280 | 69.708 | 291.988 | 1.000000 |
| open-field informational | 221.674 | 60.414 | 282.087 | 1.000000 |
| regulation-only | 31.094 | 9.294 | 40.389 | 1.000000 |
| narrowed contact | 59.185 | 7.745 | 66.930 | 1.000000 |
| fixed context | 52.621 | 12.393 | 65.014 | 1.000000 |
| reversed graph (44a implementation) | 37.300 | -3.873 | 33.427 | 1.000000 |

Thus 44a's scale supplied no dynamic range. The reversed control also was not
a true graph reversal: it reversed only the contact likelihood while leaving
the dominant bundle-to-root likelihood active. Its negative contact evidence
was overwhelmed by `+37.300` mean bundle log odds.

44b repairs the instrument without assigning root values. Bundle evidence
still reaches the identity root only through Gaussian likelihood ratios
weighted by the inferred field. Contact reaches the root only when the graph
contains a contact-to-root link, and its precision is multiplied by field
breadth. The reversed graph instead gives the observations cue-local parents,
so their likelihood is identical under both identity-root values and the root
likelihood ratio cancels while observed marginals remain unchanged.

