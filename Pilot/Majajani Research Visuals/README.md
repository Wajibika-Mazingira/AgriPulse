# Research figures, maps and data

This companion directory contains the map and graph data and reproducible Python/R scripts for the revised Majajani Farms research perspective.

## Run

From this directory, install `requirements.txt`, then run:

```sh
python scripts/build_visuals.py
Rscript scripts/build_visuals.R
```

Python downloads public geoBoundaries Kenya county geometry and selected Sentinel-2 L2A true-colour crops from Microsoft Planetary Computer. Use `python scripts/build_visuals.py --skip-imagery` to regenerate vector plots without internet imagery. The R script uses base R only; it creates its own point map (without county outlines), population and displacement plots, and evidence-network graphic as `*_R.png` files. Either language can run independently after the CSV tables are in place.

## Files and figures

- `data/sites.csv`: map reference points and precision notes.
- `data/elephant_estimates.csv`: published, method-tagged elephant estimates.
- `data/displacement_evidence.csv`: reported resettlement numbers and one farmer’s account, each with units and evidence status.
- `data/agency_timeline.csv`: institutional periods, agency heads and the source/limits of each statement.
- `data/network_nodes.csv`, `data/network_edges.csv`: graph-ready actors and relationships. Edges carry evidence classes and causal limits; short `graph_label` values in the plot map to full node labels in the table.
- `data/sources.csv`: source registry.
- `figures/`: generated locator map, estimates, displacement evidence, timeline, evidence graph and satellite panels.
- `imagery/`: cropped satellite image assets and `data/imagery_scenes.csv` metadata.

## Interpretation and methods

The Arabuko–Tsavo connector drawn on the map is deliberately schematic: the 2023 National Elephant Action Plan says it is not robustly monitored and does not supply a route geometry in the cited table. The Chakama-to-Tsavo relationship records the source area named in 2021 reporting, not a tracked route. Map points are reference locations—not title, mine-lease, conservation-area, household or Kaya boundaries. The private Majajani Farms plot was not geocoded or mapped; restricted Kaya information is not reproduced.

The Arabuko-Sokoke figure uses a 2017 dung-count estimate (215; 95% CI 145–318); Shimba Hills and Tsavo figures are 2021 aerial estimates. They are different years and survey methods, so the plot is not a population trend or a direct comparison of densities. The resettlement chart keeps people, households, acres and reported disputes in separate panels; reported grievances are not treated as adjudicated findings. The “over 3,000 people” and “over 100 disputes” values are lower-bound visual references, not exact counts.

Satellite panels use Sentinel-2 L2A surface-reflectance true-colour RGB assets at nominal 10 m ground-sample distance. The visible crops are stretched for display, labelled with scene ID, acquisition date and study-area cloud/shadow estimate, and do not delineate the operation, show pre-mining conditions, or prove rehabilitation success. Copernicus Sentinel data terms apply; source attribution and scene metadata are included in `data/imagery_scenes.csv`.

County boundaries come from geoBoundaries Kenya ADM1 2020, distributed as public-domain data. The companion `network_edges.csv` distinguishes published relationships and reported claims from open questions; it is not a causal model.
