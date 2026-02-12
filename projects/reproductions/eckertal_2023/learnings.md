# Learnings (Eckertal 2023 / Trust Game Reproduction)

## 1) Plot qs (posterior), not pD (prior)
- Initial implementation plotted normalized pD (Dirichlet prior).
- pD accumulates slowly over trials - not responsive to observations.
- Paper's Figure 2 shows belief swings from ~0.05 to ~0.95 within trials.
- This is the POSTERIOR qs after observing the outcome, not the prior.
- **Fix**: Record and plot agent.qs[T][1] (posterior over context at end of trial).

## 2) Keep/Start observations must be UNKNOWN
- Critical for epistemic motivation to share.
- If keep gives information about context, agent has no reason to take risk.
- pymdp sets behavior modality to UNKNOWN for keep/start.
- Only sharing provides information (social/antisocial behavior observed).
- This creates the exploration-exploitation tradeoff central to the task.

## 3) Environment context is FIXED, agent model is DYNAMIC
- Environment holds context constant (identity B matrix).
- Agent's generative model may believe context can change.
- Different profiles have different B transition beliefs.
- This asymmetry is intentional - agent must infer static hidden state.

## 4) Softmax on preferences creates relative utilities
- pymdp stores raw utilities in C: [reward_sensitivity, loss_aversion, neutral].
- EFE converts to log(softmax(C)) for expected utility.
- This makes preferences relative, not absolute.
- Our implementation matches this via raw C values.

## 5) Observation sampling uses separate env_share_probs
- Environment doesn't use agent's A matrix for sampling.
- Uses env_share_probs = (0.8, 0.2, 0.5) for (friendly, hostile, neutral).
- This allows environment to have different behavior from agent's beliefs.

## 6) Deterministic action selection matches paper
- Paper uses action_selection='deterministic' (argmax).
- Stochastic selection adds noise that obscures belief dynamics.
- Our `deterministic_actions=true` parameter matches this.

## 7) Learning rates matter for dynamics
- eta_A = 0.1 (slow observation learning).
- eta_B = 3.0 (fast transition learning).
- eta_D = 1.0 (moderate prior learning).
- Higher eta_D makes beliefs more responsive but less stable.

## 8) Profile-specific B matrices are key for clinical differences
- Depressed B: friendly becomes hostile (pessimistic transitions).
- Insecure B: high transition to neutral (uncertainty).
- Defeated B: friendly becomes hostile, but less extreme than depressed.
- These capture different cognitive biases about relationship dynamics.

## 9) Fatalism = update_B = false
- Depressed agents don't update their B matrix (fatalistic belief).
- They believe their actions don't change the context.
- This creates learned helplessness dynamics.

## 10) Context switch timing matters for figures
- Paper uses 20 trials friendly, 20 trials hostile (or vice versa).
- Switch at trial 20 (+1 for 1-based indexing).
- Phase boundaries recorded for visualization shading.

## 11) Practical lessons for the library
- Recording both qs (posterior) and pD (prior) allows flexible analysis.
- Profile-based parameter organization (AgentProfile struct) is clean.
- Environment/agent asymmetry is a feature, not a bug.
- Visualization functions should show phase boundaries clearly.
