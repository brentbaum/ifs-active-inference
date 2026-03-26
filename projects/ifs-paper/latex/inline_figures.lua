local figure_map = {
  ["8.1 Blending"] = {
    {
      file = "fig5_capture_index.png",
      caption = "Capture index as a function of effective part-bundle precision and present-context evidence precision. High Self-energy lowers capture by reducing effective part dominance while amplifying context weighting.",
      label = "fig:capture-index",
    },
  },
  ["12.5 Conditions"] = {
    {
      file = "fig4_control_conditions.png",
      caption = "Control conditions for the main simulation. The critical comparison holds task structure constant while varying the inferential regime through Self-energy.",
      label = "fig:control-conditions",
    },
  },
  ["12.6 H1 vs. H2"] = {
    {
      file = "fig1_h1_belief_trajectories.png",
      caption = "Belief trajectories under H1 (self-state-upstream). Witnessing is predicted to revise self-state before threat meaning and protective policy.",
      label = "fig:h1-belief-trajectories",
    },
    {
      file = "fig1_h2_belief_trajectories.png",
      caption = "Belief trajectories under H2 (threat-primary). Revision begins at threat meaning, with weaker temporal separation from self-state change.",
      label = "fig:h2-belief-trajectories",
    },
  },
  ["13.2 Order of Revision Under H1"] = {
    {
      file = "fig6_revision_order.png",
      caption = "Expected order of revision under H1: self-state shifts first, threat meaning follows, and policy relaxation lags both.",
      label = "fig:revision-order",
    },
  },
  ["13.3 Exposure Comparison"] = {
    {
      file = "fig2_witnessing_vs_exposure.png",
      caption = "Witnessing versus exposure under matched activation. The model predicts broader and deeper change when context remains online under elevated Self-energy.",
      label = "fig:witnessing-vs-exposure",
    },
  },
  ["13.8 Model Comparison"] = {
    {
      file = "fig3_h1_vs_h2_witnessing.png",
      caption = "Model comparison for witnessing trajectories under H1 and H2. The self-state-upstream account predicts earlier self-state change and stronger generalization.",
      label = "fig:h1-vs-h2",
    },
  },
  ["14.1 What the Model Explains"] = {
    {
      file = "fig7_main_summary.png",
      caption = "Summary schematic of the paper's account: formation under threat plus low control, persistence through functional isolation, and revision through witnessing.",
      label = "fig:main-summary",
    },
  },
  ["A.3 Acquisition Phase"] = {
    {
      file = "formation_acquisition_trajectories.png",
      caption = "Formation simulation acquisition trajectories across repeated episodes.",
      label = "fig:formation-acquisition",
    },
  },
  ["A.4 Controllability Gradient"] = {
    {
      file = "formation_controllability_gradient.png",
      caption = "Controllability gradient in the formation simulation. Low control under threat produces stronger part-like bundle acquisition than threat alone.",
      label = "fig:formation-controllability",
    },
  },
  ["A.5 Main Prediction"] = {
    {
      file = "formation_bundle_rigidity.png",
      caption = "Bundle rigidity as a function of helplessness during formation. More severe low-control conditions produce more treatment-resistant priors.",
      label = "fig:formation-rigidity",
    },
  },
  ["A.6 Readout"] = {
    {
      file = "formation_readout_comparison.png",
      caption = "Post-acquisition readout in a safe ambiguous context. Formed bundles over-infer helplessness, danger, and avoidance despite safety.",
      label = "fig:formation-readout",
    },
  },
  ["B.3 Dynamics"] = {
    {
      file = "polarization_timeseries.png",
      caption = "Polarization dynamics under mutual threat modeling. Low Self-energy yields anti-phase switching between competing parts.",
      label = "fig:polarization-timeseries",
    },
  },
  ["B.4 Predicted Phenomenology"] = {
    {
      file = "polarization_phase.png",
      caption = "Phase portrait of competing part activations under lower and higher Self-energy.",
      label = "fig:polarization-phase",
    },
  },
  ["B.5 Dependent Measures"] = {
    {
      file = "polarization_policy.png",
      caption = "Policy selection across polarization dynamics as Self-energy changes.",
      label = "fig:polarization-policy",
    },
    {
      file = "polarization_summary.png",
      caption = "Summary measures for oscillation, switching, entropy, and simultaneous representation in the polarization simulation.",
      label = "fig:polarization-summary",
    },
    {
      file = "polarization_combined.png",
      caption = "Combined polarization results, integrating dynamic and summary views of de-polarization under higher Self-energy.",
      label = "fig:polarization-combined",
    },
  },
}

local function html_escape(text)
  local escaped = text:gsub("&", "&amp;")
  escaped = escaped:gsub("<", "&lt;")
  escaped = escaped:gsub(">", "&gt;")
  escaped = escaped:gsub('"', "&quot;")
  return escaped
end

local function latex_figure(spec)
  return table.concat({
    "\\begin{figure}[htbp]",
    "\\centering",
    "\\includegraphics[width=0.96\\linewidth]{" .. spec.file .. "}",
    "\\caption{" .. spec.caption .. "}",
    "\\label{" .. spec.label .. "}",
    "\\end{figure}",
  }, "\n")
end

local function html_figure(spec)
  return table.concat({
    "<figure style=\"margin: 2rem 0;\">",
    "<img src=\"figures/" .. html_escape(spec.file) .. "\" alt=\"" .. html_escape(spec.caption) .. "\" style=\"max-width: 100%; height: auto; display: block; margin: 0 auto;\" />",
    "<figcaption style=\"margin-top: 0.75rem; font-size: 0.95rem; line-height: 1.4; text-align: left;\">"
      .. html_escape(spec.caption) .. "</figcaption>",
    "</figure>",
  }, "\n")
end

function Header(el)
  local title = pandoc.utils.stringify(el.content)
  local figures = figure_map[title]
  if not figures then
    return el
  end

  local blocks = { el }
  for _, spec in ipairs(figures) do
    if FORMAT:match("latex") then
      table.insert(blocks, pandoc.RawBlock("latex", latex_figure(spec)))
    elseif FORMAT:match("html") then
      table.insert(blocks, pandoc.RawBlock("html", html_figure(spec)))
    end
  end
  return blocks
end

function HorizontalRule(_)
  return {}
end
