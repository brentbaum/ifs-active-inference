A direct, faithful translation to Julia breaks into two separable pieces:
	1.	Port the model specification (your D/d, A/a, B, C, E, V, hyperparameters).
	2.	Replace SPM’s solver/plotting (spm_MDP_check, spm_MDP_VB_X, spm_MDP_VB_trial, spm_softmax) with either:

	•	(Recommended) a Julia active-inference implementation (closest “native Julia” path), or
	•	(Exact-replication) a line-by-line port of SPM’s discrete MDP VB algorithm (more work, but matches paper code behavior most closely).

Best target in Julia (so you don’t have to reimplement SPM)

ActiveInference.jl is specifically for discrete active inference / POMDP-style generative models in Julia, using the same “vector of arrays” representation for A and B that your MATLAB code uses (cell arrays of tensors).  ￼
It supports simulation workflows (and discusses fitting/parameter recovery in companion publications), which is the same broad problem class as the SPM MDP routines.  ￼

SPM.jl exists, but it targets neuroimaging workflows and is not a drop-in replacement for spm_MDP_* routines.  ￼

Data-structure mapping (MATLAB → Julia)
	•	D{f} (cell of column vectors) → D::Vector{Vector{Float64}}
	•	A{g} (cell of tensors No(g) × Ns(1) × Ns(2) × Ns(3)) → A::Vector{Array{Float64}} where size(A[g]) == (No[g], Ns...)
	•	B{f} (state transitions; for controllable factors it’s Ns(f) × Ns(f) × Nu(f)) → B::Vector{Array{Float64,3}} (use Nu(f)=1 for uncontrollable factors)
	•	C{g} (No(g) × T) → C::Vector{Matrix{Float64}}
	•	V ((T-1) × Np × Nf) → V::Array{Int,3} (policies are easiest as integer action indices)
	•	a and d are Dirichlet concentration parameters (learning priors) rather than normalized probabilities—keep them as positive counts, exactly like MATLAB. (Background on Dirichlet learning in this modeling style:  ￼)

Julia is 1-indexed like MATLAB, so the biggest “gotcha” is tensor shape consistency, not indexing.

Julia skeleton: model construction (your code up through mdp)

This is a literal translation of the model-building part (not the solver). It should match MATLAB tensor shapes and assignments.

using LinearAlgebra, Random

# --- Simulation settings ---
CABi   = 0.9
Psafe  = 0.1
Exposure = 0
N = 200

# --- Initial state priors D (categorical) ---
D = Vector{Vector{Float64}}(undef, 3)
D[1] = [1, 0, 0, 0, 0, 0]                 # start/stim/approach/interact/avoid/safety+cost
D[2] = [0, 1]                             # no spider / spider
D[3] = [0, 1]                             # dangerous / safe

Ns = length.(D)                           # [6,2,2]
No = [2, 2, 3, 6]                          # outcomes per modality
Ng = length(No)
Nf = length(D)

# --- Explicit beliefs d (Dirichlet counts over initial states) ---
d = deepcopy(D)
d[2] = [1, 1]
d[3] = [1 - Psafe, Psafe]

d[1] .*= 128
d[2] .*= 128
d[3] .*= 50

# --- A matrices: state->observation mappings ---
A = Vector{Array{Float64}}(undef, Ng)
for g in 1:Ng
    A[g] = zeros(No[g], Ns...)            # dims: (No[g], 6,2,2)
end

# Visual (spider) observations A[1]
A[1][:,:,1,1] .= [1 1 1 1 1 1;
                  0 0 0 0 0 0]
A[1][:,:,1,2] .= [1 1 1 1 1 1;
                  0 0 0 0 0 0]
A[1][:,:,2,1] .= [1 0 0 0 0 0;
                  0 1 1 1 1 1]
A[1][:,:,2,2] .= [1 0 0 0 0 0;
                  0 1 1 1 1 1]

# Arousal observations A[2]
A[2][:,:,1,1] .= [1 1 1 1 0 1;
                  0 0 0 0 1 0]
A[2][:,:,1,2] .= [1 1 1 1 0 1;
                  0 0 0 0 1 0]
A[2][:,:,2,1] .= [1 0 1 1 0 1;
                  0 1 0 0 1 0]
A[2][:,:,2,2] .= [1 0 1 1 0 1;
                  0 1 0 0 1 0]

# Affective consequences A[3]
A[3][:,:,1,1] .= [1 1 1 1 0 0;
                  0 0 0 0 1 1;
                  0 0 0 0 0 0]
A[3][:,:,1,2] .= [1 1 1 1 0 0;
                  0 0 0 0 1 1;
                  0 0 0 0 0 0]
A[3][:,:,2,1] .= [1 1 0 0 0 0;
                  0 0 1 0 1 1;
                  0 0 0 1 0 0]            # spider + dangerous
A[3][:,:,2,2] .= [1 1 1 1 0 0;
                  0 0 0 0 1 1;
                  0 0 0 0 0 0]            # spider + safe

# Behavioral observations A[4] = identity over factor1 states
for i in 1:2, j in 1:2
    A[4][:,:,i,j] .= Matrix{Float64}(I, 6, 6)
end

# --- Implicit beliefs a (Dirichlet counts over A parameters) ---
a = deepcopy(A)
a[1] .*= 128
a[2] .*= 128
a[4] .*= 128

a[3][:,:,2,1] .= [1 1 0.1 0.1 0   0;
                  0 0 0.9 0   1   1;
                  0 0 0   0.9 0   0]
a[3][:,:,2,2] .= [1 1 CABi   CABi   0      0;
                  0 0 (1-CABi) 0    1      1;
                  0 0 0      (1-CABi) 0    0]
a[3] .*= 5

# --- B matrices: transitions ---
controls = [2, 1, 1]                       # only factor 1 is controllable
B = Vector{Array{Float64,3}}(undef, Nf)

# factor 1: 6x6x2
B[1] = zeros(6,6,2)
B[1][:,:,1] .= [0 0 0 0 0 0;
                1 0 0 0 0 0;
                0 1 0 0 0 0;
                0 0 1 1 1 1;
                0 0 0 0 0 0;
                0 0 0 0 0 0]              # approach

B[1][:,:,2] .= [0 0 0 0 0 0;
                1 0 0 0 0 0;
                0 0 0 0 0 0;
                0 0 0 0 0 0;
                0 1 0 0 0 0;
                0 0 1 1 1 1]              # avoid

# factors 2 and 3: identity, single "null" control
B[2] = reshape(Matrix{Float64}(I, 2, 2), 2, 2, 1)
B[3] = reshape(Matrix{Float64}(I, 2, 2), 2, 2, 1)

# --- Policies V: (T-1) x Np x Nf ---
T = 4
Np = 2
V = ones(Int, T-1, Np, Nf)
V[:,1,1] .= [1,1,1]                        # approach policy picks action 1
V[:,2,1] .= [2,2,2]                        # avoid policy picks action 2

# --- Prior over policies E ---
E = [1.0, 1.0]

# --- Preferences C (No[g] x T) ---
C = [zeros(No[g], T) for g in 1:Ng]
C[2][2,:] .-= 1                             # dislike high arousal
C[3][2,:] .-= 1                             # dislike negative affect
C[3][3,:] .-= 12                            # strongly dislike serious harm

At this point, you have the same generative model objects as the MATLAB code, expressed idiomatically in Julia.

Replacing spm_* calls (what you need to decide)

Option A (recommended): run the agent with ActiveInference.jl

ActiveInference.jl’s README shows the core flow:
	•	initialize an agent with init_aif(A, B; settings=..., parameters=...)
	•	call infer_states!, infer_policies!, sample_action! each step  ￼

That matches the “single trial” workflow conceptually, but you’ll still need to map:
	•	your C, D, E, a, d, and precision parameters (alpha, beta, eta) into whatever fields/options ActiveInference.jl exposes (likely similar to pymdp, per the package’s positioning in the literature).  ￼

If you want, I can take your exact desired outputs (e.g., “match Figure X panels numerically”) and propose the minimal glue code around ActiveInference.jl to get there.

Option B (exact replication): port SPM’s solver

To match the paper’s MATLAB outputs precisely, you’d port:
	•	spm_MDP_check: dimension checks + normalization conventions
	•	spm_MDP_VB_X: the VB updates for hidden states, policies (EFE), action selection, and Dirichlet learning of a/d
	•	spm_softmax: temperatured softmax
	•	spm_MDP_VB_trial: plotting only

This is doable, but it’s a full algorithmic port, not just “syntax translation.”

Softmax replacement (Julia)

Your MATLAB uses spm_softmax(d_evo, .1) for display. In Julia:

# softmax along dim=1 (rows) with temperature τ
function softmaxτ(x::AbstractArray; τ::Real=1.0, dim::Int=1)
    xshift = x .- maximum(x; dims=dim)
    ex = exp.(xshift ./ τ)
    ex ./ sum(ex; dims=dim)
end

Exposure loop translation (conceptual)

Your MATLAB “exposure therapy” block is:
	•	set E = [1,0] (force a prior preference for approach)
	•	run N trials with learning enabled (eta)
	•	compare a{3}(:,:,2,1) before/after learning
	•	track evolution of explicit belief d{3}

In Julia you’d do the same: keep a and d as mutable Dirichlet counts, and after each trial update them using posterior sufficient statistics (Dirichlet-categorical learning). Background for that update rule in this modeling family:  ￼

Whether ActiveInference.jl already exposes the learning step as a function or you implement it yourself determines how much work this is.

Practical recommendation

If your goal is “have this CBT spider model running in Julia and produce equivalent qualitative plots,” start with Option A (ActiveInference.jl) and only fall back to Option B if you need strict numerical equivalence to SPM.

If you tell me which constraint matters more:
	•	(1) numerical match to the MATLAB/Scientific Reports figures, or
	•	(2) a clean Julia-native implementation you can modify/extend,

…I can give you the shortest path and the missing glue (how to thread C/D/E/a/d/alpha/beta/eta into the execution loop you want).
