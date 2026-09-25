# Graph Export Guidance

Read this before writing any code that saves a Stata graph. The default export
path below applies whenever the user has not specified a format.

## Defaults

```stata
* General purpose / slides / quick sharing — high-resolution PNG:
graph export "output/figures/wage_by_educ.png", width(2000) replace

* Paper (LaTeX manuscript) — vector PDF:
graph export "output/figures/wage_by_educ.pdf", replace
```

- **PNG** is the default. Always pass `width(2000)` — Stata's default pixel
  size is too small for documents — and `replace`.
- **PDF** only when the target is a LaTeX paper (vector, scales cleanly).
  `width()` does not apply to PDF.
- Never export both formats unless asked; pick one per the destination rule.
- Never use `graph save` as the final output — a `.gph` file is an
  intermediate, not a deliverable.

## Naming and Location

- Descriptive lowercase names with underscores: `wage_by_educ.png`,
  `event_study_coefs.pdf` — not `graph1.png`.
- Save into a dedicated output directory (`output/figures/` or the project's
  existing figures folder), never next to raw data.

## Before Exporting

- Give the graph a title and axis titles — an untitled graph is not finished:

```stata
twoway (scatter wage educ) (lfit wage educ), ///
    title("Wage by education") ///
    xtitle("Years of education") ytitle("Annual wage") ///
    legend(off)
graph export "output/figures/wage_by_educ.png", width(2000) replace
```

- If the project uses a scheme (`set scheme ...`), keep it consistent across
  all graphs in the same project. Do not install schemes inside the do-file —
  missing packages go through `ado_package_install`.

## Verification

After the do-file runs, confirm the file exists and is non-empty (Bash
`ls -l` or Glob). A `graph export` that silently failed (no graph in memory,
wrong path) produces no file and no `r()` code in some Stata versions — the
file check is the real verification, not the log alone.
