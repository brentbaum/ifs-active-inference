# V2.4.2 development failures

The V2.4 and V2.4.1 stops remain recorded in their own result trees. V2.4.2 is the adjudicated repair and pilot amendment.

## Official Gate 3 stop

- assay_3_matched_complexity_heldout
- assay_7_marginal_controls
- assay_8_formed_bank_bridge

## Failure localization

- Assay 3 met the amended matching-count power gate for every family
  (`80/80`, `80/80`, `80/80`, `80/80`, `63/80` in GW/CL/CS/DR/CP
  order). The scientific held-out advantage failed for GW
  (`-0.04957 [-0.07315,-0.02762]`), CL
  (`-0.02051 [-0.04482,0.00182]`), and DR
  (`0.00192 [-0.02684,0.03158]`). This is no longer a matching-yield
  failure.
- Assay 7 selected CS in `0.6333` of repaired product-null worlds and
  `0.4167` of repaired single-regime worlds, both above `0.10`.
  Cue-local control recovery was `0.55`, below `0.60`.
- Assay 8's genuine arm passed its selection, held-out, transfer,
  historical-retention, clone, and G-fixed requirements. Its repaired
  shuffled and single-regime controls still selected CS at `0.6000` and
  `0.4333`, above `0.10`.

No Gate-4 or Gate-5 population was opened.
