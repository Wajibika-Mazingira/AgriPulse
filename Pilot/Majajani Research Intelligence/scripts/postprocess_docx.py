#!/usr/bin/env python3
"""Add front-matter page breaks and page-number fields to a Pandoc DOCX.

The page breaks are set in OOXML. LibreOffice's UNO bridge adds native PAGE
fields so that the PDF and editable DOCX display matching page numbers.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    import uno
    from com.sun.star.beans import PropertyValue
except ImportError as exc:  # pragma: no cover - environment-specific dependency
    raise SystemExit(
        "The postprocessor requires the system Python LibreOffice UNO bridge "
        "(on Debian, install python3-uno)."
    ) from exc


W_URI = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_URI = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
W = f"{{{W_URI}}}"
ET.register_namespace("w", W_URI)
ET.register_namespace("r", R_URI)

PAGE_STARTS = {
    "Abstract",
    "Table of Contents",
    "List of Figures",
    "List of Tables",
    "List of Appendices",
    "Table of Authorities",
    "Abbreviations and Key Terms",
    "1. Introduction: purpose, research questions and scope",
    "Appendix A. The train at the sisal processing/loom area",
    "Appendix B. Foot-and-mouth disease: an exploratory historical note",
    "Author declarations, ethics and data availability",
    "References",
}


def _text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.iter(f"{W}t")).strip()


def _add_pagebreak(paragraph: ET.Element) -> None:
    properties = paragraph.find(f"{W}pPr")
    if properties is None:
        properties = ET.Element(f"{W}pPr")
        paragraph.insert(0, properties)
    if properties.find(f"{W}pageBreakBefore") is not None:
        return
    # OOXML orders pageBreakBefore after pStyle/keepNext/keepLines and before
    # spacing/indent/alignment properties.
    eligible = {"pStyle", "keepNext", "keepLines"}
    insert_at = 0
    for index, child in enumerate(list(properties)):
        if child.tag.startswith(W) and child.tag[len(W):] in eligible:
            insert_at = index + 1
    properties.insert(insert_at, ET.Element(f"{W}pageBreakBefore"))


def _insert_structural_breaks(docx_path: Path) -> int:
    with zipfile.ZipFile(docx_path, "r") as source:
        entries = [(item, source.read(item.filename)) for item in source.infolist()]
    updated: list[tuple[zipfile.ZipInfo, bytes]] = []
    count = 0
    for item, payload in entries:
        if item.filename == "word/document.xml":
            document = ET.fromstring(payload)
            for paragraph in document.iter(f"{W}p"):
                properties = paragraph.find(f"{W}pPr")
                style = properties.find(f"{W}pStyle") if properties is not None else None
                is_heading = style is not None and style.get(f"{W}val", "").startswith("Heading")
                if is_heading and _text(paragraph) in PAGE_STARTS:
                    already = properties is not None and properties.find(f"{W}pageBreakBefore") is not None
                    if not already:
                        _add_pagebreak(paragraph)
                        count += 1
            payload = ET.tostring(document, encoding="utf-8", xml_declaration=True)
        updated.append((item, payload))

    temporary = docx_path.with_suffix(".pagebreaks.tmp.docx")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as output:
        for item, payload in updated:
            output.writestr(item, payload)
    os.replace(temporary, docx_path)
    return count


def _property(name: str, value: object) -> PropertyValue:
    result = PropertyValue()
    result.Name = name
    result.Value = value
    return result


def _add_page_fields(docx_path: Path) -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]

    profile_dir = Path(tempfile.mkdtemp(prefix="majajani-lo-profile-"))
    profile_url = profile_dir.as_uri()
    process = subprocess.Popen(
        [
            "libreoffice",
            "--headless",
            "--norestore",
            "--nodefault",
            "--nofirststartwizard",
            f"-env:UserInstallation={profile_url}",
            f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ServiceManager",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    document = None
    count = 0
    try:
        local_context = uno.getComponentContext()
        resolver = local_context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_context
        )
        context = None
        for _ in range(40):
            try:
                context = resolver.resolve(
                    f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext"
                )
                break
            except Exception:
                time.sleep(0.25)
        if context is None:
            raise RuntimeError("Could not connect to the temporary LibreOffice instance")
        desktop = context.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", context
        )
        document = desktop.loadComponentFromURL(
            uno.systemPathToFileUrl(str(docx_path)),
            "_blank",
            0,
            (_property("Hidden", True), _property("ReadOnly", False)),
        )
        page_styles = document.getStyleFamilies().getByName("PageStyles")
        for style_name in page_styles.getElementNames():
            style = page_styles.getByName(style_name)
            style.FooterIsOn = True
            footer = style.FooterText
            footer.setString("")
            cursor = footer.createTextCursor()
            cursor.ParaAdjust = uno.Enum("com.sun.star.style.ParagraphAdjust", "CENTER")
            footer.insertString(cursor, "— ", 0)
            page_field = document.createInstance("com.sun.star.text.TextField.PageNumber")
            page_field.NumberingType = uno.getConstantByName("com.sun.star.style.NumberingType.ARABIC")
            footer.insertTextContent(cursor, page_field, False)
            cursor.gotoEnd(False)
            footer.insertString(cursor, " —", 0)
            count += 1
        document.getTextFields().refresh()
        document.store()
        document.close(True)
        document = None
    finally:
        if document is not None:
            try:
                document.close(True)
            except Exception:
                pass
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
        shutil.rmtree(profile_dir, ignore_errors=True)
    return count


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/postprocess_docx.py PATH.docx", file=sys.stderr)
        return 2
    path = Path(sys.argv[1]).resolve()
    if not path.is_file():
        print(f"Missing DOCX: {path}", file=sys.stderr)
        return 2
    breaks = _insert_structural_breaks(path)
    styles = _add_page_fields(path)
    print(f"Applied {breaks} structural page breaks and page-number fields to {styles} page styles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
