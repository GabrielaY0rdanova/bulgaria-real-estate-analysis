# =============================================================================
# bulgaria-real-estate-analysis — Geographic Story
# Source: data/df_analysis.pkl (output of 01_load.py)
# Purpose: Tell the geographic price story — how the market differs across
#          Bulgaria's 27 regions, which cities dominate, and how large the
#          Sofia premium is relative to the rest of the country.
# Script:  04
# Run after: 01_load.py
# Outputs: outputs/figures/04_*.png
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
FIGURES_PATH = Path("outputs/figures")
FIGURES_PATH.mkdir(parents=True, exist_ok=True)

COLOR_SALE      = "#378ADD"   # blue  — sale prices
COLOR_RENTAL    = "#1D9E75"   # teal  — rental prices
COLOR_SOFIA     = "#D85A30"   # coral — Sofia highlight
COLOR_OTHER     = "#B5D4F4"   # light blue — other regions
COLOR_ACCENT    = "#BA7517"   # amber — secondary accent

TOP_CITIES = ["Sofiya", "Varna", "Plovdiv", "Burgas", "Stara Zagora"]

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
print(f"Loaded: {len(df):,} rows × {df.shape[1]} columns")

sales   = df[df["transaction_type"] == "sale"].copy()
rentals = df[df["transaction_type"] == "rental"].copy()

# =============================================================================
# FIGURE 1 — Median sale price by region (all 27 regions)
# Sofia highlighted in coral; all others in light blue.
# =============================================================================

print("\n[1/4] Median sale price by region...")

region_sale = (
    sales.groupby("region_en")["price"]
    .agg(median="median", count="count")
    .sort_values("median", ascending=True)
)

colors = [
    COLOR_SOFIA if r == "Sofiya" else COLOR_SALE
    for r in region_sale.index
]

fig, ax = plt.subplots(figsize=(9, 9))

bars = ax.barh(
    region_sale.index,
    region_sale["median"],
    color=colors,
    height=0.65,
)

# Annotate bars
for bar, (region, row) in zip(bars, region_sale.iterrows()):
    ax.text(
        bar.get_width() + 2_000,
        bar.get_y() + bar.get_height() / 2,
        f"€{row['median']:,.0f}",
        va="center",
        fontsize=8.5,
        color="#444441",
        fontweight="bold" if region == "Sofiya" else "normal",
    )

# National median line
national_median = sales["price"].median()
ax.axvline(
    national_median,
    color="#888780",
    linestyle="--",
    linewidth=1.2,
    label=f"National median  €{national_median:,.0f}",
    zorder=3,
)

ax.set_xlabel("Median asking price (€)", fontsize=10)
ax.set_title("Median sale price by region", fontsize=13, fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{int(x):,}"))
ax.set_xlim(0, region_sale["median"].max() * 1.22)
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

sofia_patch  = mpatches.Patch(color=COLOR_SOFIA, label="Sofia")
other_patch  = mpatches.Patch(color=COLOR_SALE,  label="Other regions")
nat_line     = plt.Line2D([0], [0], color="#888780", linestyle="--",
                          label=f"National median  €{national_median:,.0f}")
ax.legend(handles=[sofia_patch, other_patch, nat_line],
          fontsize=9, frameon=False, loc="lower right")

fig.tight_layout()
fig.savefig(FIGURES_PATH / "04_01_median_price_by_region.png")
plt.close(fig)
print("   Saved 04_01_median_price_by_region.png")

# =============================================================================
# FIGURE 2 — Sofia premium: how many times more expensive than every region
# Diverging bar from 1× baseline, showing the multiplier per region.
# =============================================================================

print("[2/4] Sofia premium chart...")

sofia_median = sales[sales["region_en"] == "Sofiya"]["price"].median()

region_premium = (
    sales.groupby("region_en")["price"]
    .median()
    .drop("Sofiya")                          # exclude Sofia from the comparison
    .apply(lambda m: sofia_median / m)
    .sort_values(ascending=True)
)

fig, ax = plt.subplots(figsize=(8, 8))

bar_colors = [
    COLOR_SOFIA if v >= 3.0 else
    COLOR_SALE  if v >= 2.0 else
    COLOR_OTHER
    for v in region_premium.values
]

bars = ax.barh(
    region_premium.index,
    region_premium.values,
    color=bar_colors,
    height=0.65,
)

# 1× reference line
ax.axvline(1, color="#888780", linestyle="--", linewidth=1.0)

# Annotate multiplier
for bar, val in zip(bars, region_premium.values):
    ax.text(
        bar.get_width() + 0.03,
        bar.get_y() + bar.get_height() / 2,
        f"{val:.1f}×",
        va="center",
        fontsize=9,
        color="#444441",
    )

ax.set_xlabel("Sofia median price ÷ region median price", fontsize=10)
ax.set_title(
    f"The Sofia premium\nSofia median (€{sofia_median:,.0f}) vs every other region",
    fontsize=12,
    fontweight="bold",
)
ax.set_xlim(0, region_premium.max() * 1.18)
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

high_patch = mpatches.Patch(color=COLOR_SOFIA, label="3× or more")
mid_patch  = mpatches.Patch(color=COLOR_SALE,  label="2–3×")
low_patch  = mpatches.Patch(color=COLOR_OTHER, label="Below 2×")
ax.legend(handles=[high_patch, mid_patch, low_patch],
          title="Sofia premium", fontsize=9, frameon=False)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "04_02_sofia_premium.png")
plt.close(fig)
print("   Saved 04_02_sofia_premium.png")

# =============================================================================
# FIGURE 3 — Top 5 cities: sale price, rental price, listing volume
# Three-panel layout: listing volume | median sale price | median rental price
# =============================================================================

print("[3/4] Top 5 cities comparison...")

city_stats = []
for city in TOP_CITIES:
    city_sale   = sales[sales["locality_en"] == city]["price"].dropna()
    city_rental = rentals[rentals["locality_en"] == city]["price"].dropna()
    total       = len(df[df["locality_en"] == city])
    city_stats.append({
        "city":          city,
        "total":         total,
        "sale_median":   city_sale.median(),
        "rental_median": city_rental.median(),
        "rental_share":  len(city_rental) / total * 100,
    })

city_df = pd.DataFrame(city_stats).set_index("city")

fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

city_colors = [COLOR_SOFIA if c == "Sofiya" else COLOR_SALE for c in city_df.index]

# Panel A — listing volume
axes[0].barh(city_df.index[::-1], city_df["total"][::-1],
             color=city_colors[::-1], height=0.6)
for i, (city, row) in enumerate(city_df[::-1].iterrows()):
    axes[0].text(row["total"] + 200, i,
                 f"{row['total']:,}", va="center", fontsize=9)
axes[0].set_title("Total listings", fontsize=11, fontweight="bold")
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
axes[0].set_xlim(0, city_df["total"].max() * 1.2)
axes[0].grid(axis="x", alpha=0.3, linestyle="--")
axes[0].set_axisbelow(True)

# Panel B — median sale price
axes[1].barh(city_df.index[::-1], city_df["sale_median"][::-1],
             color=city_colors[::-1], height=0.6)
for i, (city, row) in enumerate(city_df[::-1].iterrows()):
    axes[1].text(row["sale_median"] + 1_500, i,
                 f"€{row['sale_median']:,.0f}", va="center", fontsize=9)
axes[1].set_title("Median sale price", fontsize=11, fontweight="bold")
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{int(x):,}"))
axes[1].set_xlim(0, city_df["sale_median"].max() * 1.22)
axes[1].set_yticklabels([])
axes[1].grid(axis="x", alpha=0.3, linestyle="--")
axes[1].set_axisbelow(True)

# Panel C — median rental price
axes[2].barh(city_df.index[::-1], city_df["rental_median"][::-1],
             color=[COLOR_SOFIA if c == "Sofiya" else COLOR_RENTAL
                    for c in city_df.index[::-1]],
             height=0.6)
for i, (city, row) in enumerate(city_df[::-1].iterrows()):
    axes[2].text(row["rental_median"] + 8, i,
                 f"€{row['rental_median']:,.0f}/mo", va="center", fontsize=9)
axes[2].set_title("Median rental price", fontsize=11, fontweight="bold")
axes[2].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{int(x):,}"))
axes[2].set_xlim(0, city_df["rental_median"].max() * 1.28)
axes[2].set_yticklabels([])
axes[2].grid(axis="x", alpha=0.3, linestyle="--")
axes[2].set_axisbelow(True)

fig.suptitle("Top 5 cities by listing volume", fontsize=13, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(FIGURES_PATH / "04_03_top_cities.png")
plt.close(fig)
print("   Saved 04_03_top_cities.png")

# =============================================================================
# FIGURE 4 — Apartment €/m² by region (top 10 regions)
# Apartments only — apples-to-apples comparison across regions.
# =============================================================================

print("[4/4] Apartment €/m² by region...")

top_regions = df["region_en"].value_counts().head(10).index

apt_ppm2 = (
    sales[
        (sales["property_type_en"] == "apartment") &
        sales["price_per_m2"].notna() &
        sales["region_en"].isin(top_regions)
    ]
    .groupby("region_en")["price_per_m2"]
    .agg(
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
        count="count",
    )
    .sort_values("median", ascending=True)
)

colors = [COLOR_SOFIA if r == "Sofiya" else COLOR_SALE for r in apt_ppm2.index]

fig, ax = plt.subplots(figsize=(9, 5.5))

bars = ax.barh(apt_ppm2.index, apt_ppm2["median"], color=colors, height=0.65)

# IQR whiskers
for i, (region, row) in enumerate(apt_ppm2.iterrows()):
    ax.plot([row["q25"], row["q75"]], [i, i],
            color="#444441", linewidth=1.5, solid_capstyle="round")
    ax.plot(row["q25"], i, "|", color="#444441", markersize=5)
    ax.plot(row["q75"], i, "|", color="#444441", markersize=5)

# Annotate median
for bar, val in zip(bars, apt_ppm2["median"]):
    ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height() / 2,
            f"€{val:,.0f}/m²", va="center", fontsize=9, color="#444441")

ax.set_xlabel("Median €/m²  (bars = median, lines = IQR)", fontsize=10)
ax.set_title("Apartment €/m² by region — top 10 regions by listing volume\n(sales only)",
             fontsize=12, fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{int(x):,}"))
ax.set_xlim(0, apt_ppm2["q75"].max() * 1.25)
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

sofia_patch = mpatches.Patch(color=COLOR_SOFIA, label="Sofia")
other_patch = mpatches.Patch(color=COLOR_SALE,  label="Other regions")
ax.legend(handles=[sofia_patch, other_patch], fontsize=9, frameon=False)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "04_04_apt_ppm2_by_region.png")
plt.close(fig)
print("   Saved 04_04_apt_ppm2_by_region.png")

# =============================================================================
# SUMMARY STATS
# =============================================================================

print("\n=== KEY FINDINGS — GEOGRAPHIC STORY ===")

national_median = sales["price"].median()
sofia_median    = sales[sales["region_en"] == "Sofiya"]["price"].median()
cheapest_region = region_sale["median"].idxmin()
cheapest_med    = region_sale["median"].min()

print(f"National median sale price:  €{national_median:,.0f}")
print(f"Sofia median sale price:     €{sofia_median:,.0f}  ({sofia_median/national_median:.1f}× national median)")
print(f"Most expensive region:       Sofia  (€{sofia_median:,.0f})")
print(f"Least expensive region:      {cheapest_region}  (€{cheapest_med:,.0f})")
print(f"Sofia vs {cheapest_region}:         {sofia_median/cheapest_med:.1f}× more expensive")
print(f"\nTop 5 cities:")
for _, row in city_df.iterrows():
    print(f"  {row.name:<16} listings={row['total']:,}  "
          f"sale=€{row['sale_median']:,.0f}  rental=€{row['rental_median']:,.0f}/mo")
print(f"\nApartment €/m² — Sofia: €{apt_ppm2.loc['Sofiya','median']:,.0f}  "
      f"vs national top-10 avg: €{apt_ppm2['median'].mean():,.0f}")
print(f"\nFigures saved to: {FIGURES_PATH}/")
print("\n04_geographic_story.py complete.")
