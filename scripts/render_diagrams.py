"""Render repository PlantUML sources and an offline, accessible HTML catalogue."""

import re
import struct
import subprocess
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def main():
    directory = Path(__file__).resolve().parents[1] / "docs" / "diagrams"
    sources = sorted(directory.glob("*.puml"))
    assert sources, "No PlantUML sources found"
    subprocess.run(["plantuml", "--check-syntax", *map(str, sources)], check=True)
    subprocess.run(["plantuml", "--svg", *map(str, sources)], check=True)
    figures, links, all_ids = [], [], []
    for source in sources:
        slug = source.stem
        title = next(
            line[6:] for line in source.read_text().splitlines() if line.startswith("title ")
        )
        path = source.with_suffix(".svg")
        root = ET.fromstring(path.read_text())
        assert root.tag == f"{{{SVG}}}svg"
        ids = {node.get("id"): f"{slug}-{node.get('id')}" for node in root.iter() if node.get("id")}
        for node in root.iter():
            for key, value in list(node.attrib.items()):
                if key == "id":
                    node.set(key, ids[value])
                elif value.startswith("#") and value[1:] in ids:
                    node.set(key, "#" + ids[value[1:]])
                elif "url(#" in value:
                    node.set(
                        key,
                        re.sub(
                            r"url\(#([^)]+)\)",
                            lambda m, mapping=ids: f"url(#{mapping[m[1]]})",
                            value,
                        ),
                    )
        root.set("role", "img")
        root.set("aria-labelledby", f"{slug}-title {slug}-desc")
        heading = ET.Element(f"{{{SVG}}}title", id=f"{slug}-title")
        heading.text = title
        description = ET.Element(f"{{{SVG}}}desc", id=f"{slug}-desc")
        description.text = (
            title
            + ". Boundaries describe application responsibilities; model judgments remain fallible."
        )
        root.insert(0, heading)
        root.insert(1, description)
        svg = ET.tostring(root, encoding="unicode")
        path.write_text(svg + "\n", encoding="utf-8")
        subprocess.run(
            [
                "rsvg-convert",
                str(path),
                "--background-color",
                "white",
                "--output",
                str(source.with_suffix(".png")),
            ],
            check=True,
        )
        width, height = struct.unpack(">II", source.with_suffix(".png").read_bytes()[16:24])
        view = list(map(float, root.attrib["viewBox"].split()))
        assert abs(width / view[2] - height / view[3]) < 0.02, f"Clipped render: {slug}"
        all_ids.extend(node.get("id") for node in root.iter() if node.get("id"))
        links.append(f'<li><a href="#{slug}">{escape(title)}</a></li>')
        downloads = " / ".join(
            f'<a href="{slug}.{ext}">{ext.upper()}</a>' for ext in ("puml", "svg", "png")
        )
        figures.append(
            f'<section id="{slug}"><h2>{escape(title)}</h2><p>{downloads}</p>'
            f'<div class="diagram">{svg}</div></section>'
        )
    assert len(all_ids) == len(set(all_ids)), "Duplicate SVG IDs in catalogue"
    page = """<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agentic Drink Book diagrams</title>
<style>
body {margin:0 auto; padding:32px 24px; max-width:1400px;
font:17px/1.55 system-ui,sans-serif; color:#24323d; background:#fafafa}
a {color:#154f82} h1,h2 {line-height:1.25} nav {padding:16px 24px; background:#e8f0fa}
section {margin:40px 0; padding:20px; background:white; border:1px solid #c9d2d8}
.diagram {overflow:auto} .diagram svg {display:block; max-width:none}
a:focus-visible {outline:3px solid #154f82; outline-offset:3px}
@media print {body {padding:0} nav {display:none} section {break-before:page}
.diagram svg {max-width:100%; height:auto}}
</style>
<header><h1>Agentic Drink Book diagrams</h1>
<p>Start with L0 (13), L1 (14), and the functional view (15), then follow the detailed views.
Policy 2.1.0. Four runtime LLM roles and one optional evaluation auditor.</p>
<p>Known limitations include incorrect recipes, audit false alarms, and accepted-refusal retention.
These diagrams describe controls, not a guarantee of model correctness.</p>
<p><a href="10-functional-flow.excalidraw">Editable functional scene</a> /
<a href="11-trust-boundaries.excalidraw">Editable trust-boundary scene</a></p></header>
<nav aria-label="Diagram catalogue"><ol>"""
    page += "".join(links) + "</ol></nav><main>" + "".join(figures) + "</main></html>\n"
    (directory / "index.html").write_text(page, encoding="utf-8")
    print(f"Rendered {len(sources)} diagrams as SVG and PNG; built offline index.html.")


if __name__ == "__main__":
    main()
