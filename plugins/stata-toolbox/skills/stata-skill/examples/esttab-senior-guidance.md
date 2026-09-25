# esttab Senior Guidance

Read this before writing any code that exports a regression table. `esttab`
(from the `estout` package) is the default table exporter — never hand-format
tables and never use legacy `outreg`/`outreg2` for new work.

## Setup Check

`esttab` requires the `estout` package. Package-management commands are banned
inside do-files, so check availability outside the do-file:

- Call `mcp__stata-mcp__help` with `cmd="esttab"` — a result means it is
  installed.
- If missing, call `mcp__stata-mcp__ado_package_install` with
  `package="estout"`, `source="ssc"` (unsafe profile only). If that tool is
  unavailable, report to the user that `estout` must be installed manually.

## Core Pattern

Store models, then export them together:

```stata
eststo clear
eststo m1: reghdfe wage educ, absorb(year industry) vce(cluster firm)
eststo m2: reghdfe wage educ exper, absorb(year industry) vce(cluster firm)

esttab m1 m2 using "output/tables/reg_wage.tex", replace ///
    label booktabs fragment nonumbers ///
    b(%9.3f) se(%9.3f) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    scalars("N Observations" "r2_a Adj. R-squared") ///
    sfmt(%9.0fc %9.3f) ///
    mtitles("(1)" "(2)") ///
    addnotes("Standard errors clustered at the firm level in parentheses." ///
             "Year and industry fixed effects included in all models.")
```

## Options That Matter

| Option | Use it for |
|---|---|
| `label` | Variable labels instead of raw names — always on for paper tables |
| `booktabs fragment` | LaTeX: clean rules, no wrapper environment, ready for `\input{}` |
| `b(%9.3f) se(%9.3f)` | Coefficient and SE formats; SEs print below in parentheses by default |
| `star(* 0.10 ** 0.05 *** 0.01)` | Significance stars with explicit thresholds |
| `scalars(...)` + `sfmt(...)` | Bottom rows: N (`%9.0fc` adds thousands separators), `r2_a` |
| `mtitles(...)` | Column headers; use numbers or short model names |
| `indicate("Year FE = *year")` | YES/NO rows for fixed effects when you don't want every FE coefficient shown |
| `keep()` / `drop()` | Show only the coefficients of interest |
| `compress` | Tighter table when it runs wide |
| `addnotes(...)` | Table notes (clustering level, FE structure, data source) |

## Output Format by Destination

- **Paper (LaTeX)**: `esttab ... using "name.tex", replace label booktabs fragment`
  — the `.tex` file is `\input{}`-ed into the manuscript.
- **Quick look / sharing**: `.rtf` (opens in Word) or `.csv` (opens in Excel)
  with the same options minus `booktabs fragment`.

## Fixed-Effect Rows

With `reghdfe`, absorbed fixed effects do not appear as coefficients. Add
explicit YES rows so readers know they were included:

```stata
esttab m1 m2 using "reg.tex", replace label booktabs fragment ///
    indicate("Year FE = *year*" "Industry FE = *industry*") ///
    keep(educ exper)
```

`indicate()` matches coefficient names by pattern; it only works if the FE
variables are actually in the equation (use `reghdfe ... , absorb(...)` plus
`indicate` requires the dummies — with absorbed-only FEs, prefer
`addnotes`/`scalars` or `estadd scalar` to state inclusion).

## Common Pitfalls

- **`eststo: command not found`** → `estout` missing; see Setup Check.
- **Table too wide for the page** → reduce shown coefficients with `keep()`,
  add `compress`, or split panels into two tables.
- **Stars misaligned with journal policy** → always declare thresholds
  explicitly via `star()`; never accept defaults silently.
- **N printed with decimals** → format it: `scalars("N N") sfmt(%9.0fc)`.
- **`esttab` after plain `regress`** works fine, but prefer `reghdfe` whenever
  fixed effects are involved (see the agent's regression defaults).
