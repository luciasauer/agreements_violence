---
name: project-agreements-violence
description: Core context for the Agreements and Violence research project — paper, data structure, estimation strategy, and active work on bargaining model
metadata:
  type: project
---

Research paper targeting an economics journal. Two parts: (1) causal effect of peace agreements on conflict fatalities via CSDID/IV; (2) bargaining model explaining why conflicts don't reach agreements (Fearon 1995 framework).

**Why:** Aim to publish in top economics journal; PIs are Laura Mayoral, Hannes Müller, Dominic Rohner, Christopher Rauh. RA: Lucia Sauer.

**How to apply:** When helping with code or analysis, keep the journal-publication standard in mind — robustness, clean identification, and theoretical grounding matter.

Key facts:
- 201 conflicts in sample; 66 treated (active, pass activity threshold); 135 never sign agreement
- Main causal result: first agreement reduces ln_deaths by ~0.69 at quarterly level (CSDID, p=0.002)
- CLAUDE.md at repo root has full structure, variable definitions, and workflow details
- Active work is on src/5_structural_model/ — H1 (logit) and H2 (ClogLog hazard) are in progress
- Country panel (country×month) and conflict panel (conflict×month) are at different levels — merging requires care
