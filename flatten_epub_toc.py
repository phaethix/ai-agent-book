#!/usr/bin/env python3
"""Flatten an EPUB table of contents within each chapter group."""

import copy
import os
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET


XHTML = "http://www.w3.org/1999/xhtml"
EPUB = "http://www.idpf.org/2007/ops"
NCX = "http://www.daisy.org/z3986/2005/ncx/"

ET.register_namespace("", XHTML)
ET.register_namespace("epub", EPUB)


def direct_children(element, tag):
    return [child for child in element if child.tag == tag]


def flatten_nav(data):
    root = ET.fromstring(data)
    nav = next(
        element
        for element in root.iter(f"{{{XHTML}}}nav")
        if element.get(f"{{{EPUB}}}type") == "toc"
    )
    top_list = next(child for child in nav if child.tag == f"{{{XHTML}}}ol")

    for group in direct_children(top_list, f"{{{XHTML}}}li"):
        nested_lists = direct_children(group, f"{{{XHTML}}}ol")
        if not nested_lists:
            continue

        descendants = []
        for nested_list in nested_lists:
            descendants.extend(nested_list.iter(f"{{{XHTML}}}li"))
            group.remove(nested_list)

        flat_list = ET.Element(f"{{{XHTML}}}ol", {"class": "toc"})
        for descendant in descendants:
            flat_item = copy.deepcopy(descendant)
            for child in direct_children(flat_item, f"{{{XHTML}}}ol"):
                flat_item.remove(child)
            flat_list.append(flat_item)
        group.append(flat_list)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def flatten_ncx(data):
    ET.register_namespace("", NCX)
    root = ET.fromstring(data)
    nav_map = root.find(f"{{{NCX}}}navMap")

    for group in direct_children(nav_map, f"{{{NCX}}}navPoint"):
        children = direct_children(group, f"{{{NCX}}}navPoint")
        if not children:
            continue

        descendants = []
        for child in children:
            descendants.extend(child.iter(f"{{{NCX}}}navPoint"))
            group.remove(child)

        for descendant in descendants:
            flat_point = copy.deepcopy(descendant)
            for child in direct_children(flat_point, f"{{{NCX}}}navPoint"):
                flat_point.remove(child)
            group.append(flat_point)

    depth = root.find(f".//{{{NCX}}}meta[@name='dtb:depth']")
    if depth is not None:
        depth.set("content", "2")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rewrite_epub(path):
    replacements = {}
    with zipfile.ZipFile(path) as source:
        names = set(source.namelist())
        if "EPUB/nav.xhtml" not in names or "EPUB/toc.ncx" not in names:
            raise RuntimeError("EPUB navigation files not found")
        replacements["EPUB/nav.xhtml"] = flatten_nav(source.read("EPUB/nav.xhtml"))
        replacements["EPUB/toc.ncx"] = flatten_ncx(source.read("EPUB/toc.ncx"))

        directory = os.path.dirname(os.path.abspath(path))
        descriptor, temporary_path = tempfile.mkstemp(suffix=".epub", dir=directory)
        os.close(descriptor)
        try:
            with zipfile.ZipFile(temporary_path, "w") as target:
                for info in source.infolist():
                    target.writestr(info, replacements.get(info.filename, source.read(info.filename)))
            os.replace(temporary_path, path)
        except BaseException:
            os.unlink(temporary_path)
            raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} BOOK.epub")
    rewrite_epub(sys.argv[1])
