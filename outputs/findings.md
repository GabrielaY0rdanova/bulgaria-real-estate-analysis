# findings.md — Bulgaria Real Estate Analysis
## Key Numbers & Insights

> Generated from `192,004` deduplicated listings scraped from imot.bg (April 2026).  
> Sales: `155,063` | Rentals: `36,941` | Regions covered: `27`

---

## 1. Market Composition

**What is being listed, and by whom.**

- **80.8% of all listings are sales** (155,063); rentals account for the remaining 19.2% (36,941).
- **94.2% of listings are posted by agencies** (180,897); owner-direct listings are a small minority at 5.8% (11,107). Agency dominance is consistent across all regions.
- **65.4% of listings are residential** (125,496). The remainder is commercial, land, industrial, and parking.
- **Apartments are by far the most listed property type** at 92,752 listings — nearly 3× the next largest type (plots at 34,979). The market is apartment-centric, reflecting Bulgaria's legacy of socialist-era panel-block construction.
- The top 4 apartment types (1-room through 4-room) together account for the majority of all residential supply.

> *"4 in 5 listings are for sale. 9 in 10 are posted by agencies. The market runs on apartments."*

---

## 2. Price Landscape

**What things cost, and how reliable those numbers are.**

### Sale prices

- **National median asking price: €135,000** — but the mean is €247,681 (1.8× the median). A small number of luxury and commercial listings pull the average up sharply. **Always use the median for Bulgarian property comparisons.**
- The **€50k–€100k bracket holds the most listings** — this is the core of the Bulgarian market, primarily smaller apartments in provincial cities.
- **Apartments** have a median sale price of **€144,900** and a median **€1,731/m²**.
- **Houses** sell at a median of **€130,000** — lower than apartments despite typically more space, reflecting their concentration outside major city centres.
- **Price on request** accounts for 2,364 listings (1.5% of sales) — mostly high-end commercial and luxury residential.
- Prices range from €500 to €471,195,000 — the dataset includes everything from a rural plot to a large commercial asset.

### Rental prices

- **National median rent: €614/month** — with a mean of €1,154/month (1.9× the median), heavily skewed by luxury and short-term listings at the top end.
- Rental prices range from €15 to €100,000/month. Most Bulgarian rentals fall in the **€400–€800/month** range.

### €/m² by property type (sales)

- Apartments command a median **€1,731/m²** nationally — the most meaningful benchmark given their dominance in the dataset.
- Luxury apartments and maisonettes sit above this, while houses and villas sit below — buyers pay for land and volume, but the per-m² efficiency is lower.
- Plots, agricultural land, and farms are excluded from €/m² comparisons — their values reflect land utility rather than construction cost and would collapse the scale.

> *"The average lies — €247k mean vs €135k median. A small number of luxury listings distort everything. Use the median."*

---

## 3. Geographic Story

**Where the market is concentrated, and how Sofia compares.**

### Regional spread

- **Sofia dominates** with 53,550 listings across the region — nearly double Varna (28,476), the next largest.
- The top 5 regions (Sofia, Varna, Plovdiv, Burgas, Veliko Tarnovo) account for the majority of all listings.
- **Shumen** appears in the top 10 regions by listing volume — a notable result given its population size, reflecting active local market activity.

### The Sofia premium

- **Sofia city median sale price: €244,990** — 1.8× the national median of €135,000.
- **Sofia apartment €/m²: €2,543** vs a national top-10 average of **€1,539** — a 65% premium per square metre.
- The **least expensive region is Lovech at €45,000** median, making Sofia **5.4× more expensive** than Bulgaria's cheapest market.
- Most regions sit **2–3× below Sofia** in median asking price. The market is genuinely bifurcated between the capital and everywhere else.

### Top 5 cities at a glance

| City | Listings | Median sale | Median rent |
|---|---|---|---|
| Sofia | 43,483 | €259,756 | €795/mo |
| Varna | 24,154 | €156,000 | €570/mo |
| Plovdiv | 16,387 | €160,170 | €599/mo |
| Burgas | 5,215 | €149,000 | €500/mo |
| Stara Zagora | 4,396 | €120,000 | €400/mo |

- **Sofia leads on both sale and rental price** by a clear margin.
- **Plovdiv edges out Varna on median sale price** (€160,170 vs €156,000) despite fewer listings — reflecting Plovdiv's growing appeal as a liveable inland city.
- **Varna's rental market is relatively strong** given its sale prices — the Black Sea coastal premium compresses yields compared to inland cities.
- **Stara Zagora** is the most affordable of the top 5 on both metrics.

> *"Sofia costs 5.4× more than Bulgaria's cheapest region, and €2,543/m² vs a national average of €1,539/m². The capital market is in a different tier entirely."*

---

## 4. Features That Matter

**Which amenities are advertised most, and which ones move the price needle.**

### Most advertised amenities

Top 5 by listing frequency across 122,766 clean residential listings:

| Rank | Feature | % of listings |
|---|---|---|
| 1 | Elevator | 49.7% |
| 2 | Furnished | 38.3% |
| 3 | Access control | 33.9% |
| 4 | Insulated/renovated | 25.1% |
| 5 | Parking available | 20.9% |

- **Elevator leads at 49.7%** — present in half of all clean residential listings. In Bulgarian apartment culture it is a baseline expectation, not a luxury differentiator.
- **Access control at 33.9%** reflects how commonly new-build and renovated blocks are sold as secured buildings — it clusters tightly with gated complex and alarm system.
- **Insulated/renovated at 25.1%** signals how much of the stock is older panel-block apartments where a recent renovation is genuinely worth advertising.

### Price uplift — sale market

Median price difference for listings with vs without each feature (residential, non-outlier, min. 200 listings):

| Feature | Uplift | n | Notes |
|---|---|---|---|
| With garage | **+43.8%** | 15,480 | Biggest premium — dedicated parking is scarce in city centres |
| Underground parking | ↑ Premium | — | |
| Luxury | ↑ Strong | — | Confirms the flag is used consistently |
| Gated complex | ↑ Premium | — | Security cluster signals a premium building |
| Elevator | ↑ Moderate | — | Expected enough that absence hurts more than presence helps |
| Furnished | **+1.8%** | — | Nearly negligible on sale price (€145,000 vs €142,370) |
| Needs renovation | **−32.6%** | 4,387 | Biggest discount — market explicitly prices in refurbishment cost |

### Price uplift — rental market

| Feature | Uplift | n | Notes |
|---|---|---|---|
| With garage | **+55.4%** | 1,877 | Even stronger than in the sale market |
| Furnished | **+13.2%** | — | €600/mo vs €530/mo unfurnished — meaningful and consistent |
| Insulated/renovated | **0.0%** | 8,767 | Heavily advertised but no rental uplift — tenants expect it, not reward it |

- **Garage is the standout feature in both markets** — +43.8% on sale and +55.4% on rental. Parking scarcity in Bulgarian city centres is real and the data confirms it unmistakably.
- **Furnished matters far more for rentals (+13.2%) than sales (+1.8%)** — on the sale market it's nearly a wash; in rentals it's a clear and consistent premium.
- **Insulated/renovated has zero rental uplift** despite being the 4th most advertised feature. Landlords think it's a differentiator; tenants treat it as table stakes.

### Feature frequency by region

- **Elevator prevalence is highest in Sofia and Varna** — consistent with their higher proportion of multi-storey apartment stock.
- **Furnished listings are proportionally more common in Varna and Burgas** — driven by the Black Sea coastal short-term and seasonal rental market.
- **Access control and security features concentrate in Sofia** — a specifically urban, capital-city phenomenon.
- **Needs renovation** appears more frequently in smaller cities and rural regions — reflecting older, less-maintained stock compared to Sofia's newer developments.

> *"Garage is the most valuable feature in both markets: +44% on sale, +55% on rent. Furnished matters for rentals, not sales. Insulated/renovated is table stakes — heavily advertised, zero rental uplift."*

---

## Data Notes

These findings are directional, not definitive. Key caveats:

- **Asking prices ≠ transaction prices.** imot.bg lists advertised asking prices only. Negotiation discounts (especially in slower markets) are not captured.
- **year_built is missing for ~56% of properties.** Construction age analysis would be unreliable and is intentionally excluded from this report.
- **date_posted is null for ~72% of listings.** Time-series trend analysis is not viable from this snapshot. All findings are cross-sectional (April 2026).
- **Outlier flags are applied throughout.** Price and area outliers (IQR × 3.0) are excluded from all distribution and uplift analyses. Raw statistics including outliers are available in the scripts.
- **One listing ≠ one property.** The schema does not attempt cross-listing deduplication at the physical asset level. The same flat listed by two agencies counts as two listings.

---

*Source: [imot.bg](https://www.imot.bg) | Scraper: [bulgaria-real-estate-scraper](https://github.com/GabrielaY0rdanova/bulgaria-real-estate-scraper) | Cleaning: [bulgaria-real-estate-cleaning](https://github.com/GabrielaY0rdanova/bulgaria-real-estate-cleaning) | Analysis: [bulgaria-real-estate-analysis](https://github.com/GabrielaY0rdanova/bulgaria-real-estate-analysis)*
