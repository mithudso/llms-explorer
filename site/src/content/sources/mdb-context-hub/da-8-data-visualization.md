---
title: "Data Visualization"
description: "Taxonomy context: Data Analysis > Data Visualization"
---

# Data Visualization

**Taxonomy context:** Data Analysis > Data Visualization

Data visualization is the principled translation of data into visual form so that the human visual system — which is fast, parallel, and pattern-seeking — can extract structure that the verbal system alone cannot. Done well, a chart compresses a table of numbers into a single glance and surfaces the comparison the audience needs to make a decision. Done poorly, it distorts, distracts, or actively deceives.

Two modes recur: **exploratory visualization** (analyst draws many quick charts to find something; iteration speed > polish; matplotlib, seaborn, ggplot2, altair) and **explanatory visualization** (analyst has found the point and needs the audience to see it; polish, narrative, accessibility > iteration speed; Tableau / Power BI dashboards, D3 / Plotly for web, publication matplotlib / ggplot2).

## 1. Perceptual foundation (Cleveland & McGill 1984)

Encodings ranked by accuracy of magnitude estimation (most to least accurate): position along common scale > position along non-aligned scales > length / direction / angle > area > volume / curvature > shading / color saturation / hue. Implication: encode the focal comparison along position. Reach for area, angle, or color only when position is taken or the chart's job is pattern recognition rather than precise estimation.

## 2. Tufte's principles

- **Data-ink ratio.** Maximize ratio of data-ink to total ink. Erase non-data-ink and redundant data-ink within reason. Heuristic, not commandment — accessibility and clarity can override.
- **Chartjunk.** Unnecessary elements (3D bevels, animated gradients, decorative iconography, moiré).
- **Small multiples.** Grid of the same chart type repeated for each level of a categorical variable, with shared scales. Replaces stacked bars and multi-series spaghetti.
- **Sparklines.** Word-sized, axis-free trend lines inline with prose or next to a value.
- **Graphical integrity / Lie Factor.** (Visual change shown) / (actual change in data). Should be ~1.

## 3. Knaflic / Few — explanatory design

- **Preattentive attributes.** Color, size, position, orientation are processed by visual system in ~200ms, before conscious attention. Use to direct attention to the one thing the chart is about; grey out the rest.
- **Decluttering.** Remove border, gridlines, redundant tick marks. Soften axis labels. Push legend onto the line. Apply preattentive emphasis last.
- **Action titles.** Title states the finding ("Revenue declined 12% in Q3, driven by APAC"), not a description ("Quarterly Revenue").
- **Few's dashboard rules.** Single screen, no scroll. Inverted pyramid of detail. Encode by importance. Consistent encoding across panels. Context always (target, prior period, sparkline). No gratuitous decoration. Refresh timestamp on screen.
- **BAN tiles (Big-Ass Numbers).** Large headline KPI value with small trend indicator or sparkline. Dashboard analog of an action title.

## 4. Gestalt principles

Proximity, similarity, enclosure, closure, continuity, connection — describe how the visual system groups elements. Turn data-ink abstractions into concrete layout decisions: removing a border works (closure), small multiples scan quickly (similarity + proximity), stray red dot pops (similarity-violation).

## 5. Chart selection by intent

| Intent | First choice | Avoid |
|---|---|---|
| Comparison among categories | Horizontal bar chart, sorted | Pie chart, 3D bar |
| Comparison over time | Line chart | Stacked area for >3 series |
| Composition (parts of whole) | 100% stacked bar, treemap, waffle | Donut, exploded pie, 3D pie |
| Distribution of one variable | Histogram, density, boxplot | Pie chart of binned ranges |
| Distribution by group | Small-multiples histograms, boxplots side-by-side, ridgeline | Overlapping density with many groups |
| Relationship between two numerics | Scatterplot (hexbin for large n) | Connected scatter without clear order |
| Spatial | Choropleth of rates, proportional symbol of counts | Choropleth of raw counts |
| Hierarchy | Treemap, sunburst | Pie of pies |
| Flow | Sankey, alluvial | Spaghetti line chart |
| Single headline value | BAN tile with sparkline + delta | Gauge / speedometer |

## 6. Color theory

- **Sequential palettes** — single-hue ramp for continuous ordered data with no meaningful midpoint. Viridis (perceptually uniform, colorblind-safe), Cividis (optimized for protanopia / deuteranopia), Magma, Inferno, Plasma, ColorBrewer Blues / Greens.
- **Diverging palettes** — two contrasting hues meeting at a neutral midpoint, for continuous data with a meaningful reference. ColorBrewer RdBu, BrBG, PiYG, PuOr. Midpoint must match the reference value, not dataset median.
- **Categorical palettes** — distinct unordered hues for nominal categories. Hard limit ~6-8 hues. Okabe-Ito (Wong palette, colorblind-safe), ColorBrewer Set2 / Dark2, Tableau 10.
- **Never color alone.** Pair with shape, pattern, direct label, or position (WCAG 1.4.1).
- **Grayscale test.** Viridis and Cividis pass; jet / rainbow does not.
- **Avoid rainbow / jet.** Not perceptually uniform; distorts magnitude reads.

## 7. WCAG accessibility for charts

| Criterion | Level | Meaning |
|---|---|---|
| 1.1.1 Non-text Content | A | Every chart needs text alt + (for complex) longer description and/or data table |
| 1.4.1 Use of Color | A | Color may not be the only encoding |
| 1.4.3 Contrast (Minimum) | AA | Text contrast ≥ 4.5:1 |
| 1.4.11 Non-text Contrast | AA | Graphical objects ≥ 3:1 against adjacent colors |
| 2.1.1 Keyboard | A | Interactive charts operable from keyboard alone |

Alt-text template: `[chart type] of [what is measured] by [grouping]. [Headline finding].`

## 8. Grammar of graphics (Wilkinson 1999 / Wickham 2010 layered)

Chart = data + aesthetic mapping (x, y, color, size, shape) + geom + stat (identity, bin, count, smooth, boxplot, density) + position adjustment (identity, dodge, stack, fill, jitter) + scales + coordinate system + faceting. The named-chart taxonomy (bar / pie / line) is a cache of common grammar configurations.

## 9. Tooling map

**Python notebook / static:** matplotlib (imperative foundation, max control), seaborn (statistical convenience), altair (Vega-Lite declarative), plotly express, plotnine (ggplot2 in Python), bokeh.

**R:** ggplot2 (the layered grammar reference), lattice.

**JS interactive:** D3 (low-level, max control), Observable Plot (high-level by D3 team), Vega-Lite (declarative JSON), Plotly.js (WebGL), Chart.js (simple), ECharts (enterprise dashboards).

**BI / dashboard platforms:** Tableau (long-time category leader), Power BI (Microsoft ecosystem default), Looker Studio (free, Google ecosystem), Looker enterprise (semantic-modeling-first, LookML), Metabase (open source, easy for non-technical), Apache Superset (open source, enterprise, 40+ connectors), MongoDB Atlas Charts (native to Atlas, document-aware).

**Selection heuristic:** notebook / paper → matplotlib / seaborn / ggplot2; public web → plotly / observable plot / vega-lite / D3; dashboard → BI tool; product surface → plotly / ECharts / React-charting library bound to design system.

## 10. Dashboard design — Few's at-a-glance rules

Single screen, no scroll. Inverted pyramid of detail (BANs top, trends middle, detail bottom). Encode by importance. Consistent encoding across panels. Context always. No gratuitous decoration. Color carries meaning, not personality. Drill-down paths, not detail-everywhere. Refresh cadence visible on screen.

## 11. Anti-patterns

- **Truncated y-axis on a bar chart** — bars encode magnitude; truncating lies. (Line charts exempt when range is small relative to absolute value; state baseline.)
- **3D charts** — distort perception, add chartjunk.
- **Pie charts with > 3 slices** — angle and area are low-accuracy encodings.
- **Dual y-axis charts** — independent scales fabricate apparent relationships. Use small multiples, connected scatter, or index normalization instead.
- **Rainbow / jet colormap** — not perceptually uniform.
- **Color as only encoding** — fails for colorblind viewers.
- **Spaghetti line charts** — small multiples or grey-out non-focal instead.
- **Choropleth of raw counts** — dominated by population. Use rates or cartogram.
- **Cumulative-only line hiding rate** — show daily/weekly delta alongside cumulative.
- **Mixing absolute and relative scales without labeling.**
- **Stacked bars when audience must compare segments** — use grouped bar or small multiples.
- **Bubble charts encoding diameter instead of area.**
- **Mercator for global statistical maps** — use equal-area (Robinson, Equal Earth, Mollweide).
- **Animated bar-chart races** — fun to watch, terrible for comparing specific values.

## 12. Workflow

1. Write the headline finding as a one-sentence claim before touching the chart tool.
2. Identify audience and medium.
3. Pick the intent (comparison / composition / distribution / relationship / temporal / spatial).
4. Pick chart type (apply Cleveland & McGill; avoid pie / 3D / dual-axis unless required).
5. Draft and declutter (remove border, soften gridlines, push legend onto line).
6. Apply preattentive emphasis (grey for non-focal, color for focal, direct labels).
7. Write the action title (the headline claim, not a description).
8. Verify graphical integrity (zero baseline on bars, 100% pie sum, no 3D, no dual axis).
9. Accessibility pass (contrast, alt text, color-alone check, grayscale test, screen-reader description).
10. Show to someone who has not seen the data; if the headline does not land within 5 seconds, iterate.

## 13. References

Tufte 1983 *Visual Display of Quantitative Information*; Tufte 1990 *Envisioning Information*; Few 2013 *Information Dashboard Design*; Few 2009 *Now You See It*; Knaflic 2015 *Storytelling with Data*; Cairo 2016 *The Truthful Art*; Cairo 2019 *How Charts Lie*; Wilkinson 2005 *Grammar of Graphics*; Wickham 2016 *ggplot2*; Munzner 2014 *Visualization Analysis and Design*; Cleveland & McGill 1984 *Graphical Perception* (JASA 79); Wickham 2010 *A Layered Grammar of Graphics* (JCGS 19); Heer & Bostock 2010 *Crowdsourcing Graphical Perception* (CHI); ColorBrewer 2.0 (colorbrewer2.org); Viridis (matplotlib documentation); Cividis (Nuñez Anderton Renslow 2018 PLoS One); Wong 2011 *Color blindness* (Nature Methods, Okabe-Ito); W3C WCAG 2.2; Lundgard & Satyanarayan 2022 *Accessible Visualization via Natural Language Descriptions* (IEEE VIS).

Full installed skill: `~/.claude/skills/da-8-data-visualization/SKILL.md` (815 lines).
