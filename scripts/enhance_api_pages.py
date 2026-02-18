#!/usr/bin/env python3
"""
Apply v2 enhancements (nav, CTA, schema, FAQ, related, browse-all) to API HTML pages.
Run from api-catalog root: python3 scripts/enhance_api_pages.py
"""
import json
import re
import os

BASE = "https://precisionsolutionstech-netizen.github.io/api-catalog"
APIS_DIR = os.path.join(os.path.dirname(__file__), "..", "apis")
LINKS_PATH = os.path.join(os.path.dirname(__file__), "rapid_api_links.json")

# Already enhanced (skip)
DONE = {"retail-data-normalization", "json-schema-validator", "json-diff-checker"}

# Per-page config: slug -> (breadcrumb_name, rapid_url_suffix for CTA, twitter_short, faqs list, related list, who_use, also_known_as)
with open(LINKS_PATH) as f:
    RAPID_LINKS = json.load(f)

CONFIG = {
    "event-listing-normalization": (
        "Event Listing Normalization",
        "event-listing-data-normalization",
        "Unify event data from 50+ platforms. Stateless, 25MB max.",
        [("Does it fetch events from platforms?", "No. It only normalizes user-provided payloads."), ("Max request size?", "25MB."), ("Does it store data?", "No. Fully stateless.")],
        [("retail-data-normalization.html", "Retail Data Normalization", "Normalize product data across retailers"), ("calendar-event-normalization.html", "Calendar Event Normalization", "Unify calendar events"), ("job-posting-normalization.html", "Job Posting Normalization", "Normalize job listings"), ("json-schema-validator.html", "JSON Schema Validator", "Validate payloads before normalizing")],
        "Event aggregators, discovery apps, data pipelines, and teams building a single unified event schema.",
        "Event normalizer API, Eventbrite Meetup Ticketmaster unifier, event listing canonical schema API, multi-platform event normalizer.",
    ),
    "calendar-event-normalization": (
        "Calendar Event Normalization",
        "calendar-event-normalization",
        "Unify calendar event payloads across providers. Stateless.",
        [("Does it fetch from calendar APIs?", "No. It normalizes user-provided payloads only."), ("Does it store data?", "No. Fully stateless.")],
        [("event-listing-normalization.html", "Event Listing Normalization", "Unify event listings"), ("job-posting-normalization.html", "Job Posting Normalization", "Normalize job data"), ("retail-data-normalization.html", "Retail Data Normalization", "Normalize retail data")],
        "Calendar and scheduling apps, integration platforms, and teams unifying events across providers.",
        "Calendar event normalizer, calendar API unifier, unified calendar schema.",
    ),
    "job-posting-normalization": (
        "Job Posting Normalization",
        "job-posting-normalization",
        "Normalize job listings from multiple sources. Stateless.",
        [("Does it fetch jobs from job boards?", "No. It normalizes user-provided payloads."), ("Does it store data?", "No. Fully stateless.")],
        [("retail-data-normalization.html", "Retail Data Normalization", "Normalize product data"), ("event-listing-normalization.html", "Event Listing Normalization", "Unify event data"), ("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize API errors")],
        "HR tech, job aggregators, ATS and recruitment platforms needing one job schema.",
        "Job listing normalizer, job board unifier, job data normalization API.",
    ),
    "shipping-tracking-normalization": (
        "Shipping & Tracking Normalization",
        "shipping-tracking-data-normalization",
        "Standardize shipment tracking across carriers. Stateless.",
        [("Does it track packages?", "No. It normalizes tracking payloads you provide."), ("Does it store data?", "No. Fully stateless.")],
        [("retail-data-normalization.html", "Retail Data Normalization", "Normalize retail data"), ("event-listing-normalization.html", "Event Listing Normalization", "Unify event data"), ("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize errors")],
        "Logistics and shipping apps, e-commerce platforms, and teams unifying carrier tracking data.",
        "Shipping tracking normalizer, carrier tracking API, tracking data standardization.",
    ),
    "social-media-data-normalization": (
        "Social Media Data Normalization",
        "social-media-data-normalization-interpretation",
        "Unify social content payloads. Stateless.",
        [("Does it fetch from social networks?", "No. It normalizes user-provided payloads."), ("Does it store data?", "No. Fully stateless.")],
        [("retail-data-normalization.html", "Retail Data Normalization", "Normalize product data"), ("event-listing-normalization.html", "Event Listing Normalization", "Unify events"), ("job-posting-normalization.html", "Job Posting Normalization", "Normalize job data")],
        "Social dashboards, content aggregators, and teams unifying social payloads.",
        "Social media normalizer, social content API, unified social schema.",
    ),
    "json-payload-consistency-checker": (
        "JSON Payload Consistency Checker",
        "json-payload-consistency-checker",
        "Analyze JSON structure consistency across datasets.",
        [("What does it do?", "Checks consistency of JSON structure across multiple samples."), ("Does it store data?", "No. Fully stateless.")],
        [("json-schema-validator.html", "JSON Schema Validator", "Validate JSON against schema"), ("json-diff-checker.html", "JSON Diff Checker", "Compare JSON payloads"), ("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize errors")],
        "Backend and data teams analyzing payload consistency, API contract and quality checks.",
        "JSON consistency API, payload consistency checker, JSON structure analyzer.",
    ),
    "html-to-markdown": (
        "HTML to Markdown Converter",
        "html-to-markdown-converter1",
        "Convert HTML to GitHub Flavored Markdown. Stateless.",
        [("Does it store the content?", "No. Fully stateless."), ("What HTML is supported?", "Common tags; output is GitHub Flavored Markdown.")],
        [("json-schema-validator.html", "JSON Schema Validator", "Validate JSON"), ("pii-detection-redaction.html", "PII Detection & Redaction", "Redact sensitive data in text")],
        "Content pipelines, docs tools, and teams converting HTML to Markdown.",
        "HTML to Markdown API, HTML converter, GFM converter.",
    ),
    "url-signature-presigner": (
        "URL Signature Presigner",
        "url-signature-presigner-api",
        "Generate secure signed URLs. Stateless.",
        [("Does it store URLs?", "No. Fully stateless."), ("What signing methods?", "Check RapidAPI docs for supported algorithms.")],
        [("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize API errors"), ("adaptive-rate-limit-calculator.html", "Adaptive Rate Limit Calculator", "Rate limit strategies")],
        "Developers needing signed URLs for secure, time-limited resource access.",
        "Signed URL API, URL presigner, secure URL generator.",
    ),
    "pdf-compression": (
        "PDF Compression",
        "pdf-compression-api1",
        "Reduce PDF size. Speed, lossless, or max. 80MB max.",
        [("Does it store files?", "No. Fully stateless."), ("Max file size?", "80MB.")],
        [("pdf-table-extraction.html", "PDF Table Extraction", "Extract tables from PDFs"), ("html-to-markdown.html", "HTML to Markdown", "Convert HTML to Markdown")],
        "Developers and apps optimizing PDFs for email, storage, or web.",
        "PDF compressor API, PDF shrinker, PDF optimizer.",
    ),
    "pdf-table-extraction": (
        "PDF Table Extraction",
        "pdf-table-extraction-api",
        "Extract structured table data from PDFs. Stateless.",
        [("Does it store PDFs?", "No. Fully stateless."), ("What formats?", "Returns structured table data (e.g. JSON).")],
        [("pdf-compression.html", "PDF Compression", "Compress PDFs"), ("json-schema-validator.html", "JSON Schema Validator", "Validate extracted JSON")],
        "Data teams and apps extracting tables from PDF reports and documents.",
        "PDF table extractor API, PDF to table, table extraction API.",
    ),
    "pii-detection-redaction": (
        "PII Detection & Redaction",
        "sensitive-data-detection-redaction-api",
        "Detect and redact PII in text. Stateless.",
        [("Does it store the text?", "No. Fully stateless."), ("What PII types?", "Common types; see RapidAPI docs.")],
        [("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize errors"), ("json-schema-validator.html", "JSON Schema Validator", "Validate payloads")],
        "Compliance and security teams redacting PII in logs, content, or exports.",
        "PII redaction API, sensitive data detection, PII scrubber API.",
    ),
    "qr-code-generator": (
        "QR Code Generator",
        "advanced-qr-code-generator-api1",
        "Create QR codes. Stateless.",
        [("Does it store QR codes?", "No. Fully stateless."), ("Output format?", "Image (e.g. PNG); see RapidAPI docs.")],
        [("url-signature-presigner.html", "URL Signature Presigner", "Sign URLs for QR targets"), ("html-to-markdown.html", "HTML to Markdown", "Content conversion")],
        "Apps and developers generating QR codes for links, tickets, or content.",
        "QR code API, QR generator, barcode API.",
    ),
    "adaptive-rate-limit-calculator": (
        "Adaptive Rate Limit Response Calculator",
        "adaptive-rate-limit-response-calculator",
        "Calculate adaptive retry strategies from rate limit headers.",
        [("Does it call APIs?", "No. It computes strategies from headers you provide."), ("Does it store data?", "No. Fully stateless.")],
        [("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize error responses"), ("http-error-root-trigger-analyzer.html", "HTTP Error Root Trigger Analyzer", "Analyze failure causes")],
        "Developers and platforms implementing retries and backoff from rate limits.",
        "Rate limit calculator API, retry strategy API, backoff calculator.",
    ),
    "http-error-root-trigger-analyzer": (
        "HTTP Error Root Trigger Analyzer",
        "api-fault-analysis-engine",
        "Identify root causes of API failures. Stateless.",
        [("Does it call my API?", "No. It analyzes error data you send."), ("Does it store data?", "No. Fully stateless.")],
        [("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize errors"), ("adaptive-rate-limit-calculator.html", "Adaptive Rate Limit Calculator", "Retry strategies")],
        "Platform and SRE teams diagnosing API and HTTP failure causes.",
        "API fault analyzer, HTTP error analyzer, root cause API.",
    ),
    "api-error-status-normalization": (
        "API Error & Status Normalization",
        "api-error-status-normalization",
        "Normalize API error responses into a canonical taxonomy. 1MB max.",
        [("Does it call external APIs?", "No. It normalizes the error payload you send."), ("Max request size?", "1MB."), ("Does it store data?", "No. Fully stateless.")],
        [("json-schema-validator.html", "JSON Schema Validator", "Validate payloads"), ("json-diff-checker.html", "JSON Diff Checker", "Compare payloads"), ("http-error-root-trigger-analyzer.html", "HTTP Error Root Trigger Analyzer", "Analyze failure causes")],
        "Backend and integration teams unifying error handling and retry logic.",
        "Error normalization API, API error taxonomy, error response normalizer.",
    ),
}

# Shared CSS and script snippets
EXTRA_CSS = """
        .cta-primary { display: inline-block; margin: 0 0 24px; padding: 12px 24px; background: var(--accent); color: var(--bg); border: none; border-radius: 8px; font-weight: 600; font-size: 1rem; text-decoration: none; cursor: pointer; }
        .cta-primary:hover { filter: brightness(1.1); }
        .global-nav { margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
        .global-nav a { margin-right: 16px; }
        .faq-list { list-style: none; padding: 0; margin: 0; }
        .faq-list li { border-bottom: 1px solid var(--border); }
        .faq-q { width: 100%; padding: 14px 12px; cursor: pointer; font-weight: 600; display: flex; justify-content: space-between; align-items: center; text-align: left; background: transparent; color: var(--text); border: none; font-family: inherit; font-size: inherit; }
        .faq-q:hover { background: var(--surface); }
        .faq-q::after { content: '+'; flex-shrink: 0; margin-left: 8px; width: 1.5rem; height: 1.5rem; display: inline-flex; align-items: center; justify-content: center; border-radius: 4px; background: var(--surface); color: var(--accent); font-size: 1.1rem; line-height: 1; }
        .faq-q[aria-expanded="true"]::after { content: '\u2212'; }
        .faq-a { padding: 12px 12px 16px; color: var(--muted); display: none; background: var(--surface); margin: 0 12px 8px; border-radius: 6px; font-weight: normal; }
        .faq-a.show { display: block; }
        .related-apis { list-style: none; padding: 0; margin: 0; }
        .related-apis li { margin: 10px 0; padding-left: 0; }
        .related-apis a { font-weight: 500; }
        .browse-all { margin: 28px 0; padding: 16px; background: var(--surface); border-radius: 8px; border: 1px solid var(--border); text-align: center; }
        .browse-all a { font-weight: 600; font-size: 1.05rem; }
"""

FAQ_SCRIPT = """
    document.querySelectorAll('.faq-q').forEach(function(btn){
        btn.addEventListener('click',function(){ var expanded=this.getAttribute('aria-expanded')==='true'; this.setAttribute('aria-expanded',!expanded); var panel=document.getElementById(this.getAttribute('aria-controls')); if(panel) panel.classList.toggle('show',!expanded); });
    });
"""


def main():
    for slug, cfg in CONFIG.items():
        if slug in DONE:
            continue
        path = os.path.join(APIS_DIR, slug + ".html")
        if not os.path.isfile(path):
            print("Skip (not found):", path)
            continue
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        breadcrumb_name, rapid_suffix, twitter_short, faqs, related_list, who_use, also_known_as = cfg
        rapid_url = "https://rapidapi.com/precisionsolutionstech/api/" + rapid_suffix
        page_url = f"{BASE}/apis/{slug}.html"

        # 1) Meta + schema: after first og:description, add og:url, og:image, og:type, twitter, TechArticle, Breadcrumb, FAQ
        if 'og:image" content="https://precisionsolutionstech-netizen.github.io/api-catalog/og-default.png"' in html:
            print("Already enhanced:", slug)
            continue

        # Get title from <title>...</title>
        title_match = re.search(r'<title>([^|]+)\s*\|', html)
        title = title_match.group(1).strip() if title_match else breadcrumb_name + " API"
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
        meta_desc = desc_match.group(1) if desc_match else ""

        # Replace WebPage with TechArticle and add og/twitter/breadcrumb/FAQ
        old_script = re.search(r'<script type="application/ld\+json">\s*\{[^}]+\}\s*</script>', html, re.DOTALL)
        if not old_script:
            print("No WebPage schema in", slug)
            continue
        # Insert after </script> of ld+json: new scripts and ensure og/twitter
        insert_after_canonical = f'''    <meta property="og:url" content="{page_url}">
    <meta property="og:image" content="{BASE}/og-default.png">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{twitter_short}">
    <meta name="twitter:image" content="{BASE}/og-default.png">'''
        if "og:image" not in html:
            html = re.sub(r'(<link rel="canonical" href="[^"]+"/>)\s*', r'\1\n' + insert_after_canonical + "\n    ", html, count=1)

        # Replace WebPage with TechArticle
        html = re.sub(r'"@type":"WebPage"', '"@type":"TechArticle"', html, count=1)
        html = re.sub(r'","url":"', '","author":{"@type":"Organization","name":"Precision Solutions Tech"},"url":"', html, count=1)
        if '"headline"' not in html:
            html = re.sub(r'"name":"([^"]+)"', r'"headline":"\1","name":"\1"', html, count=1)

        # Add BreadcrumbList and FAQPage after first ld+json
        if 'BreadcrumbList' not in html:
            faq_entities = ",".join(
                f'{{"@type":"Question","name":"{q.replace(chr(34), chr(92)+chr(34))}","acceptedAnswer":{{"@type":"Answer","text":"{a.replace(chr(34), chr(92)+chr(34))}"}}}}'
                for q, a in faqs
            )
            breadcrumb_ld = f'''    <script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"API Catalog","item":"{BASE}/"}},{{"@type":"ListItem","position":2,"name":"{breadcrumb_name}","item":"{page_url}"}}]}}
    </script>
    <script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{faq_entities}]}}
    </script>
'''
            html = html.replace("</script>\n    <style>", "</script>\n" + breadcrumb_ld + "    <style>", 1)

        # 2) CSS: before footer { add EXTRA_CSS
        if "global-nav" not in html:
            html = re.sub(r'(\.postman-btn:hover \{ background: var\(--border\); \}\s*)', r'\1' + EXTRA_CSS + "        ", html, count=1)

        # 3) Nav + CTA: add global nav and CTA after h1
        if 'global-nav' not in html or 'cta-primary' not in html:
            html = re.sub(r'<nav aria-label="Breadcrumb">', '<nav class="global-nav" aria-label="Main"><a href="../index.html">Home</a><a href="../index.html#normalization">Normalization APIs</a><a href="../index.html#validation">Validation APIs</a><a href="../index.html#comparison">Comparison APIs</a><a href="../blog/what-is-data-normalization.html">Blog</a></nav>\n        <nav aria-label="Breadcrumb">', html, count=1)
            html = re.sub(r'(<h1>[^<]+</h1>)\s*<p class="lead">', f'\\1\n                <p><a href="{rapid_url}" target="_blank" rel="noopener" class="cta-primary">Try on RapidAPI</a></p>\n                <p class="lead">', html, count=1)

        # 4) Related + About blocks: after What to expect section
        expect_section = re.search(r'<section><h2 id="expect">What to expect</h2>[^<]+</section>', html)
        if expect_section and 'id="related"' not in html:
            related_li = "".join(f'<li><a href="{href}">{name}</a> – {desc}</li>' for href, name, desc in related_list)
            related_block = f'''
            <section><h2 id="related">Related APIs</h2>
                <ul class="related-apis">
                    {related_li}
                </ul>
            </section>'''
            html = html.replace(expect_section.group(0), expect_section.group(0) + related_block, 1)

        # 5) Who Should Use + Also Known As before long-desc in About
        about_section = re.search(r'<section><h2 id="about">About this API</h2>\s*<div class="long-desc">', html)
        if about_section and 'id="who-should-use"' not in html:
            who_block = f'''
                <h3 id="who-should-use">Who Should Use This API</h3>
                <p>{who_use}</p>
                <h3 id="also-known-as">Also Known As</h3>
                <p>{also_known_as}</p>
<div class="long-desc">'''
            html = html.replace('<section><h2 id="about">About this API</h2>\n<div class="long-desc">', '<section><h2 id="about">About this API</h2>\n' + who_block, 1)

        # 6) Remove "Also useful if you're looking for" list (optional)
        html = re.sub(r'<p>Also useful if you\'re looking for:</p>\s*<ul>[\s\S]*?</ul>\s*', '\n', html, count=1)
        html = re.sub(r'<p>Also useful if you’re looking for:</p>\s*<ul>[\s\S]*?</ul>\s*', '\n', html, count=1)

        # 7) FAQ section + browse-all before footer
        if '<h2 id="faq">Frequently Asked Questions</h2>' not in html:
            faq_items = "".join(f'''<li>
                        <button type="button" class="faq-q" aria-expanded="false" aria-controls="faq-a{i+1}" id="faq-q{i+1}">{q}</button>
                        <div id="faq-a{i+1}" class="faq-a" role="region" aria-labelledby="faq-q{i+1}">{a}</div>
                    </li>''' for i, (q, a) in enumerate(faqs))
            faq_block = f'''
            <section><h2 id="faq">Frequently Asked Questions</h2>
                <ul class="faq-list">
                    {faq_items}
                </ul>
            </section>
            <div class="browse-all"><a href="../index.html">Browse all APIs in the catalog →</a></div>'''
            html = re.sub(r'</div></section>\s*</article>\s*<footer>', '</div></section>' + faq_block + '\n        </article>\n        <footer>', html, count=1)

        # 8) FAQ script
        if "document.querySelectorAll('.faq-q')" not in html:
            html = re.sub(r'(var toggleErrors=document\.getElementById\([\'"]toggle-errors[\'"]\)[^;]+;)\s*(document\.querySelectorAll\([\'"]\.lang-tabs)', r'\1' + FAQ_SCRIPT + "    " + r'\2', html, count=1)
            if "document.querySelectorAll('.faq-q')" not in html:
                html = re.sub(r'(document\.getElementById\([\'"]postman-download[\'"]\)\.addEventListener)', FAQ_SCRIPT + "    " + r'\1', html, count=1)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print("Enhanced:", slug)


if __name__ == "__main__":
    main()
