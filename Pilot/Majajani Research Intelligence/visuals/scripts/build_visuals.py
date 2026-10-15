#!/usr/bin/env python3
"""Build cited maps, plots, and Sentinel-2 panels for the Majajani paper.

Run from any directory with Python dependencies in requirements.txt:
    python scripts/build_visuals.py

The regional route lines are explicitly schematic. Point coordinates are
reference locations, not surveyed farm, lease, Kaya, or elephant-path limits.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import planetary_computer as pc
import rasterio
import requests
from pystac_client import Client
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from shapely.geometry import box, shape


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGURES = ROOT / "figures"
IMAGERY = ROOT / "imagery"
BOUNDARY_PATH = DATA / "geoBoundaries-KEN-ADM1.geojson"
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
GEOBOUNDARIES_URL = "https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM1/"

COLORS = {
    "wildlife": "#227C70",
    "community": "#C65D3A",
    "heritage": "#8064A2",
    "mine": "#D08B22",
    "agency": "#376996",
    "gray": "#65717C",
    "pale": "#E8ECEF",
}


def ensure_boundaries() -> dict[str, Any] | None:
    """Cache public-domain Kenya county geometry from geoBoundaries."""
    if BOUNDARY_PATH.exists():
        return json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    try:
        metadata = requests.get(GEOBOUNDARIES_URL, timeout=45).json()
        geojson_url = metadata["gjDownloadURL"]
        response = requests.get(geojson_url, timeout=90)
        response.raise_for_status()
        data = response.json()
        BOUNDARY_PATH.write_text(json.dumps(data), encoding="utf-8")
        return data
    except Exception as exc:  # map still builds with labeled reference points
        print(f"County boundary download skipped: {exc}")
        return None


def feature_name(feature: dict[str, Any]) -> str:
    props = feature.get("properties", {})
    for key in ("shapeName", "shapeNameAlt", "NAME_1", "name", "county"):
        if props.get(key):
            return str(props[key])
    return ""


def draw_geometry(ax: Any, geometry: dict[str, Any], **kwargs: Any) -> None:
    kind = geometry.get("type")
    coords = geometry.get("coordinates", [])
    polygons = [coords] if kind == "Polygon" else coords if kind == "MultiPolygon" else []
    for polygon in polygons:
        if not polygon:
            continue
        exterior = polygon[0]
        xs, ys = zip(*exterior)
        ax.fill(xs, ys, **kwargs)


def draw_coast_counties(ax: Any, boundaries: dict[str, Any] | None) -> None:
    if not boundaries:
        return
    for feature in boundaries.get("features", []):
        name = feature_name(feature).lower()
        if name not in {"kilifi", "kwale", "mombasa", "taita taveta", "taita-taveta"}:
            continue
        geom = feature.get("geometry")
        if geom:
            draw_geometry(
                ax,
                geom,
                facecolor="#F2F0E9",
                edgecolor="#89939B",
                linewidth=0.7,
                zorder=0,
            )
            centroid_coords = []
            if geom["type"] == "Polygon":
                centroid_coords = geom["coordinates"][0]
            elif geom["type"] == "MultiPolygon":
                centroid_coords = max(geom["coordinates"], key=lambda p: len(p[0]))[0]
            if centroid_coords:
                cx = sum(p[0] for p in centroid_coords) / len(centroid_coords)
                cy = sum(p[1] for p in centroid_coords) / len(centroid_coords)
                if -4.7 < cy < -2.5 and 38.4 < cx < 40.5:
                    ax.text(cx, cy, feature_name(feature), fontsize=8, color="#5E6870", ha="center", zorder=1)


def plot_regional_map(boundaries: dict[str, Any] | None) -> None:
    sites = pd.read_csv(DATA / "sites.csv")
    sites = sites.dropna(subset=["latitude", "longitude"])
    fig, ax = plt.subplots(figsize=(10, 8), layout="constrained")
    ax.set_facecolor("#EAF3F5")
    draw_coast_counties(ax, boundaries)

    styles = {
        "elephant habitat": (COLORS["wildlife"], "o"),
        "reported elephant-incursion area": (COLORS["community"], "s"),
        "coastal community reference": (COLORS["community"], "^"),
        "mining project area": (COLORS["mine"], "D"),
        "publicly mapped Kaya site": (COLORS["heritage"], "P"),
        "elephant source named in reporting": (COLORS["wildlife"], "*"),
    }
    offsets = {
        "Arabuko-Sokoke Forest": (0.025, 0.035),
        "Chakama / Adu ward": (0.025, -0.045),
        "Takaungu": (0.025, 0.005),
        "Kwale Mineral Sands / Base Titanium operations": (-0.31, -0.08),
        "Shimba Hills National Reserve": (-0.31, -0.04),
        "Kaya Kinondo": (0.035, 0.045),
    }
    map_labels = {
        "Kwale Mineral Sands / Base Titanium operations": "Kwale titanium mine area (approx.)",
        "Kaya Kinondo": "Kaya Kinondo (public reference)",
    }
    for _, site in sites.iterrows():
        color, marker = styles.get(site["site_type"], (COLORS["gray"], "o"))
        ax.scatter(site.longitude, site.latitude, s=75, c=color, marker=marker, edgecolor="white", linewidth=0.7, zorder=4)
        dx, dy = offsets.get(site["name"], (0.02, 0.02))
        ax.annotate(map_labels.get(site["name"], site["name"]), (site.longitude + dx, site.latitude + dy), fontsize=8, color="#17232B", zorder=5)

    # Deliberately schematic: the official plan says monitoring is weak; it
    # does not provide a route geometry suitable for digitizing here.
    arabuko = sites.loc[sites.site_id.eq("ASF")].iloc[0]
    tsavo = sites.loc[sites.site_id.eq("TSAVOEAST")].iloc[0]
    ax.plot(
        [tsavo.longitude, arabuko.longitude],
        [tsavo.latitude, arabuko.latitude],
        linestyle="--",
        color=COLORS["wildlife"],
        linewidth=1.4,
        zorder=2,
    )
    ax.text(39.23, -3.18, "Arabuko–Tsavo linkage (schematic)", fontsize=8, color=COLORS["wildlife"], rotation=-7, ha="center", va="bottom", bbox={"facecolor": "white", "alpha": 0.83, "edgecolor": "none", "pad": 2}, zorder=6)

    ax.set_xlim(38.65, 40.18)
    ax.set_ylim(-4.62, -2.68)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°S; plotted as negative degrees)")
    ax.set_title("Kilifi elephants, Kaya reference site, and the separate Kwale titanium project", loc="left", weight="bold")
    ax.text(
        0.01,
        0.01,
        "Reference points only. No farm, mine-lease, Kaya-boundary or wildlife-route geometry is asserted.\n"
        "The Arabuko–Tsavo line is schematic; the 2023 national plan says this linkage is not robustly monitored.",
        transform=ax.transAxes,
        fontsize=8,
        color="#44515A",
        va="bottom",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.88, "edgecolor": "#D0D6D9"},
    )
    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["wildlife"], markeredgecolor="white", label="Elephant habitat/source", markersize=8),
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=COLORS["community"], markeredgecolor="white", label="Reported incursion site", markersize=8),
        plt.Line2D([0], [0], marker="D", color="none", markerfacecolor=COLORS["mine"], markeredgecolor="white", label="Titanium project reference", markersize=8),
        plt.Line2D([0], [0], marker="P", color="none", markerfacecolor=COLORS["heritage"], markeredgecolor="white", label="Public Kaya reference", markersize=8),
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=7.5, framealpha=0.92)
    ax.grid(color="white", linewidth=0.7, alpha=0.8)
    fig.savefig(FIGURES / "regional_sites_map.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES / "regional_sites_map.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_elephant_estimates() -> None:
    data = pd.read_csv(DATA / "elephant_estimates.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), gridspec_kw={"width_ratios": [1.1, 1.2]}, layout="constrained")
    forest = data[data.population.eq("Arabuko-Sokoke Forest")].iloc[0]
    ax1.errorbar(
        [forest.estimate],
        [0],
        xerr=[[forest.estimate - forest.lower_ci], [forest.upper_ci - forest.estimate]],
        fmt="o",
        color=COLORS["wildlife"],
        capsize=5,
        markersize=8,
    )
    ax1.set_yticks([0], ["Arabuko–Sokoke"])
    ax1.set_xlim(0, 350)
    ax1.set_xlabel("Elephants (95% CI where reported)")
    ax1.set_title("Kilifi forest estimate", loc="left", weight="bold")
    ax1.text(0.02, 0.05, "2017 dung count: 215\n95% CI: 145–318", transform=ax1.transAxes, fontsize=9)
    ax1.grid(axis="x", color="#DFE4E7")

    context = data[data.population.isin(["Shimba Hills", "Tsavo ecosystem"])].copy()
    bars = ax2.barh(context.population, context.estimate, color=[COLORS["heritage"], COLORS["wildlife"]], height=0.48)
    ax2.set_xlabel("Elephants (separate ecosystem estimates)")
    ax2.set_title("Regional context — not Kilifi counts", loc="left", weight="bold")
    ax2.grid(axis="x", color="#DFE4E7")
    for bar, (_, row) in zip(bars, context.iterrows()):
        ax2.text(bar.get_width() + 260, bar.get_y() + bar.get_height() / 2, f"{int(row.estimate):,} · {int(row.estimate_year)} {row.survey_method}", va="center", fontsize=8)
    ax2.set_xlim(0, 18000)
    fig.suptitle("Published elephant estimates differ in date, method and spatial scale", x=0.01, ha="left", fontsize=13, weight="bold")
    fig.text(0.01, -0.015, "Source: KWS/WRTI National Elephant Action Plan (2023), reproducing Waweru et al. (2021). Values are not a trend series.", fontsize=8, color="#44515A")
    fig.savefig(FIGURES / "elephant_estimates.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES / "elephant_estimates.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_displacement_evidence() -> None:
    data = pd.read_csv(DATA / "displacement_evidence.csv")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    panels = [
        (axes[0, 0], ["households", "people"], "Reported relocation scale", "Count", ["Maumba households", "Kwale residents"]),
        (axes[0, 1], ["disputes"], "Dispute claims reported in 2016", "Reported cases", ["All disputes", "Claimed no compensation"]),
    ]
    households_people = data[data.unit.isin(["households", "people"])]
    ax = axes[0, 0]
    labels = ["Maumba households\n(Global Press, 2016)", "Kwale residents\n(Abuya, 2016)\n‘over 3,000’"]
    values = [480, 3000]
    bars = ax.barh(labels, values, color=[COLORS["community"], "#D98465"])
    ax.set_title("Different units and source bases", loc="left", weight="bold")
    ax.set_xlabel("Source-reported count (not an audited total)")
    ax.grid(axis="x", color="#DFE4E7")
    for bar, value, label in zip(bars, values, ["480 households", ">3,000 people"]):
        ax.text(value + 40, bar.get_y() + bar.get_height() / 2, label, va="center", fontsize=8)
    ax.set_xlim(0, 3900)

    disputes = data[data.unit.eq("disputes")]
    ax = axes[0, 1]
    dlabels = ["Land disputes reported", "Claimed no compensation"]
    dvals = [100, 91]
    bars = ax.barh(dlabels, dvals, color=[COLORS["community"], "#D98465"])
    ax.set_title("Community-reported land disputes", loc="left", weight="bold")
    ax.set_xlabel("Case count reported in 2016 (not current status)")
    ax.set_xlim(0, 125)
    ax.grid(axis="x", color="#DFE4E7")
    for bar, value in zip(bars, dvals):
        ax.text(value + 2, bar.get_y() + bar.get_height() / 2, f"{value}+" if value == 100 else str(value), va="center", fontsize=8)

    ax = axes[1, 0]
    acre_rows = data[data.unit.eq("acres")]
    vals = [31, 13]
    bars = ax.barh(["Acreage claimed", "Acreage reportedly compensated"], vals, color=[COLORS["gray"], COLORS["mine"]])
    ax.set_title("One Nguluku farmer’s account (2024)", loc="left", weight="bold")
    ax.set_xlabel("Acres; individual testimony, not adjudicated")
    ax.set_xlim(0, 38)
    ax.grid(axis="x", color="#DFE4E7")
    for bar, value in zip(bars, vals):
        ax.text(value + 0.6, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=8)

    ax = axes[1, 1]
    money = data[data.unit.eq("KES")].iloc[0].value
    ax.axis("off")
    ax.text(0.03, 0.82, "Compensation figure in same account", fontsize=10, weight="bold", transform=ax.transAxes)
    ax.text(0.03, 0.56, f"KES {money:,.0f}", fontsize=21, color=COLORS["mine"], weight="bold", transform=ax.transAxes)
    ax.text(0.03, 0.35, "One farmer’s report of payment for land\nclaimed at 31 acres; not a compensation tariff.", fontsize=9, transform=ax.transAxes)
    fig.suptitle("Titanium resettlement evidence: reported scale, dispute, and individual testimony", x=0.01, ha="left", fontsize=13, weight="bold")
    fig.text(0.01, -0.012, "Sources: Global Press Journal (2016); Abuya (2016); Dialogue Earth (2024). Company responses and evidentiary limits are described in the paper.", fontsize=8, color="#44515A")
    fig.savefig(FIGURES / "displacement_evidence.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES / "displacement_evidence.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_institution_timeline() -> None:
    data = pd.read_csv(DATA / "agency_timeline.csv")
    records = [
        (2013, 3, "Arabuko elephant plan\nsets water, connectivity,\nmonitoring tasks", COLORS["wildlife"]),
        (2021, 2, "Chakama residents report\nlimited response during\nincursion", COLORS["community"]),
        (2022.9, 1, "Waweru placed on leave;\nKanga becomes acting DG", COLORS["agency"]),
        (2023.6, 3, "National plan records\nSokoke water and corridor\nmonitoring gaps", COLORS["wildlife"]),
        (2023.7, 1, "Kanga appointed DG;\nLemarkoko leads KFS", COLORS["agency"]),
        (2025.55, 2, "Kwale mine closes;\npost-mine transition begins", COLORS["mine"]),
        (2026.02, 3, "Post-mining land-use\nroadmap launched", COLORS["mine"]),
    ]
    fig, ax = plt.subplots(figsize=(12, 5.5), layout="constrained")
    lane_names = {1: "Leadership", 2: "Community / mine events", 3: "Plans / institutional record"}
    for lane, label in lane_names.items():
        ax.axhline(lane, color="#E0E5E8", linewidth=0.8, zorder=0)
        ax.text(2012.2, lane, label, ha="right", va="center", fontsize=8, color="#52606A")
    for year, lane, label, color in records:
        ax.scatter(year, lane, s=58, color=color, zorder=3)
        yoff = 0.22 if lane != 2 else -0.31
        ax.annotate(label, (year, lane), xytext=(0, 30 if yoff > 0 else -34), textcoords="offset points", ha="center", va="bottom" if yoff > 0 else "top", fontsize=8, color="#24313A")
    ax.set_xlim(2012, 2027)
    ax.set_ylim(0.3, 3.85)
    ax.set_xticks(range(2013, 2027, 2))
    ax.set_yticks([])
    ax.set_xlabel("Year")
    ax.set_title("Conservation and mining accountability timeline", loc="left", weight="bold")
    ax.grid(axis="x", color="#EFF1F2")
    ax.text(0.01, 0.02, "Named leaders are listed in agency_timeline.csv. Institutional gaps are not personal misconduct findings.", transform=ax.transAxes, fontsize=8, color="#44515A")
    fig.savefig(FIGURES / "accountability_timeline.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES / "accountability_timeline.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_actor_network() -> None:
    nodes = pd.read_csv(DATA / "network_nodes.csv")
    edges = pd.read_csv(DATA / "network_edges.csv")
    positions = {row.node_id: (row.plot_x, row.plot_y) for row in nodes.itertuples()}
    colors_by_type = {
        "state-agency": COLORS["agency"],
        "research-agency": "#4B83A6",
        "community": COLORS["community"],
        "community-site": "#D98465",
        "ecological-site": COLORS["wildlife"],
        "extractive-project": COLORS["mine"],
        "public-process": COLORS["gray"],
        "cultural-ecological-site": COLORS["heritage"],
    }
    fig, ax = plt.subplots(figsize=(12, 7), layout="constrained")
    for edge in edges.itertuples():
        x1, y1 = positions[edge.from_id]
        x2, y2 = positions[edge.to_id]
        color = "#C65D3A" if "allegation" in edge.evidence_class or "reported" in edge.evidence_class else "#6B7780"
        style = "--" if "investigative question" in edge.evidence_class or "allegation" in edge.evidence_class else "-"
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops={"arrowstyle": "->", "color": color, "lw": 1.1, "linestyle": style, "alpha": 0.72, "shrinkA": 22, "shrinkB": 22}, zorder=1)
    for row in nodes.itertuples():
        x, y = positions[row.node_id]
        color = colors_by_type.get(row.node_type, COLORS["gray"])
        ax.scatter(x, y, s=520, color=color, edgecolor="white", linewidth=1.2, zorder=3)
        ax.text(x, y, row.graph_label, ha="center", va="center", color="white", fontsize=7.5, weight="bold", wrap=True, zorder=4)
    ax.set_xlim(-0.8, 7.3)
    ax.set_ylim(-1.7, 2.7)
    ax.axis("off")
    ax.set_title("Evidence-linked actors, places and processes", loc="left", weight="bold", fontsize=14)
    ax.text(0.01, 0.02, "Solid = documented mandate/process or published account. Dashed red = reported claim or question. Edges do not assert causation.", transform=ax.transAxes, fontsize=8, color="#44515A")
    fig.savefig(FIGURES / "evidence_network.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES / "evidence_network.pdf", bbox_inches="tight")
    plt.close(fig)


SCENE_REQUESTS = [
    {
        "scene_id": "arabuko_sokoke_latest",
        "label": "Arabuko-Sokoke Forest, Kilifi",
        "bbox": [39.80, -3.40, 39.91, -3.29],
        "datetime": "2025-01-01/2026-10-14",
        "context": "Forest and surrounding coastal agricultural mosaic; not an elephant-route map.",
    },
    {
        "scene_id": "kwale_mine_2024",
        "label": "Kwale Mineral Sands project area, 2024",
        "bbox": [39.40, -4.44, 39.52, -4.33],
        "datetime": "2024-01-01/2024-12-31",
        "context": "Mine was still operating during this period; crop is approximate and not the legal lease boundary.",
    },
    {
        "scene_id": "kwale_mine_latest",
        "label": "Kwale Mineral Sands project area, post-closure",
        "bbox": [39.40, -4.44, 39.52, -4.33],
        "datetime": "2025-01-01/2026-10-14",
        "context": "Post-mining closure imagery; visual appearance alone is not a rehabilitation audit.",
    },
    {
        "scene_id": "takaungu_latest",
        "label": "Takaungu / Vipingo coast, Kilifi",
        "bbox": [39.79, -3.74, 39.91, -3.63],
        "datetime": "2025-01-01/2026-10-14",
        "context": "Coastal landscape reference only; does not delineate plantation ownership or Majajani Farms.",
    },
]


def sentinel_crop(catalog: Client, request: dict[str, Any]) -> dict[str, Any] | None:
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=request["bbox"],
        datetime=request["datetime"],
        query={"eo:cloud_cover": {"lt": 25}},
        max_items=30,
    )
    aoi = box(*request["bbox"])
    items = [item for item in search.items() if shape(item.geometry).covers(aoi)]
    if not items:
        print(f"No cloud-screened Sentinel-2 scene fully covers {request['scene_id']} AOI")
        return None
    # Scene-wide cloud metadata can hide a cloudy study-site crop. Use the
    # scene classification layer to rank only pixels inside the chosen AOI.
    scored_items: list[tuple[float, float, Any]] = []
    for candidate in items:
        try:
            pc.sign_inplace(candidate)
            with rasterio.open(candidate.assets["SCL"].href) as scl_src:
                scl_bounds = transform_bounds("EPSG:4326", scl_src.crs, *request["bbox"], densify_pts=21)
                scl_window = from_bounds(*scl_bounds, transform=scl_src.transform).round_offsets().round_lengths()
                scl = scl_src.read(1, window=scl_window, boundless=True, fill_value=0)
            valid = (scl != 0) & (scl != 1)
            cloudy = np.isin(scl, [3, 8, 9, 10])
            local_cloud = 100.0 * np.count_nonzero(cloudy & valid) / max(np.count_nonzero(valid), 1)
            scored_items.append((local_cloud, -candidate.datetime.timestamp(), candidate))
        except Exception as exc:
            print(f"AOI cloud screen skipped {candidate.id}: {exc}")
    if not scored_items:
        print(f"No Sentinel-2 scene could be screened for {request['scene_id']}")
        return None
    scored_items.sort(key=lambda score: (score[0], score[1]))
    local_cloud, _, item = scored_items[0]
    with rasterio.open(item.assets["visual"].href) as src:
        bounds = transform_bounds("EPSG:4326", src.crs, *request["bbox"], densify_pts=21)
        window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
        rgb = src.read([1, 2, 3], window=window, boundless=True, fill_value=0)
        crs = str(src.crs)
        resolution = float(abs(src.res[0]))
    image = np.moveaxis(rgb, 0, -1).astype(float)
    if image.size == 0:
        print(f"Empty crop for {request['scene_id']}")
        return None
    # Stretch within each band for clear viewing while keeping scene content.
    for band in range(3):
        values = image[:, :, band]
        valid = values[values > 0]
        if valid.size:
            lo, hi = np.percentile(valid, [2, 98])
            image[:, :, band] = np.clip((values - lo) / max(hi - lo, 1) * 255, 0, 255)
    image = image.astype(np.uint8)
    filename = f"{request['scene_id']}_{item.datetime:%Y%m%d}.png"
    output = IMAGERY / filename
    plt.imsave(output, image)
    return {
        "scene_id": request["scene_id"],
        "label": request["label"],
        "item_id": item.id,
        "acquisition_date": item.datetime.date().isoformat(),
        "scene_cloud_cover_percent": round(float(item.properties.get("eo:cloud_cover", float("nan"))), 1),
        "aoi_cloud_or_shadow_percent": round(local_cloud, 1),
        "nominal_ground_sample_distance_m": round(resolution, 2),
        "asset": "Sentinel-2 L2A visual true-color (R/G/B)",
        "processing": "per-band 2–98 percentile contrast stretch for display",
        "bbox_wgs84": json.dumps(request["bbox"]),
        "output_file": f"imagery/{filename}",
        "context_note": request["context"],
        "catalog": STAC_URL,
        "data_terms": "Copernicus Sentinel data terms; attribution in README and figure caption",
        "source_crs": crs,
    }


def build_satellite_panels(skip: bool) -> None:
    catalog = Client.open(STAC_URL)
    scenes: list[dict[str, Any]] = []
    if not skip:
        for request in SCENE_REQUESTS:
            try:
                scene = sentinel_crop(catalog, request)
                if scene:
                    scenes.append(scene)
            except Exception as exc:
                print(f"Could not retrieve {request['scene_id']}: {exc}")
    scene_path = DATA / "imagery_scenes.csv"
    if scenes:
        pd.DataFrame(scenes).to_csv(scene_path, index=False)
        keep = {ROOT / scene["output_file"] for scene in scenes}
        for pattern in ("arabuko_sokoke_latest_*.png", "kwale_mine_latest_*.png", "takaungu_latest_*.png"):
            for stale in IMAGERY.glob(pattern):
                if stale not in keep:
                    stale.unlink()
        columns = 2
        rows = int(np.ceil(len(scenes) / columns))
        fig, axes = plt.subplots(rows, columns, figsize=(12, 5.6 * rows), squeeze=False, layout="constrained")
        for ax, scene in zip(axes.flat, scenes):
            image = plt.imread(ROOT / scene["output_file"])
            ax.imshow(image)
            ax.set_title(f"{scene['label']} · {scene['acquisition_date']} · {scene['aoi_cloud_or_shadow_percent']}% crop cloud/shadow", fontsize=10, weight="bold")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(0.01, 0.01, "True-colour Sentinel-2 L2A · 10 m source GSD · display stretch", transform=ax.transAxes, fontsize=8, color="white", bbox={"facecolor": "#17232B", "alpha": 0.72, "pad": 3})
        for ax in axes.flat[len(scenes):]:
            ax.axis("off")
        fig.suptitle("Selected Sentinel-2 site views (reference crops, not boundaries)", x=0.01, ha="left", fontsize=13, weight="bold")
        fig.savefig(FIGURES / "sentinel2_site_views.png", dpi=220, bbox_inches="tight")
        fig.savefig(FIGURES / "sentinel2_site_views.pdf", bbox_inches="tight")
        plt.close(fig)
    elif not scene_path.exists():
        pd.DataFrame(columns=["scene_id", "label", "item_id", "acquisition_date", "scene_cloud_cover_percent", "aoi_cloud_or_shadow_percent", "nominal_ground_sample_distance_m", "asset", "output_file", "context_note", "catalog", "data_terms"]).to_csv(scene_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-imagery", action="store_true", help="Build vector/data plots without online Sentinel-2 downloads")
    args = parser.parse_args()
    FIGURES.mkdir(parents=True, exist_ok=True)
    IMAGERY.mkdir(parents=True, exist_ok=True)
    boundaries = ensure_boundaries()
    plot_regional_map(boundaries)
    plot_elephant_estimates()
    plot_displacement_evidence()
    plot_institution_timeline()
    plot_actor_network()
    build_satellite_panels(args.skip_imagery)
    print(f"Figures and imagery metadata written under {ROOT}")


if __name__ == "__main__":
    main()
