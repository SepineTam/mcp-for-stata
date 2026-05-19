"""
Download Stata example datasets from the Stata-Press data repository.

Usage:
    uv run tests/download_data.py auto
    uv run tests/download_data.py auto nlswork
    uv run tests/download_data.py --list

Supported dataset sources:
    - sysuse: Stata built-in datasets (auto, census, lifeexp, nlsw88, etc.)
    - webuse: Stata web datasets (nlswork, union, wages, etc.)

Datasets are saved to tests/fixtures/dataset/
"""

import argparse
import urllib.request
from pathlib import Path

STATA_BASE_URL = "https://www.stata-press.com/data/r17"

SYSUSE_DATASETS = [
    "auto", "autornd", "bplong", "bpwide", "cancer", "census",
    "citytemp", "educ99gdp", "fruit", "gdppc", "lifeexp", "lnf",
    "nlsw88", "pop2000", "sp500", "states", "transpl", "tsltstck",
    "uslifeexp", "voter", "xmpl1", "xmpl2", "xmpl3",
]

WEBUSE_DATASETS = [
    "nlswork", "abdata", "air2", "auto", "consumption", "cancer",
    "catcathlab", "cigtax", "consump", "cps1", "drugtr", "educ99gdp",
    "gasoline", "grunfeld", "hbank", "hmda", "houseprice", "inelastic",
    "laborsup", "lifeexp", "margarin", "mus02psid92", "mus03cel",
    "mus04uibModal", "nhanes2", "nlswork", "oil", "panel101", "petris",
    "plow", "rdc", "rdc2", "rental", "robdata", "sbux", "ship", "smokes",
    "sp500", "stockmark", "surface", "texashs", "texhsgprc", "tofan",
    "traffic", "tslbond", "turan", "uganda", "union", "uslifeexp",
    "wages", "wpi1",
]

DATA_DIR = Path(__file__).resolve().parent / "fixtures" / "dataset"


def download(name: str) -> Path | None:
    """Download a single dataset. Returns file path on success, None on failure."""
    filename = f"{name}.dta"
    dest = DATA_DIR / filename
    if dest.exists():
        return dest

    url = f"{STATA_BASE_URL}/{filename}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())
        return dest
    except Exception:
        if dest.exists():
            dest.unlink()
        return None


def ensure_auto_fixtures() -> bool:
    """Download auto.dta and generate CSV/XLSX/SAV from it for tests.

    Returns True if all fixture files are available.
    """
    dta_path = download("auto")
    if dta_path is None:
        return False

    csv_path = DATA_DIR / "auto.csv"
    xlsx_path = DATA_DIR / "auto.xlsx"
    sav_path = DATA_DIR / "auto.sav"

    if csv_path.exists() and xlsx_path.exists() and sav_path.exists():
        return True

    import pandas as pd

    df = pd.read_stata(dta_path)  # type: ignore[assignment]

    if not csv_path.exists():
        df.to_csv(csv_path, index=False)  # type: ignore[union-attr]

    if not xlsx_path.exists():
        df.to_excel(xlsx_path, index=False, engine="openpyxl")  # type: ignore[union-attr]

    if not sav_path.exists():
        import pyreadstat
        pyreadstat.write_sav(df, str(sav_path))  # type: ignore[arg-type]

    return True


def list_datasets():
    """List all supported datasets."""
    all_datasets = sorted(set(SYSUSE_DATASETS + WEBUSE_DATASETS))
    print("Available datasets:")
    for name in all_datasets:
        marker = " [downloaded]" if (DATA_DIR / f"{name}.dta").exists() else ""
        print(f"  {name}{marker}")


def main():
    parser = argparse.ArgumentParser(description="Download Stata example datasets")
    parser.add_argument("datasets", nargs="*", help="Dataset names (e.g., auto nlswork)")
    parser.add_argument("--list", action="store_true", help="List all available datasets")
    args = parser.parse_args()

    if args.list:
        list_datasets()
        return

    if not args.datasets:
        parser.print_help()
        return

    targets = sorted(set(SYSUSE_DATASETS + WEBUSE_DATASETS)) if "all" in args.datasets else args.datasets
    for name in targets:
        result = download(name)
        if result:
            print(f"  OK: {result}")
        else:
            print(f"  FAILED: {name}")


if __name__ == "__main__":
    main()
