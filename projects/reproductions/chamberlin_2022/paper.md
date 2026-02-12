# Paper Reference (Chamberlin 2022)

## Citation
Chamberlin, D. E. (2022). "The Active Inference Model of Coherence Therapy." *Frontiers in Human Neuroscience*, 16, 955558.

## Links
- **Paper**: https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.955558/full
- **DOI**: 10.3389/fnhum.2022.955558

## Abstract Summary
This theoretical paper proposes integrating Coherence Therapy with active inference. The author argues that symptoms emerge from implicit models of reality (schemas), and therapeutic resolution occurs when these models become conscious through guided discovery. Crucially, Chamberlin argues this is **structure learning** (representational redescription), not just parameter updating.

## Key Contributions
1. Frames Coherence Therapy as "dyadic active inference" between therapist and client.
2. Proposes that pathological behaviors are Bayes-optimal under suboptimal prior beliefs.
3. Identifies **modularity** as the key property of implicit schemas - they are "knowledge in the system but not knowledge to the system" (p6).
4. Argues Discovery (making explicit) is often sufficient for resolution - >50% of cases resolve with Discovery alone (p3).
5. Distinguishes CT from CBT: CT involves structure learning (new representations), not gradual parameter updating.
6. Proposes that resolution involves **context embedding** - the schema becomes context-sensitive rather than context-blind.

## Core Theoretical Claims

### Bayes Optimal Pathology
- Symptoms are coherent/optimal given the agent's (flawed) generative model.
- Therapy reveals the hidden priors that make pathological behavior "make sense."
- "Behavior including pathology is always coherent" if underlying assumptions are identified.

### Implicit Schemas are Modular (Key Insight)
From p6: "it is knowledge in the system, but it is not yet knowledge to the system...the implicit knowledge is 'modular'"
- Implicit schemas operate automatically, outside conscious control
- They are **context-blind**: formed under stress with "minimal parameters e.g., no consideration of context" (p12)
- They cannot be accessed by other cognitive processes (verbal report, deliberation)
- Memory suppression keeps them isolated from representational redescription

### Coherence Therapy Process
1. **Discovery**: Surface the implicit schema, making it explicit and context-sensitive
   - This alone resolves symptoms in >50% of cases (p3)
   - Involves "representational redescription" - creating a new, higher-level representation
2. **Integration**: Incorporate explicit schema into everyday awareness
3. **Juxtaposition**: Create mismatch between schema and contradicting reality (if needed)
4. **Verification**: Confirm schema no longer generates symptoms

### Resolution Mechanism
From p14: "Rather than 'unlearning' or 'erasing' anything, she has learned a model of herself...that contains an appreciation of its former utility and current irrelevance"
- Resolution = context embedding, not erasure
- The new schema is context-sensitive: "necessary in some contexts but not others"
- Agency emerges: "I don't need to do this anymore"

### Active Inference Mapping
- Implicit schema = modular, context-blind policy
- Making explicit = breaking modularity, enabling context-sensitivity
- Discovery = therapist-guided active inference to identify the schema
- Resolution = agent recognizes current context doesn't require protective policy
- Reconsolidation (if needed) = belief updating after context-sensitive mismatch

## Relation to Other Papers
- **Smith 2021**: Also models therapy via active inference, but focuses on CBT exposure therapy with parametric learning (D matrix). Chamberlin proposes *structure learning* (model structure changes).
- **IFS**: Coherence Therapy's "parts with adaptive purposes" parallels IFS protective parts.

## Simulation Considerations
**No simulation exists in the paper.** Key challenges for implementation:
1. **Modularity**: How to represent context-blind vs. context-sensitive policy selection.
2. **Structure learning**: How to model "representational redescription" vs. parameter learning.
3. **Therapeutic dyad**: Therapist maintains high-precision belief that schema exists and can be found.
4. **Memory suppression**: How blocked access prevents representational redescription.
5. **Context embedding**: Making schema context-sensitive without necessarily updating beliefs.

### Key Simulation Prediction
If modularity-breaking is the primary mechanism, then:
- Resolution should occur when context-sensitivity is enabled
- Belief updating (D-matrix change) is NOT always necessary
- The critical variable is whether policy selection considers context
- This differs from Smith 2021 where resolution requires gradual belief change

## Implementation Files
- TBD (theoretical paper - simulation design needed)
