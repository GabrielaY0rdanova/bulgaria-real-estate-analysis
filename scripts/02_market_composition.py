# =============================================================================
# bulgaria-real-estate-analysis — Market Composition
# Source: data/df_analysis.pkl (output of 01_load.py)
# Purpose: Analyse the structure of the Bulgarian property market —
#          what is being sold, by whom, and in what transaction form.
# Script:  02
# Run after: 01_load.py
# Outputs: outputs/figures/02_*.png
# =============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# =============================================================================
# CONFIG
# =============================================================================

DATA_PATH    = Path("data/df_analysis.pkl")
FIGURES_PATH = Path("outputs/figures")
FIGURES_PATH.mkdir(parents=True, exist_ok=True)

# Shared style
PALETTE_CAT  = "#378ADD"   # blue  — primary bars
PALETTE_CAT2 = "#1D9E75"   # teal  — secondary / accent
PALETTE_WARN = "#BA7517"   # amber — highlights

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

# =============================================================================
# FIGURE 1 — Listing count by property category
# Donut chart: residential / land / commercial / industrial / parking
# =============================================================================

print("\n[1/4] Property category breakdown...")

category_counts = df["property_type_category"].value_counts()

CATEGORY_COLORS = {
    "residential": "#378ADD",
    "land":        "#1D9E75",
    "commercial":  "#BA7517",
    "industrial":  "#888780",
    "parking":     "#D4537E",
}
colors = [CATEGORY_COLORS.get(c, "#888780") for c in category_counts.index]

fig, ax = plt.subplots(figsize=(7, 5))

wedges, texts, autotexts = ax.pie(
    category_counts,
    labels=None,
    autopct="%1.1f%%",
    startangle=90,
    colors=colors,
    wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 1.5},
    pctdistance=0.78,
)
for at in autotexts:
    at.set_fontsize(10)
    at.set_color("white")
    at.set_fontweight("bold")

ax.legend(
    wedges,
    [f"{c.capitalize()}  ({v:,})" for c, v in zip(category_counts.index, category_counts)],
    loc="center left",
    bbox_to_anchor=(0.88, 0.5),
    fontsize=10,
    frameon=False,
)
ax.set_title("Listings by property category", fontsize=13, fontweight="bold", pad=16)
fig.tight_layout()
fig.savefig(FIGURES_PATH / "02_01_category_breakdown.png")
plt.close(fig)
print("   Saved 02_01_category_breakdown.png")

# =============================================================================
# FIGURE 2 — Top 15 property types by listing count (horizontal bar)
# =============================================================================

print("[2/4] Top property types...")

top_types = df["property_type_en"].value_counts().head(15)

fig, ax = plt.subplots(figsize=(8, 6))

bars = ax.barh(
    top_types.index[::-1],
    top_types.values[::-1],
    color=PALETTE_CAT,
    height=0.65,
)

# Annotate bars with count
for bar, val in zip(bars, top_types.values[::-1]):
    ax.text(
        bar.get_width() + 500,
        bar.get_y() + bar.get_height() / 2,
        f"{val:,}",
        va="center",
        fontsize=9,
        color="#444441",
    )

ax.set_xlabel("Number of listings", fontsize=10)
ax.set_title("Top 15 property types by listing volume", fontsize=13, fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_xlim(0, top_types.max() * 1.15)
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "02_02_top_property_types.png")
plt.close(fig)
print("   Saved 02_02_top_property_types.png")

# =============================================================================
# FIGURE 3 — Sale vs rental split, overall and by category
# Side-by-side: overall donut + stacked bar by category
# =============================================================================

print("[3/4] Sale vs rental split...")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# --- Left: overall donut ---
tx_counts = df["transaction_type"].value_counts()
tx_colors = [PALETTE_CAT, PALETTE_CAT2]

wedges, _, autotexts = axes[0].pie(
    tx_counts,
    labels=None,
    autopct="%1.1f%%",
    startangle=90,
    colors=tx_colors,
    wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2},
    pctdistance=0.78,
)
for at in autotexts:
    at.set_fontsize(11)
    at.set_color("white")
    at.set_fontweight("bold")

axes[0].legend(
    wedges,
    [f"{t.capitalize()}  ({v:,})" for t, v in zip(tx_counts.index, tx_counts)],
    loc="lower center",
    bbox_to_anchor=(0.5, -0.08),
    fontsize=10,
    frameon=False,
    ncol=2,
)
axes[0].set_title("Overall sale vs rental", fontsize=12, fontweight="bold")

# --- Right: stacked bar by category ---
cat_tx = (
    df.groupby(["property_type_category", "transaction_type"])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=["sale", "rental"])
)
cat_tx = cat_tx.sort_values("sale", ascending=True)
cat_tx_pct = cat_tx.div(cat_tx.sum(axis=1), axis=0) * 100

cat_tx_pct.plot(
    kind="barh",
    stacked=True,
    ax=axes[1],
    color=[PALETTE_CAT, PALETTE_CAT2],
    width=0.6,
    legend=False,
)

# Annotate with raw counts
for i, (cat, row) in enumerate(cat_tx.iterrows()):
    total = row.sum()
    axes[1].text(
        50,
        i,
        f"Sale: {int(row['sale']):,}   Rental: {int(row.get('rental', 0)):,}",
        va="center",
        fontsize=8.5,
        color="white",
        fontweight="bold",
    )

axes[1].set_xlabel("Share (%)", fontsize=10)
axes[1].set_title("Sale vs rental by property category", fontsize=12, fontweight="bold")
axes[1].set_xlim(0, 100)
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))
axes[1].legend(
    ["Sale", "Rental"],
    loc="lower right",
    fontsize=9,
    frameon=False,
)
axes[1].grid(axis="x", alpha=0.3, linestyle="--")
axes[1].set_axisbelow(True)

fig.suptitle("Market split: sale vs rental", fontsize=14, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(FIGURES_PATH / "02_03_sale_vs_rental.png")
plt.close(fig)
print("   Saved 02_03_sale_vs_rental.png")

# =============================================================================
# FIGURE 4 — Agency vs owner split by top 10 regions
# 100% stacked horizontal bar
# =============================================================================

print("[4/4] Agency vs owner by region...")

top_regions = df["region_en"].value_counts().head(10).index

region_contact = (
    df[df["region_en"].isin(top_regions)]
    .groupby(["region_en", "contact_type"])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=["agency", "owner"])
)

# Sort by owner % descending (most owner-driven markets at top)
region_contact["owner_pct"] = region_contact["owner"] / region_contact.sum(axis=1) * 100
region_contact = region_contact.sort_values("owner_pct", ascending=True)
region_contact_pct = region_contact[["agency", "owner"]].div(
    region_contact[["agency", "owner"]].sum(axis=1), axis=0
) * 100

fig, ax = plt.subplots(figsize=(9, 5.5))

region_contact_pct.plot(
    kind="barh",
    stacked=True,
    ax=ax,
    color=[PALETTE_CAT, PALETTE_WARN],
    width=0.65,
    legend=False,
)

# Annotate with owner % on the right
for i, (region, row) in enumerate(region_contact.iterrows()):
    owner_pct = row["owner_pct"]
    total     = int(row["agency"] + row["owner"])
    ax.text(
        101,
        i,
        f"{owner_pct:.1f}% owner",
        va="center",
        fontsize=8.5,
        color="#444441",
    )
    ax.text(
        50,
        i,
        f"{total:,} listings",
        va="center",
        fontsize=8,
        color="white",
        fontweight="bold",
        ha="center",
    )

ax.set_xlabel("Share (%)", fontsize=10)
ax.set_title("Agency vs owner listings — top 10 regions", fontsize=13, fontweight="bold")
ax.set_xlim(0, 118)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))
ax.legend(
    ["Agency", "Owner"],
    loc="lower right",
    fontsize=9,
    frameon=False,
)
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

fig.tight_layout()
fig.savefig(FIGURES_PATH / "02_04_agency_vs_owner.png")
plt.close(fig)
print("   Saved 02_04_agency_vs_owner.png")

# =============================================================================
# SUMMARY STATS — print key findings
# =============================================================================

print("\n=== KEY FINDINGS — MARKET COMPOSITION ===")

total = len(df)
sales   = (df["transaction_type"] == "sale").sum()
rentals = (df["transaction_type"] == "rental").sum()
agency  = (df["contact_type"] == "agency").sum()
owner   = (df["contact_type"] == "owner").sum()
res     = (df["property_type_category"] == "residential").sum()

print(f"Total listings:        {total:,}")
print(f"Sales:                 {sales:,}  ({sales/total*100:.1f}%)")
print(f"Rentals:               {rentals:,}  ({rentals/total*100:.1f}%)")
print(f"Agency listings:       {agency:,}  ({agency/total*100:.1f}%)")
print(f"Owner listings:        {owner:,}   ({owner/total*100:.1f}%)")
print(f"Residential listings:  {res:,}  ({res/total*100:.1f}%)")
print(f"\nTop property type:     apartment ({df['property_type_en'].value_counts().iloc[0]:,} listings)")
print(f"\nFigures saved to:      {FIGURES_PATH}/")
print("\n02_market_composition.py complete.")
