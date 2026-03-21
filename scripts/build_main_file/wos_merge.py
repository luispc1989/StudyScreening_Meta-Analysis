# %%
# --- User Parameters ---

from pathlib import Path
from typing import List, Dict
import pandas as pd
import re

# === User Parameters (edit these) ===
INPUT_DIR = Path(r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\StudyScreening_Meta-Analysis\data\web_of_science\raw_data")
FILE_PATTERNS = ["*savedrecs*.xls*", "*savedrecs*.csv*"]  # Supports .xls, .xlsx, .csv
OUTPUT_XLSX = Path(r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\StudyScreening_Meta-Analysis\data\web_of_science\cleaned_data\wos_merged.xlsx")

# === Processing Options ===
ALSO_CSV = True        # Export also as CSV (UTF-8-SIG)
INCLUDE_ISSUE = True   # Keep 'Issue' column
DEDUPE = False         # WoS exports are already unique


# %%
# --- File listing helper ---

def list_input_files(input_dir: Path, patterns: List[str]) -> List[Path]:
    """Collect files matching multiple patterns and containing 'savedrecs' (case-insensitive)."""
    files: List[Path] = []
    for pattern in patterns:
        for f in input_dir.glob(pattern):
            if "savedrecs" in f.name.lower():
                files.append(f)
    return sorted(set(files))


# %%
# --- Readers for CSV and Excel ---

def read_csv_any(path: Path) -> pd.DataFrame:
    """Read CSV with automatic delimiter/encoding detection."""
    encodings = ["utf-8-sig", "utf-8", "latin-1"]
    for enc in encodings:
        try:
            return pd.read_csv(
                path,
                sep=None, engine="python",
                encoding=enc,
                dtype=str, na_filter=False, low_memory=False
            )
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV '{path.name}' with tried encodings {encodings}")

def read_excel_any(path: Path) -> pd.DataFrame:
    """Read Excel (.xls or .xlsx) with engine fallback."""
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(path, engine="openpyxl", dtype=str)
    elif suffix == ".xls":
        return pd.read_excel(path, engine="xlrd", dtype=str)
    else:
        raise ValueError(f"Unsupported Excel file type: {path.suffix}")

def read_any(path: Path) -> pd.DataFrame:
    """Dispatch reader by file type."""
    if path.suffix.lower() in {".csv", ".tsv"}:
        return read_csv_any(path)
    elif path.suffix.lower() in {".xls", ".xlsx"}:
        return read_excel_any(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


# %%
# --- Target columns & aliases ---

TARGET_COLUMNS = [
    "Authors",
    "Publication Year",
    "Title",
    "Abstract",
    "Author Keywords",
    "Source Title",
    "Volume",
    "Issue",
    "Begin Page",
    "End Page",
    "Article Number",
    "E-mail Address",
    "DOI",
    "DOI Link",
]

ALIASES: Dict[str, List[str]] = {
    "Authors": ["authors", "author(s)"],
    "Publication Year": ["publication year", "year published", "year"],
    "Title": ["title", "article title"],
    "Abstract": ["abstract"],
    "Author Keywords": ["author keywords", "keywords"],
    "Source Title": ["source title", "journal", "publication name", "source"],
    "Volume": ["volume"],
    "Issue": ["issue", "number"],
    "Begin Page": ["begin page", "start page", "page begin"],
    "End Page": ["end page", "page end"],
    "Article Number": ["article number"],
    "E-mail Address": [
        "e-mail address", "e-mail addresses", "E-mail Addresses",
        "email addresses", "author email address", "email address"
    ],
    "DOI": ["doi"],
    "DOI Link": ["doi link"],
    "Pages": ["pages"],
    "Addresses": ["addresses", "affiliations", "author information", "reprint address"],
}


# %%
# --- Cleaning utilities ---

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename input columns to canonical TARGET_COLUMNS using ALIASES (case-insensitive)."""
    lower_to_orig = {c.lower().strip(): c for c in df.columns}
    col_map: Dict[str, str] = {}

    for target, alts in ALIASES.items():
        for alt in alts:
            key = alt.lower().strip()
            if key in lower_to_orig:
                col_map[lower_to_orig[key]] = target
                break

    for c in df.columns:
        if c not in col_map and c in TARGET_COLUMNS:
            col_map[c] = c

    return df.rename(columns=col_map)

def tidy_strings(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Clean whitespace and empty placeholders."""
    for c in cols:
        if c in df.columns:
            df[c] = (
                df[c].astype(str)
                .str.strip()
                .replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
            )
    return df

def ensure_email_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure E-mail Address column exists and is cleaned."""
    if "E-mail Address" not in df.columns:
        df["E-mail Address"] = pd.NA
    else:
        df["E-mail Address"] = (
            df["E-mail Address"].astype(str)
            .replace({"": pd.NA, " ": pd.NA, "nan": pd.NA, "None": pd.NA})
        )
    return df

def normalize_doi_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DOI and build DOI Link if missing."""
    if "DOI" in df.columns:
        df["DOI"] = (
            df["DOI"].astype(str)
            .str.strip()
            .str.replace(r"^https?://(dx\.)?doi\.org/", "", regex=True)
            .replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
        )

    if "DOI Link" not in df.columns:
        df["DOI Link"] = pd.NA

    df["DOI Link"] = df["DOI Link"].astype(str)
    df.loc[df["DOI Link"].str.fullmatch(r"0|nan|none|", case=False, na=True), "DOI Link"] = pd.NA

    need_link = df["DOI Link"].isna() & df.get("DOI", pd.Series([pd.NA] * len(df))).notna()
    df.loc[need_link, "DOI Link"] = "https://doi.org/" + df.loc[need_link, "DOI"].astype(str)
    return df


# %%
# --- File processing pipeline (single file) ---

def process_file(path: Path) -> pd.DataFrame:
    """Load and clean a single WoS export (.csv/.xls/.xlsx)."""
    df = read_any(path)
    df = normalize_columns(df)
    df = tidy_strings(df, [
        "Authors", "Title", "Abstract", "Author Keywords",
        "Source Title", "DOI", "DOI Link", "E-mail Address",
        "Begin Page", "End Page", "Article Number", "Issue", "Pages"
    ])

    # Remove non-breaking spaces
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.replace("\u00A0", " ", regex=False).str.strip()

    df = ensure_email_column(df)
    df = normalize_doi_fields(df)

    # Derive Begin/End Page from 'Pages'
    def _derive_pages(series: pd.Series) -> pd.DataFrame:
        pat = re.compile(r"^\s*([A-Za-z0-9]+)\s*[-–—]\s*([A-Za-z0-9]+)\s*$")
        begin, end = [], []
        for val in series.fillna(""):
            val = str(val).strip()
            if not val:
                begin.append(pd.NA)
                end.append(pd.NA)
                continue
            m = pat.match(val)
            if m:
                begin.append(m.group(1))
                end.append(m.group(2))
            else:
                begin.append(val)
                end.append(pd.NA)
        return pd.DataFrame({"Begin Page": begin, "End Page": end})

    need_begin = ("Begin Page" not in df.columns) or df["Begin Page"].isna().all()
    need_end = ("End Page" not in df.columns) or df["End Page"].isna().all()
    if "Pages" in df.columns and (need_begin or need_end):
        pages_df = _derive_pages(df["Pages"])
        if "Begin Page" not in df.columns or df["Begin Page"].isna().all():
            df["Begin Page"] = pages_df["Begin Page"]
        if "End Page" not in df.columns or df["End Page"].isna().all():
            df["End Page"] = pages_df["End Page"]

    for c in ["Publication Year", "Volume", "Issue", "Article Number", "Begin Page", "End Page"]:
        if c in df.columns:
            df[c] = df[c].astype("string")

    return df


# %%
# --- Select and order final columns ---

def select_and_order(df: pd.DataFrame, target_cols: List[str], include_issue: bool = True) -> pd.DataFrame:
    """Keep ONLY target columns (strict schema)."""
    cols = target_cols.copy()
    if not include_issue and "Issue" in cols:
        cols.remove("Issue")

    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA

    return df[cols]


# %%
# --- Cell 7: Run pipeline (merge, clean, export, numeric detection fixed + left alignment + strict DOI check) ---

# List input files (supports .xls/.xlsx/.csv)
files = list_input_files(INPUT_DIR, FILE_PATTERNS)
if not files:
    raise FileNotFoundError(f"No input files found matching {FILE_PATTERNS} in {INPUT_DIR}")

# Process each input file
frames = []
for f in files:
    print(f"Reading: {f.name}")
    df_part = process_file(f)
    frames.append(df_part)

# Merge all parts
merged = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=TARGET_COLUMNS)

# Select and order final columns (Issue controlled by INCLUDE_ISSUE)
final_df = select_and_order(merged, TARGET_COLUMNS, include_issue=INCLUDE_ISSUE).copy()

# Final polish: trim strings & remove NBSPs
for c in final_df.columns:
    if pd.api.types.is_string_dtype(final_df[c]) or final_df[c].dtype == "object":
        final_df.loc[:, c] = (
            final_df[c].astype("string")
            .str.replace("\u00A0", " ", regex=False)
            .str.strip()
        )

# EXTRA CLEANING: remove garbage tokens from page columns (e.g., "+", "-", "–", "—")
for c in ["Begin Page", "End Page"]:
    if c in final_df.columns:
        final_df.loc[:, c] = (
            final_df[c]
            .astype("string")
            .str.replace("\u00A0", " ", regex=False)
            .str.strip()
            .replace({
                "+": None, "-": None, "–": None, "—": None,
                "N/A": None, "n/a": None, "na": None
            })
        )

# First, turn clean blanks into None so Excel writes truly empty cells
final_df = final_df.replace({"": None, pd.NA: None, "<NA>": None, "nan": None, "None": None})

# Cast numeric-like columns where safe (digits only) using an object-typed buffer
numeric_like_cols = ["Publication Year", "Volume", "Issue", "Begin Page", "End Page", "Article Number"]
for c in numeric_like_cols:
    if c in final_df.columns:
        s = final_df[c].astype("string").str.strip()
        mask_num = s.str.fullmatch(r"\d+").fillna(False)
        col = pd.Series([None] * len(s), index=s.index, dtype=object)
        if mask_num.any():
            col.loc[mask_num] = pd.to_numeric(s.loc[mask_num], errors="coerce", downcast="integer")
        if (~mask_num).any():
            text_part = s.loc[~mask_num].where(s.loc[~mask_num].notna(), None)
            text_part = text_part.astype("string").str.replace("\u00A0", " ", regex=False).str.strip()
            text_part = text_part.replace({"": None, "nan": None, "<NA>": None, "None": None})
            col.loc[~mask_num] = text_part.astype(object)
        final_df.loc[:, c] = col

# Passive duplicate checks (no removal)
dup_all = final_df.duplicated().sum()
dup_doi = final_df["DOI"].duplicated().sum() if "DOI" in final_df.columns else 0
print(f"Duplicate rows (full-row comparison): {dup_all}")
print(f"Duplicate DOIs (raw count): {dup_doi}")

# --- STRICT DOI DUPLICATE ANALYSIS (10.xxxx/... pattern only) ---
if "DOI" in final_df.columns:
    doi_norm = (
        pd.Series(final_df["DOI"])
        .astype("string")
        .str.strip()
        .str.lower()
        .str.replace(r"^https?://(dx\.)?doi\.org/", "", regex=True)
    )
    valid_pat = r"^10\.\d{4,9}/\S+$"  # Crossref-style DOI pattern
    valid_mask = doi_norm.str.fullmatch(valid_pat).fillna(False)
    strict_counts = doi_norm[valid_mask].value_counts()
    strict_dup_keys = strict_counts[strict_counts > 1]
    strict_extra_rows = int((strict_dup_keys - 1).sum())

    print("\n[STRICT DOI DUPLICATES]")
    print(f"Unique valid DOIs that repeat: {len(strict_dup_keys)}")
    print(f"Extra rows among valid DOIs:   {strict_extra_rows}")

    if len(strict_dup_keys) > 0:
        print("\nExamples of repeated valid DOIs:")
        for d in strict_dup_keys.index[:10]:
            subset = final_df.loc[
                doi_norm == d,
                ["DOI", "Title", "Publication Year", "Source Title", "Volume", "Issue", "Begin Page", "End Page"]
            ]
            print(f"\nDOI: {d}  (n={len(subset)})")
            print(subset.head(3).to_string(index=False))
else:
    print("\nNo DOI column found; skipping DOI duplicate analysis.")

# Ensure output folder exists
OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)

# Export cleanly (Excel and CSV); na_rep="" ensures blanks stay empty
with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
    final_df.to_excel(writer, index=False, sheet_name="WoS_Merged", na_rep="")
    # Apply left alignment to all cells in the Excel sheet
    from openpyxl.styles import Alignment
    ws = writer.sheets["WoS_Merged"]
    left_align = Alignment(horizontal="left")
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = left_align

if ALSO_CSV:
    out_csv = OUTPUT_XLSX.with_suffix(".csv")
    final_df.to_csv(out_csv, index=False, encoding="utf-8-sig", na_rep="")

print(f"\nDone. Rows: {len(final_df)}")
print(f"Excel written to: {OUTPUT_XLSX}")
if ALSO_CSV:
    print(f"CSV written to:   {out_csv}")


# %%



