#!/usr/bin/env python3
"""Refresh SEO signals on API catalog pages (dateModified, robots, last-updated)."""
import glob
import json
import os
import re

APIS_DIR = os.path.join(os.path.dirname(__file__), "..", "apis")
DATE_ISO = "2026-06-28"
DATE_HUMAN = "June 28, 2026"
ROBOTS = '    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">\n'
MODIFIED = f'    <meta property="article:modified_time" content="{DATE_ISO}">\n'
LAST_UPDATED = f'                <p class="page-updated"><time datetime="{DATE_ISO}">Last updated: {DATE_HUMAN}</time></p>\n'


def patch_tech_article_json(text: str) -> str:
    def repl(match):
        block = match.group(1)
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            return match.group(0)
        if data.get("@type") != "TechArticle":
            return match.group(0)
        data["dateModified"] = DATE_ISO
        if "datePublished" not in data:
            data["datePublished"] = "2026-02-16"
        return "<script type=\"application/ld+json\">\n" + json.dumps(data, separators=(",", ":")) + "\n    </script>"

    return re.sub(
        r'<script type="application/ld\+json">\s*(\{[^<]*"@type":"TechArticle"[^<]*\})\s*</script>',
        repl,
        text,
        count=1,
    )


def patch_file(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    original = text

    text = patch_tech_article_json(text)

    if 'name="robots"' not in text and "<link rel=\"canonical\"" in text:
        text = text.replace(
            "<link rel=\"canonical\"",
            ROBOTS + MODIFIED + "    <link rel=\"canonical\"",
            1,
        )
    elif 'article:modified_time' not in text and "<link rel=\"canonical\"" in text:
        text = text.replace(
            "<link rel=\"canonical\"",
            MODIFIED + "    <link rel=\"canonical\"",
            1,
        )
    elif 'article:modified_time' not in text:
        text = text.replace("</head>", MODIFIED + "</head>", 1)

    if "page-updated" not in text and 'class="lead"' in text:
        text = text.replace(
            'class="lead">',
            'class="lead">',
            1,
        )
        text = re.sub(
            r'(</p>\s*\n)(\s*<p class="cta-row">|\s*<section)',
            r"\1" + LAST_UPDATED + r"\2",
            text,
            count=1,
        )

    if ".page-updated" not in text and "page-updated" in text:
        text = text.replace(
            "        .lead {",
            "        .page-updated { font-size: 0.85rem; color: var(--muted); margin: -8px 0 16px; }\n        .lead {",
            1,
        )

    if text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    return False


def main():
    changed = 0
    for path in sorted(glob.glob(os.path.join(APIS_DIR, "*.html"))):
        if patch_file(path):
            changed += 1
            print("updated", os.path.basename(path))
    print(f"Done. {changed} API pages patched.")


if __name__ == "__main__":
    main()
