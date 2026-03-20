#!/usr/bin/env python3
"""Render a structured arXiv shortlist into a Feishu-ready message envelope."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def read_payload(input_path: str | None) -> dict:
    if input_path:
        return json.loads(Path(input_path).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def join_items(values: list[str], fallback: str = "未提供") -> str:
    cleaned = [value.strip() for value in values if value and value.strip()]
    return " / ".join(cleaned) if cleaned else fallback


def build_title(report: dict) -> str:
    if report.get("title"):
        return str(report["title"]).strip()
    date = str(report.get("date", "")).strip() or "未注明日期"
    return f"ArXiv Daily Scout | {date}"


def build_markdown(report: dict, title: str) -> str:
    papers = report.get("papers", [])
    lines: list[str] = [f"# {title}", ""]

    lead = str(report.get("lead", "")).strip()
    if lead:
        lines.extend(["## 今日结论", lead, ""])

    lines.extend([f"## 精选论文（{len(papers)} 篇）", ""])

    for index, paper in enumerate(papers, start=1):
        paper_title = str(paper.get("title", "")).strip() or "Untitled paper"
        paper_url = str(paper.get("url") or paper.get("abs_url") or "").strip()
        link_text = f"[{paper_title}]({paper_url})" if paper_url else paper_title

        lines.append(f"### {index}. {link_text}")
        lines.append(f"- 方向：{join_items(paper.get('categories', []), '未标注')}")
        lines.append(f"- 作者：{join_items(paper.get('authors', []), '未标注')}")
        lines.append(f"- 为什么值得读：{str(paper.get('why_it_matters', '未提供')).strip()}")
        lines.append(f"- 核心内容：{str(paper.get('summary', '未提供')).strip()}")

        key_points = paper.get("key_points", [])
        if key_points:
            lines.append(f"- 亮点：{join_items(key_points, '无')}")

        watch_out = str(paper.get("watch_out", "")).strip()
        if watch_out:
            lines.append(f"- 关注点：{watch_out}")

        action = str(paper.get("recommended_action", "")).strip()
        if action:
            lines.append(f"- 建议动作：{action}")

        lines.append("")

    notable_mentions = report.get("notable_mentions", [])
    if notable_mentions:
        lines.extend(["## 备选关注", ""])
        for item in notable_mentions:
            mention_title = str(item.get("title", "")).strip() or "Untitled paper"
            mention_url = str(item.get("url") or item.get("abs_url") or "").strip()
            mention_reason = str(item.get("reason", "")).strip() or "值得后续观察"
            if mention_url:
                lines.append(f"- [{mention_title}]({mention_url})：{mention_reason}")
            else:
                lines.append(f"- {mention_title}：{mention_reason}")
        lines.append("")

    footer_bits = []
    if report.get("feed_url"):
        footer_bits.append(f"来源：{str(report['feed_url']).strip()}")
    if report.get("date"):
        footer_bits.append(f"日期：{str(report['date']).strip()}")
    if footer_bits:
        lines.extend(["## 元数据", "", *[f"- {bit}" for bit in footer_bits]])

    return "\n".join(lines).strip() + "\n"


def build_metadata(report: dict) -> dict:
    categories = Counter()
    for paper in report.get("papers", []):
        for category in paper.get("categories", []):
            categories[category] += 1

    return {
        "date": report.get("date"),
        "feed_url": report.get("feed_url"),
        "paper_count": len(report.get("papers", [])),
        "top_categories": [category for category, _ in categories.most_common(5)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to the structured report JSON file.")
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="Print only the rendered markdown body.",
    )
    args = parser.parse_args()

    try:
        report = read_payload(args.input)
        papers = report.get("papers", [])
        if not papers:
            raise ValueError("report must include a non-empty 'papers' list")
        title = build_title(report)
        markdown = build_markdown(report, title)
        envelope = {
            "title": title,
            "markdown": markdown,
            "metadata": build_metadata(report),
        }
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.markdown_only:
        sys.stdout.write(markdown)
    else:
        json.dump(envelope, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
