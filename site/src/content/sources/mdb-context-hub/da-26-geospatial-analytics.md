---
title: "Geospatial Analytics"
description: "Spatial analytics studies data with a geographic/locational dimension, where the"
---

# Geospatial Analytics

Spatial analytics studies data with a geographic/locational dimension, where the
core methodological premise is **Tobler's First Law**: "everything is related to
everything else, but near things are more related than distant things." This makes
location an explanatory variable, not just an attribute — and means standard
non-spatial statistics (which assume independent observations) are often invalid
on spatial data. This skill covers general spatial analysis. For MongoDB geo
queries (`2dsphere`, `$geoNear`, `$geoWithin`), defer to `mongodb-geospatial`.

## Core Concepts

### 1. Vector vs Raster Data Models
Two fundamental representations of geographic phenomena:
- **Vector**: discrete features as points, lines, and polygons defined by
  coordinate vertices. Best for objects with crisp boundaries (parcels, roads,
  administrative areas). In Python, vector geometry is handled by Shapely and
  exposed through GeoPandas as a `GeoSeries`/`GeoDataFrame` (a pandas DataFrame
  with one or more geometry columns; only one is the *active* geometry, accessed
  via `.geometry` and switched with `set_geometry()`) ([GeoPandas, Data
  structures, 2026](https://geopandas.org/en/stable/docs/user_guide/data_structures.html)).
- **Raster**: a regular grid of cells/pixels, each holding a value. Best for
  continuous fields (elevation, temperature, satellite imagery). Handled in
  Python by `rasterio`/`xarray`/`rioxarray`.
- Choose vector for object/topology-centric analysis (joins, networks); raster
  for surface/field analysis (interpolation outputs, map algebra). Conversion
  (rasterize/vectorize) loses information — avoid round-tripping.

### 2. Coordinate Reference Systems (CRS) & Projections
A CRS maps coordinates to real locations; without it, geometries are just numbers
in arbitrary space ([GeoPandas, Projections,
2026](https://geopandas.org/en/stable/docs/user_guide/projections.html)).
- **Geographic CRS** uses lat/lon on a 3D ellipsoid. **EPSG:4326 (WGS84)** is the
  GPS/GeoJSON default; its units are *degrees*, not meters.
- **Projected CRS** flattens the earth onto a plane with linear (meter) units.
  **EPSG:3857 (Web Mercator)** is the default for web tiles (Google/OSM/Mapbox):
  good for display, *bad for area* (massively distorts toward the poles).
  **UTM** divides earth into 60 zones for accurate local distance/area; pick the
  zone covering your data ([8th Light, Geographic Coordinate Systems 101,
  2023](https://8thlight.com/insights/geographic-coordinate-systems-101);
  [Esri, Spatial references,
  2024](https://developers.arcgis.com/documentation/spatial-references/)).
- **`set_crs()` vs `to_crs()`**: `set_crs` *assigns/labels* the CRS without moving
  coordinates (use when CRS is missing/wrong); `to_crs` *reprojects* (transforms
  coordinate values). Never confuse them. Use `estimate_utm_crs()` to pick a local
  metric CRS ([GeoPandas, Projections, 2026](https://geopandas.org/en/stable/docs/user_guide/projections.html);
  [Geocomputation with Python, ch.6 Reprojecting, 2024](https://py.geocompx.org/06-reproj)).

### 3. Spatial Predicates & DE-9IM
Topological relationships between two geometries are formalized by the
**Dimensionally Extended 9-Intersection Model (DE-9IM)** — a 3×3 matrix comparing
the interior/boundary/exterior of each geometry. Named predicates are shortcuts
over this matrix ([PostGIS, ch.5 Spatial Queries,
2024](https://postgis.net/docs/manual-dev/using_postgis_query.html);
[Shapely 2.1 manual, 2025](https://shapely.readthedocs.io/en/stable/manual.html)):
- `intersects` (share any space — the inverse of `disjoint`), `contains`,
  `within` (inverse of contains), `touches` (share only a boundary), `overlaps`,
  `crosses`, `equals`, `covers`/`covered_by`.
- `ST_Relate` (PostGIS) / Shapely `relate()` return the raw DE-9IM string for
  custom relationships.

### 4. Spatial Joins
A **spatial join** attaches attributes from one layer to another by spatial
relationship rather than a key. `geopandas.sjoin(left, right, predicate=...,
how=...)` supports `intersects` (default), `within`, `contains`. `sjoin_nearest`
joins to the closest feature. PostGIS performs the equivalent with predicate
functions in the `WHERE`/`JOIN ON` clause, automatically using a spatial index
when present ([PostGIS workshop, §13 Spatial Joins,
2024](https://postgis.net/workshops/postgis-intro/joins.html); [pythonGIS, Spatial
queries, 2024](https://pythongis.org/part2/chapter-06/nb/05-spatial-queries.html)).

### 5. Geometric (Constructive) Operations
- **Unary**: `buffer(d)` (zone within distance d — units follow the CRS!),
  `centroid`, `simplify(tol)` (Douglas-Peucker vertex reduction),
  `convex_hull`, `envelope`.
- **Binary / set**: `intersection`, `union` (`union_all()`/`unary_union` to
  dissolve a collection), `difference`, `symmetric_difference`.
- GeoPandas `overlay(df1, df2, how=...)` applies set operations across two whole
  layers (`intersection`/`union`/`identity`/`difference`/`symmetric_difference`)
  ([GeoPandas, Set operations with overlay,
  2026](https://geopandas.org/en/stable/docs/user_guide/set_operations.html);
  [Geocomputation with Python, ch.4 Geometry operations,
  2024](https://py.geocompx.org/04-geometry-operations)).

### 6. Spatial Indexing
Without an index, every pairwise spatial test is O(n²). Two index families:
- **Tree indexes (R-tree)**: bounding-box hierarchy used internally by GeoPandas
  (`.sindex`), Shapely STRtree, and PostGIS GiST. Fast pairwise filtering; node
  rectangles may overlap ([Corso, Geospatial Indexing,
  2020](https://austincorso.com/2020/12/02/geospatial-indexing.html)).
- **Discrete global grid systems (DGGS)** encode location as a hierarchical
  cell ID for prefix/integer lookups and aggregation:
  - **Geohash** (Niemeyer, 2008): Z-order rectangles; shared string prefix ⇒
    shared parent cell. Suffers boundary discontinuity (adjacent points can
    differ at the first char).
  - **Google S2**: projects sphere onto cube faces, Hilbert-curve ordered
    64-bit IDs; square cells; used in Google Maps. Strong for hierarchical
    coverings/aggregation.
  - **Uber H3** (open-sourced 2018): hexagonal cells; near-uniform centroid
    spacing and a single neighbor distance, ideal for grid traversal, binning,
    and ML features. Hexagons can't perfectly nest, so parent/child is
    approximate ([Feifke, Geospatial Indexing Explained,
    2023](https://benfeifke.com/posts/geospatial-indexing-explained/); [KunYu,
    H3 vs Geohash vs S2, 2024](https://ky-gis.com/en/blog/h3-vs-geohash-vs-s2)).
  - Rule of thumb: **H3** for neighbor/traversal and binning; **S2** for exact
    nesting/aggregation; **geohash** for simple prefix-range queries in a B-tree.

### 7. Spatial Weights (W)
ESDA and spatial regression require a **spatial weights matrix** encoding which
observations are neighbors. Built with libpysal ([Geographic Data Science with
Python, ch.4 Spatial Weights,
2024](https://geographicdata.science/book/notebooks/04_spatial_weights.html);
[libpysal 4.13 user guide,
2024](https://pysal.org/libpysal/user-guide/weights/weights.html)):
- **Contiguity**: `Queen` (share a vertex *or* edge) vs `Rook` (share an edge
  only) — for polygons.
- **Distance-based**: `KNN` (k nearest), `DistanceBand` (all within a threshold),
  `Kernel` (distance-decayed weights).
- **Row-standardization** (`w.transform = 'r'`) rescales each row to sum to 1 so
  the spatial lag is a neighbor *average*; usually required before Moran's I /
  regression.

### 8. Spatial Autocorrelation (ESDA)
Measures whether similar values cluster in space ([Geographic Data Science with
Python, ch.7 Local Autocorrelation,
2024](https://geographicdata.science/book/notebooks/07_local_autocorrelation.html);
[PySAL `esda`, 2025](https://johal.in/pysal-spatial-stats-python-moran-i-autocorrelation-2025/);
[r-spatial book, ch.15 Measures of Spatial Autocorrelation,
2023](https://r-spatial.org/book/15-Measures.html)):
- **Global Moran's I**: one statistic for the whole map: positive ⇒ clustering,
  ~0 ⇒ spatial randomness, negative ⇒ dispersion/checkerboard. Significance via
  permutation inference (`esda.Moran`).
- **Geary's C**: ranges ~0–2 (1 = no autocorrelation); more sensitive to *local*
  differences and inversely related to Moran's I but not identical.
- **LISA / Local Moran's I** (`esda.Moran_Local`): decomposes the global
  statistic per location, classifying significant units into **HH, LL** (spatial
  clusters) and **HL, LH** (spatial outliers); visualize with a Moran scatterplot
  and LISA cluster map (`splot`).

### 9. Point-Pattern Analysis
Analyzes the locations of events themselves (not attribute values), testing
against **Complete Spatial Randomness (CSR)** ([Geographic Data Science with
Python, ch.8 Point Pattern Analysis,
2024](https://geographicdata.science/book/notebooks/08_point_pattern_analysis.html);
[PySAL `pointpats` v2.5,
2025](http://pysal.org/pointpats/)):
- **Kernel Density Estimation (KDE)**: smooth continuous intensity surface
  (hotspot map); bandwidth choice dominates the result.
- **Nearest-neighbor / G & F functions**: distribution of nearest-neighbor
  distances; clustered if observed distances < CSR expectation.
- **Ripley's K (and the variance-stabilized L)**: counts neighbors within
  increasing radii to test clustering vs dispersion *across scales*; assess
  against simulation envelopes.

### 10. Interpolation & Kriging
Predict values at unsampled locations from sampled points ([pygis, Spatial
Interpolation, 2024](https://pygis.io/docs/e_interpolation.html); [Columbia MSPH,
Kriging Interpolation, 2024](https://www.publichealth.columbia.edu/research/population-health-methods/kriging-interpolation);
[PyKrige 1.7 docs, 2024](https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/generated/pykrige.ok.OrdinaryKriging.html)):
- **IDW (Inverse Distance Weighting)**: deterministic; weight ∝ 1/dist^p. Simple,
  no uncertainty estimate, prone to "bull's-eyes."
- **Kriging**: geostatistical; weights derive from a fitted **variogram**
  (semi-variance vs lag distance), so it accounts for spatial structure *and*
  yields prediction variance. **Ordinary kriging** assumes an unknown constant
  mean; PyKrige supports linear/power/spherical/gaussian/exponential variogram
  models and 2D/3D ordinary & universal kriging.

### 11. Geocoding
Forward **geocoding** = address → coordinates; **reverse geocoding** = coordinates
→ address. `geopy` wraps providers (OSM **Nominatim** = free, Google/Bing/etc.).
Wrap calls in `geopy.extra.rate_limiter.RateLimiter` and set a unique
`user_agent` — Nominatim enforces ≤1 req/s and bans bulk abuse ([GeoPy 2.4 docs,
2024](https://geopy.readthedocs.io/); [Spatial Dev Guru, Geocoding with geopy,
2023](https://spatial-dev.guru/2023/03/12/geocoding-and-reverse-geocoding-in-python-using-geopy/)).

### 12. Choropleth Mapping & Classification
A **choropleth** shades areal units by a value; the **classification scheme**
(binning) drives the visual message ([Geographic Data Science with Python, ch.5
Choropleth Mapping,
2024](https://geographicdata.science/book/notebooks/05_choropleth.html);
[PySAL `mapclassify`, 2024](https://github.com/pysal/mapclassify); [GIS Geography,
Choropleth data classification, 2024](https://gisgeography.com/choropleth-maps-data-classification/)):
- **Equal Interval**: equal value ranges; intuitive but skewed data collapses
  into few classes.
- **Quantiles**: equal *count* per class; good general-purpose readability but
  can place similar values in different classes.
- **Natural Breaks (Fisher-Jenks)**: minimizes within-class variance, maximizes
  between-class variance; respects data structure but breaks aren't comparable
  across maps.
- Always **normalize counts to rates/densities** before mapping, and use
  `mapclassify` (`NaturalBreaks`, `Quantiles`, `EqualInterval`, `FisherJenks`).

### 13. Spatial Regression
Standard OLS on spatial data violates the independence assumption; residuals are
autocorrelated. Two model families ([Spatial Modelling for Data Scientists, ch.9
GWR, 2024](https://gdsl-ul.github.io/san/09-gwr.html); [Esri, GWR tool reference,
2024](https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-statistics/geographically-weighted-regression.htm);
PySAL `spreg`/`mgwr`):
- **Spatial lag model (SAR)**: adds a spatially-lagged *dependent* variable
  (Wy); models spillover/interdependence between units.
- **Spatial error model (SEM)**: autocorrelation in the *error* term (Wε);
  unmodeled spatially-structured omitted variables.
  Choose between them with Lagrange Multiplier diagnostics in `spreg`.
- **Geographically Weighted Regression (GWR)**: fits a *local* regression at each
  location with distance-weighted neighbors, producing spatially-varying
  coefficients (models **non-stationarity**, not interdependence). Watch local
  multicollinearity and bandwidth selection.

## Tools & Frameworks
- **Shapely 2.x**: geometry engine (GEOS); vectorized ops on geometry arrays.
- **GeoPandas 1.x** (2026): pandas + Shapely + pyproj + Fiona/pyogrio; the
  Python workhorse for vector I/O, CRS, joins, overlay, plotting.
- **PostGIS**: spatial extension for PostgreSQL; production spatial SQL with GiST
  indexes; the most feature-complete OSS spatial engine.
- **PySAL**: spatial *statistics* (libpysal weights, esda autocorrelation,
  pointpats, mapclassify, spreg/mgwr regression).
- **H3 / S2**: DGGS libraries for binning, indexing, and ML features.
- **DuckDB spatial extension**: `INSTALL spatial; LOAD spatial;`; fast in-process
  analytical spatial SQL, reads/writes GeoParquet; lighter than PostGIS but fewer
  functions ([DuckDB Spatial Extension docs,
  2025](https://duckdb.org/docs/current/core_extensions/spatial/overview)).
- **Apache Sedona / SedonaDB**: distributed (Spark) and single-node (SedonaDB,
  released 2025) engines treating spatial as first-class; for cluster-scale data
  ([Apache Sedona, Introducing SedonaDB,
  2025](https://sedona.apache.org/latest/blog/2025/09/24/introducing-sedonadb-a-single-node-analytical-database-engine-with-geospatial-as-a-first-class-citizen/)).
- **kepler.gl 3.1**: browser-based large-scale visualization; embeds DuckDB to
  query GeoParquet client-side ([Foursquare, Kepler.gl 3.1,
  2024](https://foursquare.com/resources/blog/products/foursquare-brings-enterprise-grade-spatial-analytics-to-your-browser-with-kepler-gl-3-1/)).
- **GeoParquet**: columnar, compressed interchange format read by GeoPandas,
  DuckDB, Sedona, QGIS, kepler.gl; the emerging standard for analytical vector
  data.

**Tool selection** ([Forrest, Geospatial Tools Compared,
2025](https://forrest.nyc/geospatial-tools-compared-when-to-use-geopandas-postgis-duckdb-apache-sedona-and-wherobots/)):
single-machine exploration/notebooks → GeoPandas; persistent transactional
spatial DB → PostGIS; fast analytical queries on files → DuckDB; cluster-scale
batch → Sedona; spatial statistics/modeling → PySAL.

## Methodology (end-to-end)
1. **Ingest & set CRS**: load, confirm `.crs`; `set_crs` if missing, never to fix
   wrong coordinates.
2. **Reproject**: `to_crs` to a **metric/projected CRS** (UTM via
   `estimate_utm_crs()`) before any distance/area/buffer step.
3. **Clean geometry**: fix invalidities (`make_valid`/`buffer(0)`), drop
   empties, set precision.
4. **Build/attach index**: rely on `.sindex` / GiST; for binning encode H3/S2.
5. **Operate**: joins, overlays, geometric ops.
6. **Analyze**: build weights → ESDA (Moran/LISA) → point pattern / interpolation
   / spatial regression as the question demands.
7. **Communicate**: choropleth with a justified classifier on normalized rates;
   interactive map (kepler.gl/folium) for exploration.

## Practical Patterns
- Reproject to UTM/equal-area **before** measuring length, area, or buffering;
  back to 4326/3857 only for output/display.
- Pre-filter with the spatial index (or H3 cell join) before exact predicate
  tests on large datasets.
- Use H3 to turn messy point data into tidy, joinable grid features for ML and
  dashboards.
- Map **rates/densities**, not raw counts; pick the classifier deliberately
  (quantiles for readability, Jenks for structure, equal interval for comparison).
- Push heavy joins/aggregations into DuckDB-spatial or PostGIS; keep GeoPandas for
  the last-mile.

## Anti-Patterns
- **Computing distance/area in EPSG:4326**: degrees aren't meters; results are
  nonsense and vary with latitude.
- **`set_crs` to "fix" wrong coordinates**: it only relabels; you need `to_crs`
  (or the correct source CRS).
- **Mixing CRS across layers**: silently wrong joins/overlays; always reproject
  to a common CRS first.
- **Using Web Mercator for area/statistics**: extreme high-latitude distortion;
  use an equal-area projection.
- **Skipping row-standardization of W** before Moran's I / spatial lag.
- **Mapping raw counts as a choropleth** (population artifact) instead of rates.
- **Bulk-hammering Nominatim** without rate-limiting/user_agent — gets you banned.
- **Trusting OLS on spatial data** without checking residual autocorrelation.

## Troubleshooting
- *"Geometry is in a geographic CRS. Results may be incorrect" (GeoPandas
  warning)* → reproject to a projected CRS before the area/length/buffer op.
- *Empty/NaN spatial join result* → CRS mismatch between layers, or wrong
  `predicate`; check `.crs` on both and the relationship direction
  (within vs contains).
- *`TopologyException` / invalid geometry* → run `make_valid()` or `buffer(0)`;
  inspect with `.is_valid` and `.explain_validity`.
- *Moran's I ≈ 0 but a visible pattern* → wrong/under-connected weights (try
  Queen vs KNN), or scale mismatch; verify W connectivity (no islands).
- *Kriging variogram won't fit* → too few points, duplicate coordinates, or wrong
  model; try IDW as a baseline and inspect the empirical variogram.
- *H3/geohash boundary artifacts* → neighbors split across cells; buffer the query
  or use `grid_disk`/`kRing` to include adjacent cells.
- *DuckDB function missing* → spatial coverage is narrower than PostGIS; fall back
  to PostGIS/GeoPandas for that op.

## References
- GeoPandas, Data structures / Projections / Set operations (2026): https://geopandas.org/en/stable/docs/user_guide/
- Shapely 2.1 User Manual (2025): https://shapely.readthedocs.io/en/stable/manual.html
- PostGIS, Spatial Queries & Joins workshop (2024): https://postgis.net/workshops/postgis-intro/joins.html
- Geographic Data Science with Python, Weights/ESDA/Point Patterns/Choropleth (2024): https://geographicdata.science/book/
- libpysal Spatial Weights v4.13 (2024): https://pysal.org/libpysal/user-guide/weights/weights.html
- PySAL esda / pointpats / mapclassify / spreg / mgwr (2024-2025): https://pysal.org/
- PyKrige 1.7 docs (2024): https://geostat-framework.readthedocs.io/projects/pykrige/
- GeoPy 2.4 docs (2024): https://geopy.readthedocs.io/
- Geocomputation with Python, Reprojection & Geometry ops (2024): https://py.geocompx.org/
- Feifke, Geospatial Indexing Explained, Geohash/S2/H3 (2023): https://benfeifke.com/posts/geospatial-indexing-explained/
- KunYu, H3 vs Geohash vs S2 (2024): https://ky-gis.com/en/blog/h3-vs-geohash-vs-s2
- DuckDB Spatial Extension (2025): https://duckdb.org/docs/current/core_extensions/spatial/overview
- Apache Sedona, Introducing SedonaDB (2025): https://sedona.apache.org/latest/blog/2025/09/24/introducing-sedonadb-a-single-node-analytical-database-engine-with-geospatial-as-a-first-class-citizen/
- Foursquare, Kepler.gl 3.1 (2024): https://foursquare.com/resources/blog/products/foursquare-brings-enterprise-grade-spatial-analytics-to-your-browser-with-kepler-gl-3-1/
- Forrest, Geospatial Tools Compared (2025): https://forrest.nyc/geospatial-tools-compared-when-to-use-geopandas-postgis-duckdb-apache-sedona-and-wherobots/
- Esri, GWR & Spatial references (2024): https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-statistics/geographically-weighted-regression.htm
