# =============================================================================
# bulgaria-real-estate-analysis — Price Landscape
# Source: data/df_analysis.pkl (output of 01_load.py)
# Purpose: Analyse asking price distributions across transaction types and
#          property types. Covers headline stats, price brackets, €/m²,
#          and the impact of outliers on mean vs median.
# Script:  03
# Run after: 01_load.py
# Outputs: outputs/figures/03_*.png
# =============================================================================

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# =============================================================================
# CONFIG
# =============================================================================

DATA_PATH    = Path("data/df_analysis.pkl")
FIGURES_PATH = Path("outputs/figures")
FIGURES_PATH.mkdir(parents=True, exist_ok=True)

COLOR_SALE   = "#378ADD"   # blue
COLOR_RENTAL = "#1D9E75"   # teal
COLOR_ACCENT = "#BA7517"   # amber — highlights / mean line

plt.rcParams.update({
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
    "font.family":       "sans-serif",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "axes.grid.axis":    "y",
    "grid.alpha":        0.3,
    "grid.linestyle":    "--",
})

# =============================================================================
# LOAD
# =============================================================================

df = pd.read_pickle(DATA_PATH)
print(f"Loaded: {len(df):,} rows × {df.shape[1]} columns")

sales   = df[df["transaction_type"] == "sale"].copy()
rentals = df[df["transaction_type"] == "rental"].copy()

# =============================================================================
# FIGURE 1 — Sale price distribution: bracket histogram
# Clipped at p99 (€2M) to keep the chart readable.
# Outliers above p99 annotated as a note.
# =============================================================================

print("\n[1/4] Sale price bracket distribution...")

sale_prices = sales["price"].dropna()
P99_SALE    = sale_prices.quantile(0.99)     # ~2M
above_p99   = (sale_prices > P99_SALE).sum()

brackets = [0, 50_000, 100_000, 150_000, 200_000, 300_000, 500_000, 1_000_000, P99_SALE]
labels   = ["<50k", "50–100k", "100–150k", "150–200k",
            "200–300k", "300–500k", "500k–1M", "1M–2M"]

clipped      = sale_prices[sale_prices <= P99_SALE]
bracket_cuts = pd.cut(clipped, bins=brackets, labels=labels, include_lowest=True)
bracket_counts = bracket_cuts.value_counts().reindex(labels)

fig, ax = plt.subplots(figsize=(10, 5))

bars = ax.bar(
    labels,
    bracket_counts.values,
    color=COLOR_SALE,
    width=0.7,
    edgecolor="white",
    linewidth=0.5,
)

# Annotate each bar with count
for bar, val in zip(bars, bracket_counts.values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 200,
        f"{int(val):,}",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="#444441",
    )

# Median and mean lines
median_sale = sale_prices.median()
mean_sale   = sale_prices.mean()

# Map price values to approximate bar positions
def price_to_x(price, labels, brackets):
    for i, (lo, hi) in enumerate(zip(brackets[:-1], brackets[1:])):
        if lo <= price <= hi:
            frac = (price - lo) / (hi - lo)
            return i + frac - 0.5
    return None

median_x = price_to_x(median_sale, labels, brackets)
mean_x   = price_to_x(sale_prices[sale_prices <= P99_SALE].mean(), labels, brackets) \
           if mean_sale <= P99_SALE else None

ax.axvline(median_x, color=COLOR_SALE, linestyle="--", linewidth=1.5,
           label=f"Median  €{median_sale:,.0f}")
if mean_x:
    ax.axvline(mean_x, color=COLOR_ACCENT, linestyle="--", linewidth=1.5,
               label=f"Mean  €{mean_sale:,.0f}")

ax.set_xlabel("Asking price (€)", fontsize=10)
ax.set_ylabel("Number of listings", fontsize=10)
ax.set_title("Sale price distribution", fontsize=13, fontweight="bold")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.tick_params(axis="x", labelsize=9)
ax.legend(fontsize=9, frameon=False)

ax.text(
    0.98, 0.97,
    f"{above_p99:,} listings above €2M excluded from chart",
    transform=ax.transAxes,
    ha="right", va="top",
    fontsize=8,
    color="#888780",
    style="italic",
)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "03_01_sale_price_distribution.png")
plt.close(fig)
print("   Saved 03_01_sale_price_distribution.png")

# =============================================================================
# FIGURE 2 — Rental price distribution: bracket histogram
# =============================================================================

print("[2/4] Rental price distribution...")

rent_prices = rentals["price"].dropna()
P99_RENT    = rent_prices.quantile(0.99)    # ~8,786
above_p99r  = (rent_prices > P99_RENT).sum()

rent_brackets = [0, 200, 400, 600, 800, 1_000, 1_500, 2_000, P99_RENT]
rent_labels   = ["<200", "200–400", "400–600", "600–800",
                 "800–1k", "1k–1.5k", "1.5k–2k", "2k–9k"]

clipped_r       = rent_prices[rent_prices <= P99_RENT]
rent_cuts       = pd.cut(clipped_r, bins=rent_brackets, labels=rent_labels, include_lowest=True)
rent_counts     = rent_cuts.value_counts().reindex(rent_labels)

fig, ax = plt.subplots(figsize=(10, 5))

bars = ax.bar(
    rent_labels,
    rent_counts.values,
    color=COLOR_RENTAL,
    width=0.7,
    edgecolor="white",
    linewidth=0.5,
)

for bar, val in zip(bars, rent_counts.values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 30,
        f"{int(val):,}",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="#444441",
    )

median_rent = rent_prices.median()
mean_rent   = rent_prices.mean()

def price_to_x_r(price, brackets):
    for i, (lo, hi) in enumerate(zip(brackets[:-1], brackets[1:])):
        if lo <= price <= hi:
            frac = (price - lo) / (hi - lo)
            return i + frac - 0.5
    return None

median_rx = price_to_x_r(median_rent, rent_brackets)
mean_rx   = price_to_x_r(mean_rent,   rent_brackets)

if median_rx is not None:
    ax.axvline(median_rx, color=COLOR_RENTAL, linestyle="--", linewidth=1.5,
               label=f"Median  €{median_rent:,.0f}/mo")
if mean_rx is not None:
    ax.axvline(mean_rx, color=COLOR_ACCENT, linestyle="--", linewidth=1.5,
               label=f"Mean  €{mean_rent:,.0f}/mo")

ax.set_xlabel("Monthly rent (€)", fontsize=10)
ax.set_ylabel("Number of listings", fontsize=10)
ax.set_title("Rental price distribution", fontsize=13, fontweight="bold")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.tick_params(axis="x", labelsize=9)
ax.legend(fontsize=9, frameon=False)

ax.text(
    0.98, 0.97,
    f"{above_p99r:,} listings above €{P99_RENT:,.0f}/mo excluded from chart",
    transform=ax.transAxes,
    ha="right", va="top",
    fontsize=8,
    color="#888780",
    style="italic",
)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "03_02_rental_price_distribution.png")
plt.close(fig)
print("   Saved 03_02_rental_price_distribution.png")

# =============================================================================
# FIGURE 3 — Median €/m² by property type (sale)
# Excludes plots and agricultural land — their €/m² is orders of magnitude
# lower than built property and would collapse the scale.
# =============================================================================

print("[3/4] €/m² by property type (sale)...")

EXCLUDE_TYPES = {"plot", "agricultural land", "farm", "solar park"}

sale_ppm2 = sales[
    sales["price_per_m2"].notna() &
    ~sales["property_type_en"].isin(EXCLUDE_TYPES)
].copy()

# Keep types with at least 100 observations
type_counts = sale_ppm2["property_type_en"].value_counts()
valid_types = type_counts[type_counts >= 100].index

ppm2_stats = (
    sale_ppm2[sale_ppm2["property_type_en"].isin(valid_types)]
    .groupby("property_type_en")["price_per_m2"]
    .agg(
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
        count="count",
    )
    .sort_values("median", ascending=True)
)

fig, ax = plt.subplots(figsize=(9, 7))

colors = [COLOR_SALE if m >= 1_000 else "#B5D4F4" for m in ppm2_stats["median"]]

bars = ax.barh(
    ppm2_stats.index,
    ppm2_stats["median"],
    color=colors,
    height=0.65,
)

# IQR whiskers
for i, (idx, row) in enumerate(ppm2_stats.iterrows()):
    ax.plot(
        [row["q25"], row["q75"]],
        [i, i],
        color="#444441",
        linewidth=1.5,
        solid_capstyle="round",
    )
    ax.plot(row["q25"], i, "|", color="#444441", markersize=6)
    ax.plot(row["q75"], i, "|", color="#444441", markersize=6)

# Annotate with median value
for bar, val in zip(bars, ppm2_stats["median"]):
    ax.text(
        bar.get_width() + 30,
        bar.get_y() + bar.get_height() / 2,
        f"€{val:,.0f}",
        va="center",
        fontsize=9,
        color="#444441",
    )

ax.set_xlabel("Median €/m²  (bars = median, lines = IQR)", fontsize=10)
ax.set_title("Median price per m² by property type — sales only\n(plots and agricultural land excluded)",
             fontsize=12, fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{int(x):,}"))
ax.set_xlim(0, ppm2_stats["q75"].max() * 1.25)
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "03_03_price_per_m2_by_type.png")
plt.close(fig)
print("   Saved 03_03_price_per_m2_by_type.png")

# =============================================================================
# FIGURE 4 — Mean vs median: outlier impact panel
# Shows how heavily the mean is skewed by extreme listings.
# Side-by-side bars for mean vs median, sale and rental.
# =============================================================================

print("[4/4] Mean vs median — outlier impact...")

# Compute stats for key residential types (sale) + overall rental
FOCUS_TYPES = ["apartment", "house", "multi-room apartment", "maisonette", "villa"]

rows = []
for pt in FOCUS_TYPES:
    sub = sales[sales["property_type_en"] == pt]["price"].dropna()
    if len(sub) < 50:
        continue
    rows.append({
        "label":  pt.capitalize(),
        "median": sub.median(),
        "mean":   sub.mean(),
        "count":  len(sub),
        "skew":   sub.mean() / sub.median(),
    })

# Overall rental
rent_sub = rentals["price"].dropna()
rows.append({
    "label":  "All rentals",
    "median": rent_sub.median(),
    "mean":   rent_sub.mean(),
    "count":  len(rent_sub),
    "skew":   rent_sub.mean() / rent_sub.median(),
})

stats = pd.DataFrame(rows).set_index("label")

x     = np.arange(len(stats))
width = 0.38

fig, ax = plt.subplots(figsize=(10, 5))

bars_med = ax.bar(x - width / 2, stats["median"], width, label="Median",
                  color=COLOR_SALE, edgecolor="white")
bars_mean = ax.bar(x + width / 2, stats["mean"],   width, label="Mean",
                   color=COLOR_ACCENT, edgecolor="white")

# Annotate
for bar in bars_med:
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1_500,
            f"€{bar.get_height():,.0f}", ha="center", va="bottom",
            fontsize=8, color=COLOR_SALE, fontweight="bold")

for bar in bars_mean:
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1_500,
            f"€{bar.get_height():,.0f}", ha="center", va="bottom",
            fontsize=8, color=COLOR_ACCENT, fontweight="bold")

# Skew ratio annotation
for i, (label, row) in enumerate(stats.iterrows()):
    ax.text(i, max(row["median"], row["mean"]) + 18_000,
            f"mean/median: {row['skew']:.1f}×",
            ha="center", va="bottom", fontsize=7.5, color="#888780", style="italic")

ax.set_xticks(x)
ax.set_xticklabels(stats.index, fontsize=10)
ax.set_ylabel("Price (€)", fontsize=10)
ax.set_title("Mean vs median asking price — outlier impact\n(high mean/median ratio = heavy right skew from luxury listings)",
             fontsize=12, fontweight="bold")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{int(x):,}"))
ax.legend(fontsize=10, frameon=False)
ax.grid(axis="y", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "03_04_mean_vs_median.png")
plt.close(fig)
print("   Saved 03_04_mean_vs_median.png")

# =============================================================================
# SUMMARY STATS
# =============================================================================

print("\n=== KEY FINDINGS — PRICE LANDSCAPE ===")

sale_p  = sales["price"].dropna()
rent_p  = rentals["price"].dropna()
apt_p   = sales[sales["property_type_en"] == "apartment"]["price"].dropna()
apt_pm2 = sales[sales["property_type_en"] == "apartment"]["price_per_m2"].dropna()
house_p = sales[sales["property_type_en"] == "house"]["price"].dropna()

print(f"Sale   — median: €{sale_p.median():,.0f}  |  mean: €{sale_p.mean():,.0f}  |  mean/median: {sale_p.mean()/sale_p.median():.1f}×")
print(f"Rental — median: €{rent_p.median():,.0f}/mo  |  mean: €{rent_p.mean():,.0f}/mo  |  mean/median: {rent_p.mean()/rent_p.median():.1f}×")
print(f"Apartment sale  — median: €{apt_p.median():,.0f}  |  median €/m²: €{apt_pm2.median():,.0f}")
print(f"House sale      — median: €{house_p.median():,.0f}")
print(f"Listings with price on request: {sales['price_on_request'].sum():,} ({sales['price_on_request'].mean()*100:.1f}% of sales)")
print(f"\nFigures saved to: {FIGURES_PATH}/")
print("\n03_price_landscape.py complete.")
