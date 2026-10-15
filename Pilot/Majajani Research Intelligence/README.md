# Majajani Research Intelligence

An evidence-led, reproducible companion repository for William Majanja’s documentary perspective on banana-based soil building, Kilifi elephants and water, Mijikenda Kaya stewardship, and titanium-related land dispossession in Kwale.

The repository combines the manuscript, final exports, cited data tables, graph-ready actor relationships, regional mapping, Sentinel-2 imagery, and reproducible Python and R figures. It is organized so a researcher can audit the source of each number and distinguish documented findings from community testimony and unresolved questions.

## Main deliverables

- [Manuscript source](manuscript/Majajani_Farms_Research_Perspective.md)
- [Final DOCX](manuscript/exports/Majajani_Farms_Research_Perspective_Final.docx)
- [Final PDF](manuscript/exports/Majajani_Farms_Research_Perspective_Final.pdf)
- [Visualisation methods and data guide](visuals/README.md)
- [Python build script](visuals/scripts/build_visuals.py)
- [R build script](visuals/scripts/build_visuals.R)
- [Source register](visuals/data/sources.csv)
- [Agency-leadership timeline](visuals/data/agency_timeline.csv)
- [Graph nodes](visuals/data/network_nodes.csv) and [edges](visuals/data/network_edges.csv)
- [SHA-256 fingerprint manifest](integrity/SHA256SUMS)

## What the evidence shows

- KWS/WRTI’s 2023 National Elephant Action Plan repeats a **2017 Arabuko-Sokoke dung-count estimate of 215 elephants**; Kinyanjui (2020) reports a 95% confidence interval of 145–318. The plan also identifies inadequate water points, incomplete carrying-capacity information, weak Arabuko–Tsavo monitoring and poor implementation of corridor recommendations.
- A 2021 report from Chakama/Adu describes residents’ accounts of Tsavo East elephants raiding farms and communal water points, including bananas. It reports residents’ view that a response with six rangers was inadequate; this is not a court finding against KWS or a GPS record of an elephant route.
- KWS leadership named by period in the manuscript: **John Waweru** was Director General during the 2021 incident report; **Erustus Kanga** became acting Director General in December 2022 and was appointed effective 1 August 2023. For the forest-management and enforcement concerns, **Alex Lemarkoko** became KFS Chief Conservator of Forests on 2 August 2023. The source-based agency timeline identifies further leaders and evidentiary limits.
- The operating titanium mine and reported resettlement disputes are in **Kwale**, particularly the Maumba–Nguluku project area. Reports document relocation and compensation disputes, but counts reported in households, people and individual testimony are not added into a single total. The evidence reviewed does not prove that the Kwale mine occupied a named Kaya forest or caused Kilifi elephant movements.
- *Mokono/Mkono wa Tembo* is recorded as “elephant’s hand” in literal Swahili wording and as an elephant-trunk resemblance in the author’s local interpretation. Whether elephants historically ate that specific plant is left as a question for community-led oral history and ecological research.
- A declassified-in-part January 1987 CIA assessment, written after the failed 1982 Air Force-led coup attempt, describes Moi-era security consolidation, elite land concentration, government graft and U.S.–Kenya military access. The paper uses it as contemporaneous U.S. intelligence analysis and a reason to examine postcolonial power and accountability; it does not treat it as proof of CIA direction of local land decisions. The scan and official CIA FOIA record are registered as `src28`. The visible 25X1/25X6 markings and three page-denial notices are catalogued, but absent wording is not reconstructed.
- The comparison now distinguishes Guatemala’s CIA-backed 1954 coup from the domestic 2024 Gen Z-led protests and police violence in Kenya. KNCHR and the U.S. State Department document protest deaths, injuries and accountability concerns; the sources do not establish that the movement was an armed insurrection or that the CIA directed it. Guatemala’s Commission for Historical Clarification findings concern the later 1960–1996 conflict, not a casualty count for the coup.
- Haiti is treated as an international-policing comparison with separate missions: MINUSTAH (a UN peacekeeping mission) and the Kenya-led MSS (a UN-authorized but non-UN-commanded force) are not interchangeable. The record shows both security/police support and significant oversight and human-rights failures.
- Israel-related claims are bounded to documented public diplomacy and attributed reporting: Ruto visited Israel and the Western Wall in 2023 and publicly described Israel as a friend while supporting a two-state solution; 2023 investigative reporting documented Team Jorge’s demonstration of access to accounts belonging to a Ruto aide. The reviewed sources do not establish Israeli financing or government direction of Kenyan candidates or that all candidates visited the Wall.

The manuscript reports institutional shortcomings where official plans or reporting document them, while distinguishing those from allegations and court findings. It does not infer personal culpability from an agency’s leadership tenure.

## Repository layout

```text
manuscript/
  Majajani_Farms_Research_Perspective.md
  exports/                         final DOCX and PDF
visuals/
  data/                            CSV evidence, graph and source tables; CIA.pdf source scan
  figures/                         generated Python and R plots/maps
  imagery/                         selected Sentinel-2 true-colour crops
  scripts/                         reproducible Python and R builders
scripts/
  validate_repository.py           local integrity checks
  fingerprint_release.py           SHA-256 baseline writer/verifier
  postprocess_docx.py              DOCX page-break/page-number postprocessor
integrity/
  SHA256SUMS                       release fingerprint baseline
  README.md                        fingerprint scope and limitations
Makefile                            reproducible build targets
RIGHTS.md                           source and reuse notes
CITATION.cff                        citation metadata
```

## Rebuild

Requirements: Python 3.11 or later, R (base installation only), Pandoc and LibreOffice. DOCX page-break and page-number formatting uses the LibreOffice UNO bridge from system Python (on Debian, install `python3-uno`; override `UNO_PYTHON` if its interpreter is elsewhere). Python package versions are declared in `visuals/requirements.txt`. Downloading new Sentinel-2 imagery and geoBoundaries geometry requires internet access; the selected crops, scene metadata and boundary GeoJSON are already included.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r visuals/requirements.txt
make all
```

To rebuild plots/maps without online imagery:

```sh
make visuals-offline
```

`make validate` checks CSV structure and source/graph references, IEEE citation numbering and first-citation order, figure and imagery files, the final export assets and the SHA-256 fingerprint. The build postprocessor adds stable page breaks for the cover/front matter and page-number fields to DOCX. The R script emits separate `*_R.png` figures; the manuscript embeds the six selected Python-generated figures.

Run `python3 scripts/fingerprint_release.py --verify` to compare repository files to the recorded SHA-256 baseline. After an approved edit and rebuild, refresh it with `--write`. The hash verifies file identity, not AI authorship; details and limitations are in [`integrity/README.md`](integrity/README.md).

## Evidence and mapping guardrails

The map uses public reference points and 2020 geoBoundaries county outlines. It does not show the private Majajani Farms parcel, mine-lease extents, individual land titles, household locations or restricted Kaya knowledge. The Arabuko–Tsavo line is schematic because the national plan says the linkage is not robustly monitored and the sources reviewed do not provide a route geometry. The land-displacement graph records documented processes, published accounts and open questions as different edge types; it is not a causal model.

Sentinel-2 panels show selected L2A true-colour crops at nominal 10 m ground-sample distance. The Kwale images date from 29 May 2024 and 29 January 2025; neither provides a pre-mining baseline. Their appearance alone cannot verify an environmental impact or rehabilitation outcome. Scene IDs, dates, crop boxes and crop cloud/shadow estimates are in `visuals/data/imagery_scenes.csv`.

## Citation

See [`CITATION.cff`](CITATION.cff). The companion data registry records references used for the visuals; the full manuscript bibliography records article sources.
