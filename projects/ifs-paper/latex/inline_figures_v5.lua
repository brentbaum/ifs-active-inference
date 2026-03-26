local figure_map = {
  ["12.1 Main model"] = {
    {
      file = "fig4_control_conditions.png",
      caption = "Five-condition main simulation design. Exposure and witnessing share the same cue and contact structure; the manipulated difference is inferential regime via Self-energy.",
      label = "fig:control-conditions-v5",
    },
  },
  ["12.2 H1 versus H2"] = {
    {
      file = "fig1_h1_belief_trajectories.png",
      caption = "Belief trajectories under H1, where self-state is upstream of threat meaning. Witnessing produces earlier self-state revision and later policy relaxation.",
      label = "fig:h1-trajectories-v5",
    },
    {
      file = "fig1_h2_belief_trajectories.png",
      caption = "Belief trajectories under H2, where threat meaning is primary. The ordering differs from the IFS-consistent H1 account.",
      label = "fig:h2-trajectories-v5",
    },
  },
  ["13.1 Same activation, different relationship"] = {
    {
      file = "fig7_main_summary.png",
      caption = "Main summary figure for the paper's architecture and main simulation signatures. It is the clearest visual overview of formation, capture, witnessing, and revision.",
      label = "fig:main-summary-v5",
    },
  },
  ["13.2 H1 produces the predicted revision order"] = {
    {
      file = "fig6_revision_order.png",
      caption = "Revision ordering under H1. Self-state shifts first, threat meaning follows, and avoidance relaxes last.",
      label = "fig:revision-order-v5",
    },
  },
  ["13.3 H2 flips the order"] = {
    {
      file = "fig3_h1_vs_h2_witnessing.png",
      caption = "Model comparison between H1 and H2 under witnessing. H1 produces the self-state-first ordering predicted by the paper's thesis.",
      label = "fig:h1-vs-h2-v5",
    },
  },
  ["13.4 Witnessing outperforms exposure without changing the task"] = {
    {
      file = "fig2_witnessing_vs_exposure.png",
      caption = "Witnessing versus exposure under matched contact. The difference in learning follows from inferential regime rather than privileged stimulus access.",
      label = "fig:witnessing-vs-exposure-v5",
    },
  },
  ["13.7 Capture is a regime parameter in the current simulations"] = {
    {
      file = "fig5_capture_index.png",
      caption = "Capture index regime map. In the current implementation, Self-energy fixes condition-level capture rather than a trial-wise learned trajectory.",
      label = "fig:capture-index-v5",
    },
  },
  ["Appendix A. Formation Simulation"] = {
    {
      file = "formation_acquisition_trajectories.png",
      caption = "Formation acquisition trajectories across the three development conditions.",
      label = "fig:formation-acquisition-v5",
    },
    {
      file = "formation_controllability_gradient.png",
      caption = "Controllability gradient in part formation. Low control is the main driver of helpless self-state consolidation and bundle rigidity.",
      label = "fig:formation-control-v5",
    },
    {
      file = "formation_bundle_rigidity.png",
      caption = "Bundle rigidity by acquisition environment. High threat plus low control produces the strongest integrated rigidity profile.",
      label = "fig:formation-rigidity-v5",
    },
    {
      file = "formation_readout_comparison.png",
      caption = "Safe-context readout after formation. The low-control condition carries the strongest residual bundle into safety.",
      label = "fig:formation-readout-v5",
    },
  },
  ["Appendix B. Polarization Simulation"] = {
    {
      file = "polarization_timeseries.png",
      caption = "Polarization time series. Low Self-energy produces strong anti-phase alternation between the two bundles.",
      label = "fig:polarization-timeseries-v5",
    },
    {
      file = "polarization_phase.png",
      caption = "Polarization phase portrait under varying Self-energy levels.",
      label = "fig:polarization-phase-v5",
    },
    {
      file = "polarization_policy.png",
      caption = "Policy selection under polarization. The transition from takeover to coexistence proceeds through a higher-entropy exploration band.",
      label = "fig:polarization-policy-v5",
    },
    {
      file = "polarization_summary.png",
      caption = "Summary metrics for oscillation, switching, entropy, and simultaneous representation across polarization regimes.",
      label = "fig:polarization-summary-v5",
    },
    {
      file = "polarization_combined.png",
      caption = "Combined polarization figure showing the full transition from capture, to exploration, to negotiation as Self-energy rises.",
      label = "fig:polarization-combined-v5",
    },
  },
}

local function latex_figure(spec)
  return table.concat({
    "\\begin{figure}[H]",
    "\\centering",
    "\\includegraphics[width=0.92\\linewidth]{" .. spec.file .. "}",
    "\\caption{" .. spec.caption .. "}",
    "\\label{" .. spec.label .. "}",
    "\\end{figure}",
    "\\FloatBarrier",
  }, "\n")
end

local code_math_map = {
  ["π_part"] = "$\\pi_{\\mathrm{part}}$",
  ["λ_ctx"] = "$\\lambda_{\\mathrm{ctx}}$",
  ["E_t"] = "$E_t$",
  ["V_t"] = "$V_t$",
  ["M_t"] = "$M_t$",
  ["r_t"] = "$r_t$",
}

function Header(el)
  local title = pandoc.utils.stringify(el.content)
  if title == "Abstract" and FORMAT:match("latex") then
    return pandoc.RawBlock("latex", "\\section*{Abstract}")
  end
  local figures = figure_map[title]
  if not figures then
    return el
  end

  local blocks = { el }
  for _, spec in ipairs(figures) do
    if FORMAT:match("latex") then
      table.insert(blocks, pandoc.RawBlock("latex", latex_figure(spec)))
    end
  end
  return blocks
end

function Code(el)
  local replacement = code_math_map[el.text]
  if replacement and FORMAT:match("latex") then
    return pandoc.RawInline("latex", replacement)
  end
  return el
end

function HorizontalRule(_)
  return {}
end
