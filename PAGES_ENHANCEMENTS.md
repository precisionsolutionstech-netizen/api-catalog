# API Page Enhancement Template (v2)

This doc describes the Page Enhancement v2 pattern. **Reference pages:** `apis/retail-data-normalization.html` and `apis/json-schema-validator.html` (both fully updated).

## What’s implemented on the reference pages

- **Global nav** — Home | Normalization APIs | Validation APIs | Comparison APIs | Blog (links to index anchors and blog).
- **Primary CTA** — “Try on RapidAPI” button under the H1 (above the fold).
- **Structured data** — `TechArticle` (replacing WebPage), `BreadcrumbList`, `FAQPage` (when FAQ exists).
- **OpenGraph & Twitter** — `og:image`, `og:url`, `og:type`, Twitter card meta (use default image: `og-default.png` at repo root; recommend 1200×630).
- **Related APIs** — Section after “What to expect” with 4–6 links and descriptive anchor text.
- **Who Should Use This API** — Structured section (e.g. H3 + bullet list).
- **Also Known As** — Common search terms / keywords.
- **FAQ** — Collapsible FAQ after “About this API” + FAQPage schema.
- **Browse all** — “Browse all APIs in the catalog →” link block before footer.
- **FAQ script** — Toggle for `.faq-q` / `.faq-a` (aria-expanded and .show).

## Applying to other API pages

For each remaining API page:

1. **Head**
   - Add `og:url`, `og:image` (e.g. `https://.../og-default.png`), `og:type` (article), Twitter card meta.
   - Replace `WebPage` with `TechArticle` and add `"author": {"@type":"Organization","name":"Precision Solutions Tech"}`.
   - Add `BreadcrumbList` JSON-LD (Catalog → [Page name]).
   - Add `FAQPage` JSON-LD if you add an FAQ section.

2. **Styles**
   - Copy the extra CSS from retail or json-schema-validator: `.cta-primary`, `.global-nav`, `.faq-list`, `.faq-q`, `.faq-a`, `.related-apis`, `.browse-all`.

3. **Body**
   - Insert global nav before the breadcrumb nav.
   - Insert CTA link (RapidAPI subscribe URL for that API) under the H1.
   - After “What to expect”: add “Related APIs” section with 4–6 links (descriptive text).
   - In “About this API”: add “Who Should Use This API” and “Also Known As” (can shorten “Also useful if you’re looking for” in long-desc to avoid duplication).
   - After “About this API”: add “Frequently Asked Questions” with 3–4 Q/A pairs and FAQ JSON-LD.
   - Before footer: add “Browse all APIs in the catalog →” block.

4. **Script**
   - Add the FAQ toggle listener (see json-schema-validator or retail inline script).

## Default OG image

Add an image at repo root: **`og-default.png`** (1200×630 px recommended) for social sharing. All pages reference `https://precisionsolutionstech-netizen.github.io/api-catalog/og-default.png`. If the file is missing, social previews may show no image until you add it.
