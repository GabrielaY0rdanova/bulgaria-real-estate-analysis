# =============================================================================
# bulgaria-real-estate-analysis — Features Analysis
# Source: data/df_analysis.pkl (output of 01_load.py)
#         data/clean/property_features.csv
#         data/clean/features.csv
# Purpose: Analyse property amenities — prevalence, price uplift, and regional
#          frequency. Three focused outputs feeding the dashboard narrative.
# Script:  05
# Run after: 01_load.py
# Outputs: outputs/figures/05_*.png
# =============================================================================

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns

# =============================================================================
# CONFIG
# =============================================================================

DATA_PATH    = Path("data/df_analysis.pkl")
CLEAN_PATH   = Path("data/clean")
FIGURES_PATH = Path("outputs/figures")
FIGURES_PATH.mkdir(parents=True, exist_ok=True)

COLOR_PRIMARY  = "#378ADD"   # blue  — primary bars
COLOR_TEAL     = "#1D9E75"   # teal  — secondary / positive uplift
COLOR_AMBER    = "#BA7517"   # amber — accent / negative / neutral
COLOR_CORAL    = "#D85A30"   # coral — negative uplift
COLOR_LIGHT    = "#B5D4F4"   # light blue — background bars

TOP_REGIONS = ["Sofiya", "Varna", "Plovdiv", "Burgas", "Stara Zagora",
               "Ruse", "Pleven", "Blagoevgrad"]

plt.rcParams.update({
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
    "font.family":       "sans-serif",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "axes.grid.axis":    "x",
    "grid.alpha":        0.3,
    "grid.linestyle":    "--",
})

# =============================================================================
# LOAD
# =============================================================================

df = pd.read_pickle(DATA_PATH)
print(f"Loaded df_analysis: {len(df):,} rows × {df.shape[1]} columns")

# Load junction and lookup tables to resolve feature names per property
property_features = pd.read_csv(CLEAN_PATH / "property_features.csv")
features_lookup   = pd.read_csv(CLEAN_PATH / "features.csv")

print(f"Loaded property_features: {len(property_features):,} rows")
print(f"Loaded features:          {len(features_lookup):,} rows")

# Resolve feature names
pf = property_features.merge(
    features_lookup[["feature_id", "name_en"]],
    on="feature_id",
    how="left",
)

# Attach listing/property context (price, region, transaction_type)
# df.property_id is 1-based and matches property_features.property_id directly.
pf = pf.merge(
    df[["property_id", "price", "price_per_m2", "area_m2",
        "transaction_type", "region_en", "property_type_category"]],
    on="property_id",
    how="left",
)

# Derive outlier flags here using IQR × 3.0 — same method as 05_flag_outliers.py
# in the cleaning stage. The flags were not forwarded into df_analysis, so we
# recompute them on the fly from the price and area columns.
def iqr_outlier_mask(series: pd.Series, k: float = 3.0) -> pd.Series:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return (series < q1 - k * iqr) | (series > q3 + k * iqr)

# Price outlier: per property_type_en group (mirrors cleaning pipeline logic)
df["price_outlier"] = False
for ptype, grp in df[df["price"].notna()].groupby("property_type_en"):
    if len(grp) < 10:
        continue
    df.loc[grp.index[iqr_outlier_mask(grp["price"])], "price_outlier"] = True

# Area outlier: global IQR + zero-area catch
df["area_outlier"] = False
area_valid = df["area_m2"].notna()
df.loc[df.index[area_valid][iqr_outlier_mask(df.loc[area_valid, "area_m2"])], "area_outlier"] = True
df.loc[df["area_m2"] == 0, "area_outlier"] = True

print(f"Outlier flags derived — price: {df['price_outlier'].sum():,}  area: {df['area_outlier'].sum():,}")

# Working subset: non-outlier residential listings with a known price.
# Outlier filter is critical here — a €10M apartment with "furnished" would
# inflate the furnished premium dramatically and mislead the analysis.
res_clean = df[
    (df["property_type_category"] == "residential") &
    df["price"].notna() &
    ~df["price_outlier"] &
    ~df["area_outlier"]
].copy()

pf_clean = pf[
    pf["property_id"].isin(res_clean["property_id"])
].copy()

print(f"\nClean residential subset: {len(res_clean):,} listings")
print(f"Feature rows for subset:  {len(pf_clean):,}")

# =============================================================================
# FIGURE 1 — Top 20 most advertised amenities (all residential listings)
# Horizontal bar: count + % of listings that mention each feature.
# =============================================================================

print("\n[1/3] Top 20 amenities by listing frequency...")

# Count distinct properties per feature (not rows — avoids double-counting)
feature_counts = (
    pf_clean.groupby("name_en")["property_id"]
    .nunique()
    .sort_values(ascending=False)
    .head(20)
)

total_props = res_clean["property_id"].nunique()
feature_pct = (feature_counts / total_props * 100).round(1)

fig, ax = plt.subplots(figsize=(9, 7))

bars = ax.barh(
    feature_counts.index[::-1],
    feature_counts.values[::-1],
    color=COLOR_PRIMARY,
    height=0.65,
)

# Annotate: count on the bar, % at the end
for bar, count, pct in zip(
    bars,
    feature_counts.values[::-1],
    feature_pct.values[::-1],
):
    # Percentage label to the right of bar
    ax.text(
        bar.get_width() + total_props * 0.005,
        bar.get_y() + bar.get_height() / 2,
        f"{pct}%",
        va="center",
        fontsize=8.5,
        color="#444441",
    )

ax.set_xlabel("Number of residential listings", fontsize=10)
ax.set_title("Top 20 amenities by listing frequency\n(residential listings, outliers excluded)",
             fontsize=13, fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_xlim(0, feature_counts.max() * 1.18)
ax.set_axisbelow(True)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "05_01_top_amenities.png")
plt.close(fig)
print("   Saved 05_01_top_amenities.png")

# =============================================================================
# FIGURE 2 — Price uplift for key features
# For sale and rental separately: compare median price of listings WITH
# a feature vs listings WITHOUT that feature. Express as % difference.
# Only features present in ≥ 200 clean residential listings are included
# to keep the comparison statistically meaningful.
# =============================================================================

print("[2/3] Price uplift analysis...")

# Features to analyse — anchored to the most portfolio-relevant amenities
# rather than showing all 46 (many are too sparse or non-price-relevant).
UPLIFT_FEATURES = [
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

MIN_LISTINGS = 200   # minimum presence count to include in uplift chart

def compute_uplift(transaction_type: str, price_col: str = "price") -> pd.DataFrame:
    """
    For each feature in UPLIFT_FEATURES, compute median price WITH vs WITHOUT
    the feature for a given transaction type.
    Returns a DataFrame with columns: feature, median_with, median_without,
    uplift_pct, n_with.
    """
    subset = res_clean[res_clean["transaction_type"] == transaction_type].copy()
    pf_subset = pf_clean[pf_clean["transaction_type"] == transaction_type].copy()

    if subset[price_col].isna().all():
        return pd.DataFrame()

    # Property IDs for each feature
    feature_prop_map = (
        pf_subset.groupby("name_en")["property_id"]
        .apply(set)
        .to_dict()
    )

    rows = []
    for feat in UPLIFT_FEATURES:
        props_with = feature_prop_map.get(feat, set())
        n_with = len(props_with & set(subset["property_id"]))

        if n_with < MIN_LISTINGS:
            continue

        prices_with    = subset.loc[
            subset["property_id"].isin(props_with), price_col
        ].dropna()
        prices_without = subset.loc[
            ~subset["property_id"].isin(props_with), price_col
        ].dropna()

        if len(prices_with) < 10 or len(prices_without) < 10:
            continue

        med_with    = prices_with.median()
        med_without = prices_without.median()
        uplift_pct  = (med_with - med_without) / med_without * 100

        rows.append({
            "feature":        feat,
            "median_with":    med_with,
            "median_without": med_without,
            "uplift_pct":     uplift_pct,
            "n_with":         n_with,
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("uplift_pct", ascending=False)
    return result

uplift_sale   = compute_uplift("sale")
uplift_rental = compute_uplift("rental")

print(f"   Sale uplift rows:   {len(uplift_sale)}")
print(f"   Rental uplift rows: {len(uplift_rental)}")

def plot_uplift(uplift_df: pd.DataFrame, transaction_type: str,
                filename: str, price_label: str = "price"):
    if uplift_df.empty:
        print(f"   No uplift data for {transaction_type} — skipping chart")
        return

    fig, ax = plt.subplots(figsize=(9, max(5, len(uplift_df) * 0.45 + 1)))

    colors = [COLOR_TEAL if v >= 0 else COLOR_CORAL for v in uplift_df["uplift_pct"]]

    bars = ax.barh(
        uplift_df["feature"],
        uplift_df["uplift_pct"],
        color=colors,
        height=0.6,
    )

    # Zero reference line
    ax.axvline(0, color="#888780", linewidth=1.2, linestyle="-")

    # Annotate each bar
    for bar, row in zip(bars, uplift_df.itertuples()):
        sign   = "+" if row.uplift_pct >= 0 else ""
        label  = f"{sign}{row.uplift_pct:.1f}%  (n={row.n_with:,})"
        x_pos  = row.uplift_pct + (1.5 if row.uplift_pct >= 0 else -1.5)
        ha     = "left" if row.uplift_pct >= 0 else "right"
        ax.text(
            x_pos,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha=ha,
            fontsize=8.5,
            color="#333330",
        )

    ax.set_xlabel("Median price difference vs listings without this feature (%)", fontsize=9.5)
    ax.set_title(
        f"Feature price uplift — {transaction_type} ({price_label})\n"
        f"(residential, non-outlier listings | min {MIN_LISTINGS} listings per feature)",
        fontsize=12,
        fontweight="bold",
    )

    # Legend
    pos_patch = mpatches.Patch(color=COLOR_TEAL,  label="Premium feature")
    neg_patch = mpatches.Patch(color=COLOR_CORAL, label="Discount feature")
    ax.legend(handles=[pos_patch, neg_patch], loc="lower right", fontsize=9, frameon=False)

    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Extend x-axis so labels don't clip
    x_min = uplift_df["uplift_pct"].min()
    x_max = uplift_df["uplift_pct"].max()
    ax.set_xlim(x_min * 1.45 if x_min < 0 else -15,
                x_max * 1.45 if x_max > 0 else 15)

    fig.tight_layout()
    fig.savefig(FIGURES_PATH / filename)
    plt.close(fig)
    print(f"   Saved {filename}")

plot_uplift(uplift_sale,   "sale",   "05_02a_price_uplift_sale.png",   "asking price")
plot_uplift(uplift_rental, "rental", "05_02b_price_uplift_rental.png", "monthly rent")

# =============================================================================
# FIGURE 3 — Feature frequency by region (heatmap)
# Top 8 regions × top 12 features most present in those regions.
# Cell value: % of residential listings in that region that have the feature.
# =============================================================================

print("[3/3] Feature frequency heatmap by region...")

HEATMAP_FEATURES = [
    "elevator",
    "furnished",
    "with parking space",
    "with garage",
    "air conditioning",
    "insulated/renovated",
    "gated complex",
    "alarm system",
    "video surveillance",
    "luxury",
    "needs renovation",
    "underground parking",
]

# Filter to top regions and target features
pf_region = pf_clean[
    pf_clean["region_en"].isin(TOP_REGIONS) &
    pf_clean["name_en"].isin(HEATMAP_FEATURES)
].copy()

# Count of distinct properties per (region, feature)
feat_region_counts = (
    pf_region.groupby(["region_en", "name_en"])["property_id"]
    .nunique()
    .reset_index(name="n_with")
)

# Total residential listings per region (denominator)
region_totals = (
    res_clean[res_clean["region_en"].isin(TOP_REGIONS)]
    .groupby("region_en")["property_id"]
    .nunique()
    .rename("n_total")
    .reset_index()
)

feat_region_counts = feat_region_counts.merge(region_totals, on="region_en", how="left")
feat_region_counts["pct"] = (
    feat_region_counts["n_with"] / feat_region_counts["n_total"] * 100
).round(1)

# Pivot to matrix: rows = regions (sorted by listing volume), cols = features
pivot = feat_region_counts.pivot_table(
    index="region_en", columns="name_en", values="pct", fill_value=0.0
)

# Order regions by listing volume (descending) and features by mean frequency
region_order = (
    region_totals.sort_values("n_total", ascending=False)["region_en"].tolist()
)
# Keep only regions that appear in the pivot
region_order = [r for r in region_order if r in pivot.index]

feature_order = (
    pivot.reindex(region_order)
    .mean()
    .sort_values(ascending=False)
    .index.tolist()
)
# Keep only features that appear in the pivot
feature_order = [f for f in HEATMAP_FEATURES if f in pivot.columns]

pivot = pivot.reindex(index=region_order, columns=feature_order)

fig, ax = plt.subplots(figsize=(13, 5.5))

sns.heatmap(
    pivot,
    ax=ax,
    annot=True,
    fmt=".0f",
    cmap="Blues",
    linewidths=0.4,
    linecolor="#e0e0e0",
    cbar_kws={"label": "% of listings in region", "shrink": 0.7},
    annot_kws={"size": 9},
)

ax.set_title(
    "Feature frequency by region — % of residential listings\n"
    "(top 8 regions by listing volume, outliers excluded)",
    fontsize=12,
    fontweight="bold",
    pad=14,
)
ax.set_xlabel("Feature", fontsize=10)
ax.set_ylabel("Region", fontsize=10)
ax.tick_params(axis="x", rotation=35, labelsize=9)
ax.tick_params(axis="y", rotation=0,  labelsize=9)

# Annotate region listing totals on the y-axis
for i, region in enumerate(pivot.index):
    total = region_totals.set_index("region_en").loc[region, "n_total"]
    ax.text(
        -0.35,
        i + 0.5,
        f"n={total:,}",
        va="center",
        ha="right",
        fontsize=8,
        color="#666663",
        transform=ax.get_yaxis_transform(),
    )

fig.tight_layout()
fig.savefig(FIGURES_PATH / "05_03_feature_frequency_by_region.png")
plt.close(fig)
print("   Saved 05_03_feature_frequency_by_region.png")

# =============================================================================
# SUMMARY STATS — key findings to feed findings.md
# =============================================================================

print("\n=== KEY FINDINGS — FEATURES ANALYSIS ===")

# Top amenity
top_feat  = feature_counts.index[0]
top_pct   = feature_pct.iloc[0]
print(f"Most advertised amenity: {top_feat!r} ({top_pct}% of clean residential listings)")

# Top 5 amenities
print("\nTop 5 amenities:")
for feat, pct in feature_pct.head(5).items():
    print(f"  {feat:<30} {pct:.1f}%")

# Biggest uplift — sale
if not uplift_sale.empty:
    top_sale = uplift_sale.iloc[0]
    print(f"\nBiggest sale price uplift:  {top_sale['feature']!r}  "
          f"+{top_sale['uplift_pct']:.1f}%  (n={top_sale['n_with']:,})")
    bot_sale = uplift_sale.iloc[-1]
    print(f"Biggest sale price discount: {bot_sale['feature']!r}  "
          f"{bot_sale['uplift_pct']:.1f}%  (n={bot_sale['n_with']:,})")

# Biggest uplift — rental
if not uplift_rental.empty:
    top_rent = uplift_rental.iloc[0]
    print(f"\nBiggest rental price uplift: {top_rent['feature']!r}  "
          f"+{top_rent['uplift_pct']:.1f}%  (n={top_rent['n_with']:,})")
    bot_rent = uplift_rental.iloc[-1]
    print(f"Biggest rental price discount: {bot_rent['feature']!r}  "
          f"{bot_rent['uplift_pct']:.1f}%  (n={bot_rent['n_with']:,})")

# Furnished: sale vs rental comparison
for tx, uplift_df in [("sale", uplift_sale), ("rental", uplift_rental)]:
    if not uplift_df.empty and "furnished" in uplift_df["feature"].values:
        row = uplift_df[uplift_df["feature"] == "furnished"].iloc[0]
        print(f"\nFurnished uplift ({tx}): +{row['uplift_pct']:.1f}%  "
              f"(median with: €{row['median_with']:,.0f}  |  "
              f"without: €{row['median_without']:,.0f})")

print(f"\nFigures saved to: {FIGURES_PATH}/")
print("\n05_features_analysis.py complete.")
