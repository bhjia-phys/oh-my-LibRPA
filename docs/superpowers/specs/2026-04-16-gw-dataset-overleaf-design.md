# GW Dataset Overleaf Note Design

## Context

We need a new English Overleaf project at `~/同步空间/overleaf/gw_dataset` that documents the current status of the CaMg$_2$N$_2$ ABACUS+LibRPA investigation. The note should not read like a finished journal manuscript. It should read like a structured project note that can later grow into a formal paper section.

The note must include:

- what this project is trying to achieve
- what tests have already been run
- what the current evidence suggests
- the newly generated same-ABFS/different-lattice comparison figure
- a table of contents

## Goal

Create a standalone English LaTeX manuscript that explains the project scope, summarizes the current test matrix, presents the baseline-vs-lattice+20\% GW band comparison, and states the current conclusion with the right level of caution.

## Audience

The target reader is an internal collaborator who already knows GW, ABACUS, LibRPA, and auxiliary-basis terminology, but needs a clean and compact written record of what has been tested and what can currently be concluded.

## Format Choice

Use a standalone LaTeX `article` project rather than a journal-specific submission template.

Reasoning:

- the document needs a visible table of contents
- the note is project-facing and expandable, not yet submission-facing
- the structure should stay lightweight while remaining easy to migrate into a journal template later

## Project Layout

Create the following structure under `~/同步空间/overleaf/gw_dataset`:

- `main.tex`
- `figures/`
- `tables/`

The project should compile directly with `latexmk -pdf`.

## Manuscript Structure

The first draft should contain these sections:

1. `Abstract`
2. `Introduction`
3. `Project Goal`
4. `Current Test Status`
5. `Same-ABFS, Different-Lattice Comparison`
6. `Current Interpretation`
7. `Next Steps`

`\\tableofcontents` should appear after the abstract.

## Content Plan

### Introduction

Explain that the project is investigating whether irregularities in periodic GW band structures are tied to the localized resolution-of-the-identity treatment, the auxiliary basis construction, or related workflow choices. Make it clear that the current text is a status note for an ongoing investigation.

### Project Goal

State that the immediate purpose is to determine whether the observed near-gap band irregularities are primarily controlled by:

- the auxiliary basis recipe itself
- long-range interaction sensitivity
- other workflow ingredients such as geometry- or screening-related effects

### Current Test Status

Include a compact summary table covering the main tested routes so far:

- `noABFS / internal PCA`
- `G2 gaus_extend baseline`
- `jle-smooth plus1 fixfmt`
- `jle-smooth plus5more fixfmt`
- `same G2 gaus_extend ABFS with lattice +20%`

For each row, summarize:

- the essential setup difference
- whether the run completed
- the GW gap if available
- the practical takeaway

### Same-ABFS, Different-Lattice Comparison

Insert the already generated figure:

- `/Users/ghj/code/oh-my-librpa/camg2n2_latscale120_vs_baseline_band_compare/camg2n2_gw_band_compare_baseline_vs_latscale120.png`

Explain clearly that:

- both panels use the same `G2 gaus_extend` ABFS
- only the lattice constant changes
- each panel is aligned to its own VBM
- the purpose is to isolate how the band shape changes when the geometry is expanded while the auxiliary basis recipe stays fixed

### Current Interpretation

State the current evidence conservatively:

- the expanded-lattice case shows visibly smoother near-gap conduction dispersions than the baseline
- this is consistent with an LRI-related interpretation
- however, the 20\% lattice expansion also drives the system to a negative GW gap, so the structural perturbation is too large to serve as a clean diagnostic by itself

The wording must avoid claiming that the LRI hypothesis has been proven.

### Next Steps

Recommend smaller lattice expansions such as `+5%` and `+10%` as cleaner follow-up tests.

## Figures and Tables

The first draft should include:

- one figure: the baseline-vs-lattice+20\% band comparison
- one table: the current test summary

No additional figures are required in the first draft.

## Style Constraints

- English only
- compact, technical, and readable
- no exaggerated claims
- no journal-polish padding
- suitable for iterative project updates

## Boundaries

This first draft does not need:

- a literature review
- formal bibliography support unless needed
- exhaustive computational details
- new data generation

The task is documentation and presentation of already obtained results.
