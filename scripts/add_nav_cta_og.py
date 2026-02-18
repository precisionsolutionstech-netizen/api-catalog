#!/usr/bin/env python3
"""Add global nav, CTA, and og/twitter to script-enhanced pages that are missing them."""
import os
import re

APIS_DIR = os.path.join(os.path.dirname(__file__), "..", "apis")
BASE = "https://precisionsolutionstech-netizen.github.io/api-catalog"

# slug -> (breadcrumb_text, rapid_suffix, twitter_short)
PAGES = {
    "calendar-event-normalization": ("Calendar Event Normalization", "calendar-event-normalization", "Unify calendar event payloads. Stateless."),
    "job-posting-normalization": ("Job Posting Normalization", "job-posting-normalization", "Normalize job listings. Stateless."),
    "shipping-tracking-normalization": ("Shipping & Tracking Normalization", "shipping-tracking-data-normalization", "Standardize tracking across carriers. Stateless."),
    "social-media-data-normalization": ("Social Media Data Normalization", "social-media-data-normalization-interpretation", "Unify social content. Stateless."),
    "json-payload-consistency-checker": ("JSON Payload Consistency Checker", "json-payload-consistency-checker", "Analyze JSON consistency."),
    "html-to-markdown": ("HTML to Markdown Converter", "html-to-markdown-converter1", "Convert HTML to Markdown. Stateless."),
    "url-signature-presigner": ("URL Signature Presigner", "url-signature-presigner-api", "Generate signed URLs. Stateless."),
    "pdf-compression": ("PDF Compression", "pdf-compression-api1", "Reduce PDF size. 80MB max."),
    "pdf-table-extraction": ("PDF Table Extraction", "pdf-table-extraction-api", "Extract tables from PDFs. Stateless."),
    "pii-detection-redaction": ("PII Detection & Redaction", "sensitive-data-detection-redaction-api", "Detect and redact PII. Stateless."),
    "qr-code-generator": ("QR Code Generator", "advanced-qr-code-generator-api1", "Create QR codes. Stateless."),
    "adaptive-rate-limit-calculator": ("Adaptive Rate Limit Response Calculator", "adaptive-rate-limit-response-calculator", "Calculate retry strategies. Stateless."),
    "http-error-root-trigger-analyzer": ("HTTP Error Root Trigger Analyzer", "api-fault-analysis-engine", "Identify API failure causes. Stateless."),
    "api-error-status-normalization": ("API Error & Status Normalization", "api-error-status-normalization", "Normalize API errors. 1MB max."),
}

NAV_HTML = '<nav class="global-nav" aria-label="Main"><a href="../index.html">Home</a><a href="../index.html#normalization">Normalization APIs</a><a href="../index.html#validation">Validation APIs</a><a href="../index.html#comparison">Comparison APIs</a><a href="../blog/what-is-data-normalization.html">Blog</a></nav>\n        '

OG_TWITTER = '''    <meta property="og:url" content="{base}/apis/{slug}.html">
    <meta property="og:image" content="{base}/og-default.png">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{twitter}">
    <meta name="twitter:image" content="{base}/og-default.png">
'''

def main():
    for slug, (breadcrumb, rapid_suffix, twitter) in PAGES.items():
        path = os.path.join(APIS_DIR, slug + ".html")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        rapid_url = f"https://rapidapi.com/precisionsolutionstech/api/{rapid_suffix}"
        page_url = f"{BASE}/apis/{slug}.html"
        title = breadcrumb + (" API" if "API" not in breadcrumb else "")

        changed = False
        # Add global nav before breadcrumb (if not already there)
        if '<nav class="global-nav"' not in html or html.find('<nav class="global-nav"') > html.find('<nav aria-label="Breadcrumb">'):
            # Insert global nav before first <nav aria-label="Breadcrumb">
            html = html.replace(
                "<nav aria-label=\"Breadcrumb\"><a href=\"../index.html\">API Catalog</a> → " + breadcrumb + "</nav>",
                NAV_HTML + "<nav aria-label=\"Breadcrumb\"><a href=\"../index.html\">API Catalog</a> → " + breadcrumb + "</nav>",
                1
            )
            changed = True

        # Add CTA after h1 (if not already)
        if "cta-primary" not in html or html.find("cta-primary") > html.find("<p class=\"lead\">"):
            # Find first <h1>...</h1> followed by <p class="lead">
            pattern = r'(<h1>[^<]+</h1>)\s*<p class="lead">'
            if re.search(pattern, html) and 'Try on RapidAPI' not in html[:html.find('<p class="lead">')]:
                cta = f'<p><a href="{rapid_url}" target="_blank" rel="noopener" class="cta-primary">Try on RapidAPI</a></p>\n                '
                html = re.sub(pattern, r'\1\n                ' + cta + '<p class="lead">', html, 1)
                changed = True

        # Add og/twitter after canonical if missing
        if 'og:image" content="' not in html:
            insert = OG_TWITTER.format(base=BASE, slug=slug, title=title, twitter=twitter)
            html = re.sub(
                r'(<link rel="canonical" href="[^"]+">)\s*\n(\s*<meta property="og:title")',
                r'\1\n' + insert + r'\2',
                html,
                1
            )
            changed = True

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            print("Updated:", slug)

if __name__ == "__main__":
    main()
