# Sandved-Smith et al. 2021 Reproduction

This is a bounded standalone Python reproduction of:

Sandved-Smith, L., Hesp, C., Mattout, J., Friston, K., Lutz, A., & Ramstead, M. J. D. (2021). "Towards a computational phenomenology of mental action: modelling meta-awareness and attentional control with deep parametric active inference." *Neuroscience of Consciousness*, 2021(1), niab018. https://doi.org/10.1093/nc/niab018

I found the open OSF preprint metadata and primary PDF, but not an official public code repository or supplementary code/data link. The OSF preprint API reports `has_data_links: no`. This implementation is therefore a direct compact reimplementation from the paper's described architecture and figure captions, not a port of official code.

## Run

From this directory:

```bash
uv run python reproduce.py
```

Without uv:

```bash
python3 reproduce.py
```

Outputs are written to `outputs/`:

- `paper_figure_6_precision_oddball.png`
- `paper_figure_8_attention_capture_return.png`
- `paper_figure_10_meta_awareness_dwell.png`
- `stability_envelope.csv`
- `summary.json`

## Model Scope

The reproduction keeps the paper's three-level structure:

- Level 1: perceptual states in an oddball task, inferred through a likelihood mapping whose precision is controlled by level 2.
- Level 2: attentional states, Focused versus Distracted, inferred from metacognitive observations and controlled by mental policies.
- Level 3: meta-awareness states, High versus Low, setting the precision of the level-2 likelihood mapping.

Mental action is implemented as policy selection over the level-2 transition model: `maintain` versus `refocus`. Policy scores use expected future preference violation plus an action cost over a configurable planning horizon.

This is qualitative, not parameter-identical: the published paper does not provide enough numeric implementation detail in the text to claim an exact replication.
