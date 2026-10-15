#!/usr/bin/env python3
"""Dependency-light integrity checks for the packaged research repository."""

from __future__ import annotations

import csv
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VISUALS = ROOT / "visuals"
DATA = VISUALS / "data"
FIGURES = VISUALS / "figures"
IMAGERY = VISUALS / "imagery"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path.relative_to(ROOT)}")
        if any(None in row for row in rows):
            raise ValueError(f"Inconsistent CSV row width: {path.relative_to(ROOT)}")
        return rows


def check_tables() -> int:
    source_rows = read_csv(DATA / "sources.csv")
    source_ids = {row["source_id"] for row in source_rows}
    if len(source_ids) != len(source_rows):
        raise ValueError("Duplicate source_id in sources.csv")

    references = {
        "sites.csv": "source_id",
        "elephant_estimates.csv": "source_id",
        "displacement_evidence.csv": "source_id",
        "agency_timeline.csv": "source_id",
        "network_nodes.csv": "source_id",
        "network_edges.csv": "source_id",
    }
    for filename, column in references.items():
        for row in read_csv(DATA / filename):
            for source_id in row[column].split(";"):
                if source_id and source_id not in source_ids:
                    raise ValueError(f"Unknown {source_id} in {filename}")

    nodes = read_csv(DATA / "network_nodes.csv")
    node_ids = {row["node_id"] for row in nodes}
    for row in read_csv(DATA / "network_edges.csv"):
        if row["from_id"] not in node_ids or row["to_id"] not in node_ids:
            raise ValueError(f"Unresolved graph edge: {row['edge_id']}")
    return len(source_ids)


def check_citations() -> int:
    manuscript = ROOT / "manuscript/Majajani_Farms_Research_Perspective.md"
    text = manuscript.read_text(encoding="utf-8")
    if "## References" not in text:
        raise ValueError("Manuscript is missing its References section")
    body, reference_tail = text.split("## References", 1)
    visible_references = reference_tail.split("<!-- Archived", 1)[0]
    reference_numbers = [
        int(value)
        for value in re.findall(r"^\[(\d+)\]\s+", visible_references, re.MULTILINE)
    ]
    if not reference_numbers or reference_numbers != list(range(1, len(reference_numbers) + 1)):
        raise ValueError("IEEE references are not numbered consecutively from [1]")

    reference_set = set(reference_numbers)
    cite_pattern = re.compile(
        r"\[(\d+)(?:,\s*[^]]*)?\]"
        r"(?:\s*[–-]\s*\[(\d+)\])?"
    )
    cited_in_order: list[int] = []
    for match in cite_pattern.finditer(body):
        start = int(match.group(1))
        end = int(match.group(2) or start)
        # Bracketed years in legal citations, such as [2026] KECA, are not
        # numeric references. A citation-like number within the bibliography
        # range, however, must resolve to a numbered reference.
        if start not in reference_set:
            if start > len(reference_numbers):
                continue
            raise ValueError(f"Unresolved in-text citation [{start}]")
        if end not in reference_set or end < start:
            raise ValueError(f"Invalid in-text citation range [{start}]–[{end}]")
        cited_in_order.extend(range(start, end + 1))

    first_citation_order = list(dict.fromkeys(cited_in_order))
    if first_citation_order != reference_numbers:
        raise ValueError(
            "IEEE reference numbering does not follow first-citation order "
            f"(first mismatch near {first_citation_order[:12]})"
        )

    author_date = re.compile(
        r"\([A-Z][^()\n]{0,180},\s*(?:19|20)\d{2}[a-z]?(?:\s*;|\s*\))"
    )
    legacy = author_date.search(body)
    if legacy:
        raise ValueError(f"Legacy author–date citation remains: {legacy.group(0)}")
    return len(reference_numbers)


def check_assets() -> tuple[int, int]:
    manuscript = ROOT / "manuscript/Majajani_Farms_Research_Perspective.md"
    text = manuscript.read_text(encoding="utf-8")
    image_links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    for link in image_links:
        target = (manuscript.parent / link).resolve()
        if not target.is_file():
            raise FileNotFoundError(f"Missing manuscript image: {link}")

    scene_rows = read_csv(DATA / "imagery_scenes.csv")
    for row in scene_rows:
        if row.get("output_file"):
            target = VISUALS / row["output_file"]
            if not target.is_file():
                raise FileNotFoundError(f"Missing satellite crop: {target.relative_to(ROOT)}")

    required = [
        DATA / "CIA.pdf",
        FIGURES / "regional_sites_map.png",
        FIGURES / "elephant_estimates.png",
        FIGURES / "displacement_evidence.png",
        FIGURES / "evidence_network.png",
        FIGURES / "sentinel2_site_views.png",
        FIGURES / "accountability_timeline.png",
        FIGURES / "regional_sites_map_R.png",
        FIGURES / "elephant_estimates_R.png",
        FIGURES / "displacement_evidence_R.png",
        FIGURES / "evidence_network_R.png",
        ROOT / "manuscript/exports/Majajani_Farms_Research_Perspective_Final.docx",
        ROOT / "manuscript/exports/Majajani_Farms_Research_Perspective_Final.pdf",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required deliverables: " + ", ".join(missing))

    docx = ROOT / "manuscript/exports/Majajani_Farms_Research_Perspective_Final.docx"
    with zipfile.ZipFile(docx) as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
        document_xml = archive.read("word/document.xml").decode("utf-8")
        footer_xml = archive.read("word/footer1.xml").decode("utf-8") if "word/footer1.xml" in archive.namelist() else ""
    if len(media) < len(image_links):
        raise ValueError(f"DOCX embeds {len(media)} images for {len(image_links)} manuscript figures")
    if "PAGE" not in footer_xml:
        raise ValueError("DOCX page-number footer field is missing")
    if document_xml.count('w:type="page"') < 8:
        raise ValueError("DOCX front matter/page-break formatting is incomplete")
    return len(image_links), len(media)


def main() -> int:
    sources = check_tables()
    citations = check_citations()
    figure_links, docx_media = check_assets()
    print(f"Validated {sources} registered sources, graph/data foreign keys and imagery records.")
    print(f"Validated {citations} IEEE references and first-citation order.")
    print(f"Validated {figure_links} manuscript figure links and {docx_media} embedded DOCX images.")
    print("Repository assets and final exports are present.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
