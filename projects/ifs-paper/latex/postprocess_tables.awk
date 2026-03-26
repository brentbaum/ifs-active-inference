BEGIN {
  table1 = "\\begin{table}[htbp]\n" \
           "\\centering\n" \
           "\\small\n" \
           "\\begin{tabular}{|p{0.22\\linewidth}|p{0.68\\linewidth}|}\n" \
           "\\hline\n" \
           "\\textbf{Phenomenon} & \\textbf{How it falls out} \\\\\n" \
           "\\hline\n" \
           "Parts & Learned local control models bundling self-state, world-state, policy, and expected outcome; formed under overwhelm and stabilized by high prior precision \\\\\n" \
           "\\hline\n" \
           "Blending & The part captures inference, present context goes functionally offline, and its beliefs feel like \\emph{me} \\\\\n" \
           "\\hline\n" \
           "Witnessing & The same part stays active while present evidence stays online too; its beliefs feel like something I am with \\\\\n" \
           "\\hline\n" \
           "Self-energy & The variable that determines which relation holds; theoretically composite of autonomic-social safety and metacognitive depth, modeled in v1 by a scalar proxy \\\\\n" \
           "\\hline\n" \
           "Outdated beliefs & Priors that were adaptive under earlier conditions but are anachronistic now; capture prevents the system from fully registering the mismatch \\\\\n" \
           "\\hline\n" \
           "Age regression & The active bundle carries a developmental self-state -- ``I am six'' is modeled as a live prior, not reduced to metaphor \\\\\n" \
           "\\hline\n" \
           "8 C's of Self & The phenomenological signature of sufficiently uncaptured inference under high Self-energy, not yet a fully derived theorem and not evidence for a separate inner homunculus \\\\\n" \
           "\\hline\n" \
           "Protectors & Policy priors and access-control tendencies that prevent destabilizing exile takeover; in practice they also have trust conditions for stepping back, though v1 formalizes only the minimal gatekeeping function \\\\\n" \
           "\\hline\n" \
           "Polarization & Two or more part-bundles competing for takeover, each treating the other's preferred policy as dangerous \\\\\n" \
           "\\hline\n" \
           "Exposure vs IFS & Exposure: corrective evidence under activation with limited Self-energy support. Witnessing: corrective evidence under activation while context remains online \\\\\n" \
           "\\hline\n" \
           "Unburdening & Durable revision of the part's upstream priors, made possible because context was maintained during activation \\\\\n" \
           "\\hline\n" \
           "Dissociation vs Self-led calm & Both may look quiet. Dissociation = present evidence functionally turned down. Self-ledness = present evidence strongly online with no part dominating \\\\\n" \
           "\\hline\n" \
           "Why change generalizes & Witnessing revises ``who I am here'' before ``what is dangerous,'' allowing upstream change to cascade downstream when H1 holds \\\\\n" \
           "\\hline\n" \
           "\\end{tabular}\n" \
           "\\end{table}"

  table2 = "\\begin{table}[htbp]\n" \
           "\\centering\n" \
           "\\small\n" \
           "\\begin{tabular}{|p{0.28\\linewidth}|p{0.28\\linewidth}|p{0.28\\linewidth}|}\n" \
           "\\hline\n" \
           " & \\textbf{Low Self-energy ($E_t$)} & \\textbf{High Self-energy ($E_t$)} \\\\\n" \
           "\\hline\n" \
           "\\textbf{Low part activation} & Baseline / ordinary cognition & Presence / Self \\\\\n" \
           "\\hline\n" \
           "\\textbf{High part activation} & Blending & Witnessing (therapeutic zone) \\\\\n" \
           "\\hline\n" \
           "\\end{tabular}\n" \
           "\\end{table}"
}

function flush_block(    rendered) {
  if (index(block, "Phenomenon") > 0 && index(block, "How it falls out") > 0) {
    print table1
  } else if (index(block, "Low Self-energy") > 0 && index(block, "High Self-energy") > 0) {
    print table2
  } else {
    printf "%s", block
  }
  block = ""
  capture = 0
}

/^\{\\def\\LTcaptype\{none\}/ {
  capture = 1
  block = $0 ORS
  next
}

capture {
  block = block $0 ORS
  if ($0 == "}") {
    flush_block()
  }
  next
}

{
  print
}
