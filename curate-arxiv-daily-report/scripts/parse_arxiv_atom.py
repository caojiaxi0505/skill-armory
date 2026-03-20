#!/usr/bin/env python3
"""Parse an arXiv Atom feed into a normalized JSON structure."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_FEED_URL = "https://rss.arxiv.org/atom/cs.AI+cs.LG+cs.CL"
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
NS = {"atom": ATOM_NS, "arxiv": ARXIV_NS, "dc": DC_NS}
ABSTRACT_PREFIX_RE = re.compile(
    r"^arXiv:[^\s]+\s+Announce Type:\s*[^\s]+\s+Abstract:\s*",
    re.IGNORECASE,
)


def collapse_ws(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def normalize_abstract(raw_summary: str) -> str:
    cleaned = collapse_ws(raw_summary)
    return ABSTRACT_PREFIX_RE.sub("", cleaned).strip()


def derive_pdf_url(abs_url: str, pdf_url: str) -> str:
    if pdf_url:
        return pdf_url
    if abs_url.startswith("https://arxiv.org/abs/"):
        paper_id = abs_url.rsplit("/", 1)[-1]
        if paper_id:
            return f"https://arxiv.org/pdf/{paper_id}.pdf"
    return ""


def read_source(input_path: str | None, source_url: str | None) -> tuple[str, str]:
    if input_path:
        path = Path(input_path)
        return path.read_text(encoding="utf-8"), str(path.resolve())

    if source_url:
        request = urllib.request.Request(
            source_url,
            headers={"User-Agent": "curate-arxiv-daily-report/1.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8"), source_url

    if not sys.stdin.isatty():
        payload = sys.stdin.read()
        if payload.strip():
            return payload, "stdin"

    raise ValueError("Provide --input, --source-url, or Atom XML on stdin.")


def pick_links(entry: ET.Element) -> tuple[str, str]:
    abs_url = ""
    pdf_url = ""

    for link in entry.findall("atom:link", NS):
        href = link.attrib.get("href", "")
        rel = link.attrib.get("rel", "")
        title = link.attrib.get("title", "")
        link_type = link.attrib.get("type", "")

        if not abs_url and (rel == "alternate" or "/abs/" in href):
            abs_url = href

        if not pdf_url and (
            title.lower() == "pdf"
            or "/pdf/" in href
            or link_type == "application/pdf"
        ):
            pdf_url = href

    return abs_url, pdf_url


def pick_authors(entry: ET.Element) -> list[str]:
    authors = [
        collapse_ws(author.findtext("atom:name", default="", namespaces=NS))
        for author in entry.findall("atom:author", NS)
    ]
    authors = [author for author in authors if author]
    if authors:
        return authors

    creator = collapse_ws(entry.findtext("dc:creator", default="", namespaces=NS))
    if creator:
        return [part.strip() for part in creator.split(",") if part.strip()]

    return []


def parse_entry(entry: ET.Element) -> dict:
    abs_url, pdf_url = pick_links(entry)
    authors = pick_authors(entry)
    categories = []
    for category in entry.findall("atom:category", NS):
        term = collapse_ws(category.attrib.get("term"))
        if term and term not in categories:
            categories.append(term)

    primary = entry.find("arxiv:primary_category", NS)
    primary_category = collapse_ws(primary.attrib.get("term")) if primary is not None else ""
    raw_summary = collapse_ws(entry.findtext("atom:summary", default="", namespaces=NS))
    abstract = normalize_abstract(raw_summary)
    pdf_url = derive_pdf_url(abs_url, pdf_url)
    if not primary_category and categories:
        primary_category = categories[0]

    return {
        "id": collapse_ws(entry.findtext("atom:id", default="", namespaces=NS)),
        "title": collapse_ws(entry.findtext("atom:title", default="", namespaces=NS)),
        "abstract": abstract,
        "raw_summary": raw_summary,
        "published": collapse_ws(entry.findtext("atom:published", default="", namespaces=NS)),
        "updated": collapse_ws(entry.findtext("atom:updated", default="", namespaces=NS)),
        "authors": authors,
        "categories": categories,
        "primary_category": primary_category,
        "abs_url": abs_url,
        "pdf_url": pdf_url,
    }


def parse_feed(xml_payload: str, source: str, limit: int | None) -> dict:
    root = ET.fromstring(xml_payload)
    entries = [parse_entry(entry) for entry in root.findall("atom:entry", NS)]
    if limit is not None:
        entries = entries[:limit]

    return {
        "feed": {
            "title": collapse_ws(root.findtext("atom:title", default="", namespaces=NS)),
            "id": collapse_ws(root.findtext("atom:id", default="", namespaces=NS)),
            "updated": collapse_ws(root.findtext("atom:updated", default="", namespaces=NS)),
            "source": source,
        },
        "entry_count": len(entries),
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to a saved Atom XML file.")
    parser.add_argument(
        "--source-url",
        default=None,
        help=f"URL to fetch. Use {DEFAULT_FEED_URL!r} for the default arXiv feed.",
    )
    parser.add_argument("--limit", type=int, help="Optional maximum number of entries to keep.")
    parser.add_argument(
        "--output",
        help="Optional path to write the parsed JSON output. Defaults to stdout when omitted.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    try:
        source_url = args.source_url or None
        xml_payload, source = read_source(args.input, source_url)
        parsed = parse_feed(xml_payload, source, args.limit)
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"error: {exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=indent) + "\n",
            encoding="utf-8",
        )
    else:
        json.dump(parsed, sys.stdout, ensure_ascii=False, indent=indent)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
