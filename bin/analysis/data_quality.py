# bin/analysis/data_quality.py

import pandas as pd
import numpy as np


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def _df_summary(df):
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }


# ---------------------------------------------------
# 1. STRUCTURAL VALIDATION
# ---------------------------------------------------
def qc_structure(df):
    summary = _df_summary(df)

    txt = (
        "Data structure check.\n\n"
        f"Rows: {summary['rows']}\n"
        f"Columns: {', '.join(summary['columns'])}\n\n"
        "Dtypes:\n" + "\n".join([f"{k}: {v}" for k, v in summary["dtypes"].items()])
    )

    return txt, summary


# ---------------------------------------------------
# 2. MISSING VALUES
# ---------------------------------------------------
def qc_missing(df):
    missing_counts = df.isna().sum().to_dict()

    txt = (
        "Missing data check.\n\n"
        "Missing values per column:\n"
        + "\n".join([f"{k}: {v}" for k, v in missing_counts.items()])
        + "\n"
    )

    return txt, missing_counts


# ---------------------------------------------------
# 3. DUPLICATES
# ---------------------------------------------------
def qc_duplicates(df):
    total_dups = int(df.duplicated().sum())

    txt = (
        "Duplicate row check.\n\n"
        f"Total duplicates: {total_dups}\n"
    )

    return txt, {"duplicates": total_dups}


# ---------------------------------------------------
# 4. OUTLIER DETECTION (Z-SCORE)
# ---------------------------------------------------
def qc_outliers(df, numeric_vars):
    outlier_info = {}

    for col in numeric_vars:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        mean = series.mean()
        std = series.std()
        if std == 0:
            continue

        z = (series - mean) / std
        outlier_count = int((z.abs() > 3).sum())

        outlier_info[col] = {
            "mean": float(mean),
            "std": float(std),
            "outliers_z>3": outlier_count,
        }

    txt = "Outlier check (|z| > 3).\n\n"
    for col, info in outlier_info.items():
        txt += f"{col}: mean={info['mean']:.3f}, std={info['std']:.3f}, outliers={info['outliers_z>3']}\n"

    return txt, outlier_info


# ---------------------------------------------------
# 5. RANGE CHECK
# ---------------------------------------------------
def qc_ranges(df, numeric_vars):
    ranges = {}

    for col in numeric_vars:
        if df[col].dropna().empty:
            continue

        ranges[col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max())
        }

    txt = "Range check for numeric variables.\n\n"
    for col, info in ranges.items():
        txt += f"{col}: min={info['min']}, max={info['max']}\n"

    return txt, ranges

