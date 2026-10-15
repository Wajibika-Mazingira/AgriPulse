PYTHON ?= python3
UNO_PYTHON ?= /usr/bin/python3
R ?= Rscript
PANDOC ?= pandoc
LIBREOFFICE ?= libreoffice
MANUSCRIPT := manuscript/Majajani_Farms_Research_Perspective.md
EXPORT_DIR := manuscript/exports

.PHONY: all visuals visuals-offline manuscript validate fingerprint

all: visuals manuscript validate

visuals:
	$(PYTHON) visuals/scripts/build_visuals.py
	$(R) visuals/scripts/build_visuals.R

visuals-offline:
	$(PYTHON) visuals/scripts/build_visuals.py --skip-imagery
	$(R) visuals/scripts/build_visuals.R

manuscript:
	$(PANDOC) "$(MANUSCRIPT)" --standalone --resource-path="manuscript:." --output "$(EXPORT_DIR)/Majajani_Farms_Research_Perspective_Final.docx"
	$(UNO_PYTHON) scripts/postprocess_docx.py "$(EXPORT_DIR)/Majajani_Farms_Research_Perspective_Final.docx"
	$(RM) "$(EXPORT_DIR)/Majajani_Farms_Research_Perspective_Final.pdf"
	$(LIBREOFFICE) --headless --convert-to pdf --outdir "$(EXPORT_DIR)" "$(EXPORT_DIR)/Majajani_Farms_Research_Perspective_Final.docx"

validate:
	$(PYTHON) scripts/validate_repository.py
	$(PYTHON) scripts/fingerprint_release.py --verify

fingerprint:
	$(PYTHON) scripts/fingerprint_release.py --write
