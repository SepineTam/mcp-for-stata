---
paths:
  - "**/*.do"
---

# Stata Do-file Rules

Apply these rules when writing or modifying Stata do-files, unless the user
explicitly asks otherwise.

## Style

- Indent with 4 spaces. Do not use tabs.
- One command per line. Do not use `#delimit ;`.
- Break long commands with `///` and indent the continuation lines.
- Write Stata commands and variable names in lowercase.
- Use `*` for standalone comment lines and `//` for end-of-line comments.

## Tables

- Export regression tables with `esttab` (from the `estout` package). Do not
  hand-copy results or use `outreg`-style legacy commands.
- If `estout` is not installed, install it through the controlled ado-install
  path (`ado_package_install`) instead of calling `ssc install` inside the
  do-file.

## Figures

- Export graphs with `graph export` and always set an explicit width, e.g.
  `graph export figure.png, width(2000) replace`.
- Prefer PNG for exported figures unless the user requests another format.

## General

- Never overwrite raw data files. Save derived datasets to a separate output
  directory.
- Use relative paths or global macros defined at the top of the do-file. Do
  not hard-code absolute paths.
