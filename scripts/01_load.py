# =============================================================================
# bulgaria-real-estate-analysis — Load
# Source: data/clean/*.csv (output of bulgaria-real-estate-cleaning pipeline)
# Purpose: Load all eight normalised tables, resolve foreign keys, and produce
#          a single flat analysis-ready DataFrame saved as data/df_analysis.pkl.
#          All downstream analysis scripts load from this pickle.
# Script:  01
# Run after: (none — pipeline entry point for analysis stage)
# Output:  data/df_analysis.pkl
# =============================================================================

from pathlib import Path
import pandas as pd

DATA_PATH  = Path("data/clean")
OUT_PATH   = Path("data")
OUT_PATH.mkdir(exist_ok=True)

# =============================================================================
# LOAD — all eight tables
# =============================================================================

print("Loading tables...")

PHONE_COLS = ["phone"]

listings           = pd.read_csv(DATA_PATH / "listings.csv",           low_memory=False)
properties         = pd.read_csv(DATA_PATH / "properties.csv",         low_memory=False)
geographies        = pd.read_csv(DATA_PATH / "geographies.csv",        low_memory=False)
contacts           = pd.read_csv(DATA_PATH / "contacts.csv",           low_memory=False,
                                  dtype={c: "string" for c in PHONE_COLS})
property_types     = pd.read_csv(DATA_PATH / "property_types.csv",     low_memory=False)
construction_types = pd.read_csv(DATA_PATH / "construction_types.csv", low_memory=False)
features           = pd.read_csv(DATA_PATH / "features.csv",           low_memory=False)
property_features  = pd.read_csv(DATA_PATH / "property_features.csv",  low_memory=False)

for name, df in [
    ("listings",           listings),
    ("properties",         properties),
    ("geographies",        geographies),
    ("contacts",           contacts),
    ("property_types",     property_types),
    ("construction_types", construction_types),
    ("features",           features),
    ("property_features",  property_features),
]:
    print(f"  {name:<22} {len(df):>8,} rows  |  {len(df.columns)} cols")

# =============================================================================
# RESOLVE GEOGRAPHY
# Three-level hierarchy: region → locality → area.
# properties.geo_id points to the most specific level available —
# area when present, locality otherwise.
# We resolve upward to always attach both locality_en and region_en.
# =============================================================================

print("\nResolving geography hierarchy...")

regions    = geographies[geographies["level"] == "region"][
    ["geo_id", "name_en"]
].rename(columns={"geo_id": "region_geo_id", "name_en": "region_en"})

localities = geographies[geographies["level"] == "locality"][
    ["geo_id", "name_en", "locality_type", "parent_id"]
].rename(columns={
    "name_en":      "locality_en",
    "locality_type": "locality_type_geo",
    "parent_id":    "region_geo_id",
})

areas = geographies[geographies["level"] == "area"][
    ["geo_id", "name_en", "parent_id"]
].rename(columns={"name_en": "area_en", "parent_id": "locality_geo_id"})

# Build a lookup keyed on geo_id → (locality_en, locality_type_geo, region_geo_id)
# for both locality-level and area-level geo_ids.

# Locality-level: direct match
locality_lookup = localities[
    ["geo_id", "locality_en", "locality_type_geo", "region_geo_id"]
].copy()

# Area-level: resolve via parent locality
area_lookup = (
    areas
    .merge(
        localities[["geo_id", "locality_en", "locality_type_geo", "region_geo_id"]],
        left_on="locality_geo_id",
        right_on="geo_id",
        how="left",
        suffixes=("_area", ""),
    )
    [["geo_id_area", "locality_en", "locality_type_geo", "region_geo_id"]]
    .rename(columns={"geo_id_area": "geo_id"})
)

# Combine both lookup levels
geo_lookup = pd.concat([locality_lookup, area_lookup], ignore_index=True)
geo_lookup = geo_lookup.merge(regions, on="region_geo_id", how="left")
geo_lookup = geo_lookup[["geo_id", "locality_en", "locality_type_geo", "region_en"]]

# Sanity check — every geo_id in properties should resolve
unresolved = set(properties["geo_id"]) - set(geo_lookup["geo_id"])
if unresolved:
    raise ValueError(f"{len(unresolved):,} geo_ids could not be resolved: {list(unresolved)[:10]}")

print(f"  All {properties['geo_id'].nunique():,} unique geo_ids resolved successfully")

# =============================================================================
# MERGE — build flat analysis DataFrame
# Join order: listings → properties → lookups → contacts → geography
# =============================================================================

print("\nBuilding flat analysis DataFrame...")

df = (
    listings
    .merge(properties,         on="property_id",         how="left")
    .merge(
        property_types[["property_type_id", "name_en", "category"]],
        on="property_type_id",
        how="left",
    )
    .merge(
        construction_types[["construction_type_id", "name_en"]],
        on="construction_type_id",
        how="left",
        suffixes=("", "_ct"),
    )
    .merge(
        contacts[["contact_id", "contact_type", "name"]],
        on="contact_id",
        how="left",
    )
    .merge(geo_lookup, on="geo_id", how="left")
)

# Rename for clarity
df = df.rename(columns={
    "name_en":    "property_type_en",
    "category":   "property_type_category",
    "name_en_ct": "construction_type_en",
    "name":       "contact_name",
})

# =============================================================================
# DERIVE — price_per_m2
# Only meaningful when both price and area_m2 are non-null and area > 0.
# Infinite values (area = 0) are set to null.
# =============================================================================

df["price_per_m2"] = (df["price"] / df["area_m2"]).replace(
    [float("inf"), float("-inf")], None
)

# =============================================================================
# CAST — parse dates, fix dtypes
# =============================================================================

for col in ["date_posted", "date_modified", "scraped_at", "date_last_checked"]:
    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

df["price_on_request"] = df["price_on_request"].map(
    lambda x: str(x).strip().lower() == "true"
)
df["has_photos"] = df["has_photos"].map(
    lambda x: str(x).strip().lower() == "true"
)

for col in ["bedrooms", "floor", "total_floors", "year_built"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

# =============================================================================
# VALIDATE — row count and key column nulls
# =============================================================================

print("\nValidation:")

expected_rows = len(listings)
if len(df) != expected_rows:
    raise ValueError(
        f"Row count mismatch after merge: expected {expected_rows:,}, got {len(df):,}"
    )
print(f"  Row count: {len(df):,} (matches listings — OK)")

assert df["source_id"].is_unique, "source_id is not unique after merge"
print(f"  source_id unique: OK")

null_checks = {
    "property_type_en": 0.0,
    "region_en":        0.0,
    "locality_en":      0.0,
    "transaction_type": 0.0,
    "price":            3.0,
    "area_m2":          3.0,
}
for col, max_null_pct in null_checks.items():
    null_pct = df[col].isna().mean() * 100
    status = "OK" if null_pct <= max_null_pct else "WARN"
    print(f"  {col:<25} null: {null_pct:.1f}%  [{status}]")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n=== ANALYSIS DATAFRAME SUMMARY ===")
print(f"Shape:              {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"\nTransaction type:")
print(df["transaction_type"].value_counts().to_string())
print(f"\nProperty type (top 10):")
print(df["property_type_en"].value_counts().head(10).to_string())
print(f"\nRegion (top 10):")
print(df["region_en"].value_counts().head(10).to_string())
print(f"\nContact type:")
print(df["contact_type"].value_counts().to_string())
print(f"\nPrice (sale):")
sale_prices = df.loc[df["transaction_type"] == "sale", "price"].dropna()
print(f"  n={len(sale_prices):,} | min={sale_prices.min():,.0f} | "
      f"median={sale_prices.median():,.0f} | "
      f"mean={sale_prices.mean():,.0f} | "
      f"max={sale_prices.max():,.0f}")
print(f"\nPrice (rental):")
rent_prices = df.loc[df["transaction_type"] == "rental", "price"].dropna()
print(f"  n={len(rent_prices):,} | min={rent_prices.min():,.0f} | "
      f"median={rent_prices.median():,.0f} | "
      f"mean={rent_prices.mean():,.0f} | "
      f"max={rent_prices.max():,.0f}")
print(f"\nColumns: {list(df.columns)}")

# =============================================================================
# SAVE
# =============================================================================

out = OUT_PATH / "df_analysis.pkl"
df.to_pickle(out)
print(f"\ndf_analysis saved to: {out}")
print("01_load.py complete.")
