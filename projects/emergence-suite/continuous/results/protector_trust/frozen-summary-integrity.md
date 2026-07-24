# Experiment 47 frozen-summary integrity

- Pre-addendum SHA-256: `4e9e0f923d4bc411e38a845d1b83519bad9bf07b665ae4b4cb13baf41685c7c2`.
- The exploratory result was appended as the final top-level `exploratory` member of `summary.json`.
- Reconstruction removes the line containing the member's leading comma and everything after it, then restores the original final `}` plus newline.
- Reconstructed SHA-256: `4e9e0f923d4bc411e38a845d1b83519bad9bf07b665ae4b4cb13baf41685c7c2`.
- Result: **exact byte match**. The pilot, confirmation, config, structural audit, and frozen 4/5 verdict are unchanged.

The summary was untracked rather than committed when the addendum was requested, so the preserved pre-addendum artifact from this same run is the comparison state.
