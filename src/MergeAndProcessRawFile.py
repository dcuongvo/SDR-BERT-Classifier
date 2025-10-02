# convert_html_that_has_xls_extensiion_to_csv.py
# Usage:
#   python convert_fake_xls_html_to_csv.py SDR_676_202509.xls

import sys
from pathlib import Path
import pandas as pd

# ---------- CONFIG ----------
ROOT = Path(__file__).resolve().parents[1]
IN_DIR  = ROOT / "data" / "SDR_data"              
GLOB    = "SDR_676_*.xls"  #Match all file has pattern SD_676_...
OUT_CSV = ROOT / "data" / "processed" / "SDR_676_all_converted.csv"
# --------------------------------

def read_htmlish_xls(src_path) -> Path:
    # Ensure src_path is a Path object
    src_path = Path(src_path)
    # 1) Parse all tables from the file (HTML masquerading as .xls)
    tables = pd.read_html(src_path, header=0)  # pandas auto-detects HTML tables
    if not tables:
        raise ValueError("No tables found in the file.")
    # 2) Pick the largest table by number of rows (usually the real dataset)
    largest_idx = max(range(len(tables)), key=lambda i: tables[i].shape[0])
    df = tables[largest_idx].copy()

    # 3) Light, safe cleanups
    #df = df.dropna(axis=0, how="all")   # drop empty rows
    #df = df.dropna(axis=1, how="all")   # drop empty columns
    df.columns = [str(c).strip() for c in df.columns]  # strip col names

    # Drop "Unnamed: 0" if it's just an index/blank
    if df.columns[0].startswith("Unnamed"):
        col0 = df.iloc[:, 0]
        if col0.isna().mean() > 0.9:
            df = df.iloc[:, 1:]

    # tag source for traceability
    df["SourceFile"] = src_path.name
    return df


def main():
    IN_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(IN_DIR.glob(GLOB))
    if not files:
        raise SystemExit(f"No files found matching {GLOB} in {IN_DIR.resolve()}")

    frames = []
    all_cols = set()

    # first pass: read & collect columns
    for f in files:
        try:
            df = read_htmlish_xls(f)
            frames.append(df)
            all_cols |= set(df.columns)
            print(f"OK  {f.name}  -> shape={df.shape}")
        except Exception as e:
            print(f"[WARN] {f.name}: {e}")

    if not frames:
        raise SystemExit("No parsable files.")

    # make a consistent column order (union of all columns)
    all_cols = list(all_cols)
    aligned = []
    for df in frames:
        aligned.append(df.reindex(columns=all_cols))

    big = pd.concat(aligned, ignore_index=True)

    # save one big CSV
    big.to_csv(OUT_CSV, index=False)
    print(f"\nSaved combined CSV: {OUT_CSV}  rows={len(big)}  cols={big.shape[1]}")

if __name__ == "__main__":
    main()