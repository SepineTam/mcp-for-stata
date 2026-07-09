#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : .claude/skills/mcp-smoke-test/scripts/gen_mock_data.py

"""Generate a mock auto dataset for the Stata-MCP smoke test."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


# Match the original Stata auto.dta schema.
_N_OBS = 74


def generate_mock_data(seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame that mimics the Stata auto.dta dataset.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        A DataFrame with 74 observations and 12 variables.
    """
    rng = np.random.default_rng(seed)

    make = [f"Mock Make {i + 1}" for i in range(_N_OBS)]
    price = rng.integers(3_299, 15_906, size=_N_OBS)
    mpg = rng.integers(12, 41, size=_N_OBS)
    rep78 = rng.choice([1, 2, 3, 4, 5, np.nan], size=_N_OBS, p=[0.05, 0.1, 0.3, 0.3, 0.2, 0.05])
    headroom = rng.uniform(1.5, 5.0, size=_N_OBS).round(1)
    trunk = rng.integers(5, 23, size=_N_OBS)
    weight = rng.integers(1_760, 4_840, size=_N_OBS)
    length = rng.integers(142, 233, size=_N_OBS)
    turn = rng.integers(31, 51, size=_N_OBS)
    displacement = rng.integers(79, 425, size=_N_OBS)
    gear_ratio = rng.uniform(2.4, 3.9, size=_N_OBS).round(2)
    foreign = rng.choice(["Domestic", "Foreign"], size=_N_OBS, p=[0.7, 0.3])

    return pd.DataFrame(
        {
            "make": make,
            "price": price.astype("int16"),
            "mpg": mpg.astype("int16"),
            "rep78": rep78,
            "headroom": headroom.astype("float32"),
            "trunk": trunk.astype("int16"),
            "weight": weight.astype("int16"),
            "length": length.astype("int16"),
            "turn": turn.astype("int16"),
            "displacement": displacement.astype("int16"),
            "gear_ratio": gear_ratio.astype("float32"),
            "foreign": pd.Categorical(foreign),
        }
    )


def _save_data_to_csv(df: pd.DataFrame, saved_path: Path) -> Path:
    """Save DataFrame to CSV and return the written path."""
    df.to_csv(saved_path, index=False)
    return saved_path


def _save_data_to_dta(df: pd.DataFrame, saved_path: Path) -> Path:
    """Save DataFrame to Stata .dta and return the written path."""
    # Convert categorical to string to avoid potential pandas/Stata version issues.
    out = df.copy()
    if out["foreign"].dtype.name == "category":
        out["foreign"] = out["foreign"].astype(str)
    out.to_stata(saved_path, write_index=False)
    return saved_path


def save_data(
    df: pd.DataFrame,
    output_dir: Path,
    name: str,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """Save the DataFrame in the requested formats.

    Args:
        df: DataFrame to save.
        output_dir: Directory where files are written.
        name: Base file name without extension.
        formats: List of formats; supports "csv" and "dta".

    Returns:
        Mapping from format to the written file path.
    """
    valid_formats = {"csv", "dta"}
    if formats is None:
        formats = ["csv", "dta"]
    formats = [fmt.lower() for fmt in formats if fmt.lower() in valid_formats]

    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for fmt in formats:
        saved_path = output_dir / f"{name}.{fmt}"
        if fmt == "csv":
            _save_data_to_csv(df, saved_path)
        elif fmt == "dta":
            _save_data_to_dta(df, saved_path)
        written[fmt] = saved_path

    return written


def main() -> None:
    """Generate mock auto data from the command line."""
    parser = argparse.ArgumentParser(
        description="Generate a mock auto dataset for smoke testing."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "tmp",
        help="Directory to write output files (default: ./tmp).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="auto_mock",
        help="Base file name without extension (default: auto_mock).",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["csv", "dta"],
        help="Output formats, space separated (default: csv dta).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    args = parser.parse_args()

    df = generate_mock_data(seed=args.seed)
    written = save_data(df, args.output_dir, args.name, args.formats)

    for fmt, path in written.items():
        print(f"Saved {fmt}: {path}")


if __name__ == "__main__":
    main()
