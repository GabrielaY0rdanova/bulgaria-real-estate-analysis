# =============================================================================
# bulgaria-real-estate-analysis — Export for Power BI
# Source: data/df_analysis.pkl (output of 01_load.py)
#         data/clean/property_features.csv
#         data/clean/features.csv
# Purpose: Produce a single flat, Power BI-ready CSV from the analysis
#          DataFrame. Resolves all foreign keys, derives outlier flags,
#          pivots property features into binary columns, and strips columns
#          that are irrelevant or redundant in a BI context.
#          The output is the sole data source for the Power BI dashboard —
#          no merges or transformations are required inside Power Query.
# Script:  06
# Run after: 01_load.py
# Output:  data/df_powerbi.csv
# =============================================================================

from pathlib import Path
import pandas as pd

# =============================================================================
# CONFIG
# =============================================================================

DATA_PATH  = Path("data/df_analysis.pkl")
CLEAN_PATH = Path("data/clean")
OUT_PATH   = Path("data")
OUT_PATH.mkdir(exist_ok=True)

# Columns to carry through to the dashboard.
# Internal IDs (geo_id, property_type_id, etc.) are dropped — their resolved
# English labels are already present. Raw URLs and scraped_at are also dropped
# as they add no analytical value in a BI context.
KEEP_COLS = [
    # --- identifiers ---
    "listing_id",
    "property_id",
    "source_id",

    # --- transaction ---
    "transaction_type",
    "price",
    "price_per_m2",
    "price_on_request",
    "status",
    "listing_tier",

    # --- property physical ---
    "area_m2",
    "bedrooms",
    "floor",
    "total_floors",
    "construction_status",
    "year_built",

    # --- resolved lookups ---
    "property_type_en",
    "property_type_category",
    "construction_type_en",
    "contact_type",

    # --- geography ---
    "locality_en",
    "region_en",

    # --- dates ---
    "date_posted",
    "date_modified",

    # --- flags ---
    "has_photos",
]

# Features to pivot into binary indicator columns.
# Restricted to the 17 analytically meaningful amenities used in
# 05_features_analysis.py — pivoting all 46 features would produce
# many near-empty columns that clutter the data model.
PIVOT_FEATURES = [
    "elevator",
    "furnished",
    "unfurnished",
    "with parking space",
    "with garage",
    "underground parking",
    "parking available",
    "air conditioning",
    "luxury",
    "insulated/renovated",
    "needs renovation",
    "gated complex",
    "alarm system",
    "video surveillance",
    "access control",
    "internet connection",
    "pets allowed",
]

# =============================================================================
# LOAD
# =============================================================================

print("Loading df_analysis...")
df = pd.read_pickle(DATA_PATH)
print(f"  {len(df):,} rows × {df.shape[1]} columns")

print("\nLoading property_features and features lookup...")
property_features = pd.read_csv(CLEAN_PATH / "property_features.csv")
features_lookup   = pd.read_csv(CLEAN_PATH / "features.csv")
print(f"  property_features: {len(property_features):,} rows")
print(f"  features:          {len(features_lookup):,} rows")

# =============================================================================
# OUTLIER FLAGS
# IQR × 3.0 per property_type_en group — mirrors the cleaning pipeline logic
# used in 05_features_analysis.py. Flagged rows are retained in the export
# (dropping them would misrepresent market volume) but the flag columns allow
# Power BI visuals to exclude them from price / €/m² calculations via filters.
# =============================================================================

print("\nDeriving outlier flags...")

def iqr_outlier_mask(series: pd.Series, k: float = 3.0) -> pd.Series:
    """Return a boolean mask: True where values fall outside Q1 − k×IQR or Q3 + k×IQR."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr    = q3 - q1
    return (series < q1 - k * iqr) | (series > q3 + k * iqr)

# Price outlier: computed per property_type_en group
df["price_outlier"] = False
for ptype, grp in df[df["price"].notna()].groupby("property_type_en"):
    if len(grp) < 10:
        continue
    df.loc[grp.index[iqr_outlier_mask(grp["price"])], "price_outlier"] = True

# Area outlier: global IQR + zero-area catch
df["area_outlier"] = False
area_valid = df["area_m2"].notna()
df.loc[
    df.index[area_valid][iqr_outlier_mask(df.loc[area_valid, "area_m2"])],
    "area_outlier"
] = True
df.loc[df["area_m2"] == 0, "area_outlier"] = True

print(f"  price_outlier flagged: {df['price_outlier'].sum():,}")
print(f"  area_outlier  flagged: {df['area_outlier'].sum():,}")

KEEP_COLS += ["price_outlier", "area_outlier"]

# =============================================================================
# PIVOT FEATURES — binary indicator columns
# Each selected amenity becomes a 0/1 column named feat_<snake_case>.
# For example, "with garage" → feat_with_garage.
# Properties that have the feature get 1; all others get 0.
# =============================================================================

print("\nPivoting property features into binary indicator columns...")

# Resolve feature names for the full junction table
pf = property_features.merge(
    features_lookup[["feature_id", "name_en"]],
    on="feature_id",
    how="left",
)

# Filter to the target feature set only
pf_filtered = pf[pf["name_en"].isin(PIVOT_FEATURES)].copy()

# Build a set of property_ids per feature for fast lookup
feature_prop_map = (
    pf_filtered.groupby("name_en")["property_id"]
    .apply(set)
    .to_dict()
)

# Create binary columns on df
for feat in PIVOT_FEATURES:
    col_name = "feat_" + feat.replace(" ", "_").replace("/", "_")
    prop_ids = feature_prop_map.get(feat, set())
    df[col_name] = df["property_id"].isin(prop_ids).astype(int)
    KEEP_COLS.append(col_name)

print(f"  {len(PIVOT_FEATURES)} feature columns added")

# =============================================================================
# SELECT & CAST
# Keep only the columns defined in KEEP_COLS (in that order).
# Strip timezone info from datetime columns — Power BI does not support
# timezone-aware datetimes and will silently convert or error on import.
# Cast boolean columns to int (0/1) for clean Power BI slicing.
# =============================================================================

print("\nSelecting columns and casting dtypes...")

# Drop any KEEP_COLS entries that don't exist in this run of df
cols_present = [c for c in KEEP_COLS if c in df.columns]
missing      = set(KEEP_COLS) - set(cols_present)
if missing:
    print(f"  WARNING: columns not found, skipped: {sorted(missing)}")

out = df[cols_present].copy()

# Datetime — strip timezone
for col in ["date_posted", "date_modified"]:
    if col in out.columns:
        out[col] = pd.to_datetime(out[col], errors="coerce").dt.tz_localize(None)

# Boolean → int
for col in ["price_on_request", "has_photos", "price_outlier", "area_outlier"]:
    if col in out.columns:
        out[col] = out[col].astype(int)

print(f"  Output shape: {out.shape[0]:,} rows × {out.shape[1]} columns")

# =============================================================================
# VALIDATE
# =============================================================================

print("\nValidation:")

if len(out) != len(df):
    raise ValueError(
        f"Row count mismatch: expected {len(df):,}, got {len(out):,}"
    )
print(f"  Row count: {len(out):,} — OK")

for col in ["transaction_type", "property_type_en", "region_en", "locality_en"]:
    null_pct = out[col].isna().mean() * 100
    status   = "OK" if null_pct == 0.0 else "WARN"
    print(f"  {col:<25} null: {null_pct:.1f}%  [{status}]")

# Spot-check key values
sale_median = out.loc[out["transaction_type"] == "sale", "price"].median()
print(f"  Median sale price:      €{sale_median:,.0f}")

apt_ppm2_median = out.loc[
    (out["transaction_type"] == "sale") &
    (out["property_type_en"] == "apartment") &
    out["price_per_m2"].notna()
, "price_per_m2"].median()
print(f"  Apartment median €/m²:  €{apt_ppm2_median:,.0f}")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n=== EXPORT SUMMARY ===")
print(f"Shape:              {out.shape[0]:,} rows × {out.shape[1]} columns")
print(f"\nColumns exported:")
for i, col in enumerate(out.columns, 1):
    print(f"  {i:>2}. {col}")

print(f"\nTransaction type:")
print(out["transaction_type"].value_counts().to_string())

print(f"\nProperty type (top 10):")
print(out["property_type_en"].value_counts().head(10).to_string())

print(f"\nRegion (top 10):")
print(out["region_en"].value_counts().head(10).to_string())

print(f"\nOutlier summary:")
print(f"  price_outlier = 1:  {out['price_outlier'].sum():,} rows")
print(f"  area_outlier  = 1:  {out['area_outlier'].sum():,} rows")

print(f"\nFeature prevalence (% of all listings):")
feat_cols = [c for c in out.columns if c.startswith("feat_")]
for col in feat_cols:
    pct = out[col].mean() * 100
    print(f"  {col:<35} {pct:.1f}%")

# =============================================================================
# SAVE
# =============================================================================

out_file = OUT_PATH / "df_powerbi.csv"
out.to_csv(out_file, index=False, encoding="utf-8-sig")
print(f"\ndf_powerbi.csv saved to: {out_file}")
print(f"File size: {out_file.stat().st_size / 1_048_576:.1f} MB")

# --- price history ---
price_history = pd.read_csv(CLEAN_PATH / "price_history.csv")
price_history_file = OUT_PATH / "df_price_history.csv"
price_history.to_csv(price_history_file, index=False, encoding="utf-8-sig")
print(f"\ndf_price_history.csv saved to: {price_history_file}")
print(f"  {len(price_history):,} price change rows")

print("\n06_export_for_powerbi.py complete.")
