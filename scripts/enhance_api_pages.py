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
DONE = {"retail-data-normalization", "json-schema-validator", "json-diff-checker", "json-payload-consistency-checker"}

# Per-page config: slug -> (breadcrumb_name, rapid_url_suffix for CTA, twitter_short, faqs list, related list, who_use, also_known_as)
with open(LINKS_PATH) as f:
    RAPID_LINKS = json.load(f)

CONFIG = {
    "event-listing-normalization": (
        "Event Listing Normalization",
        "event-listing-data-normalization",
        "One API call unifies event payloads from 50+ sources into a canonical schema for search, calendars, and analytics.",
        [
            ("What platforms are supported?", "Ten vendors have dedicated adapters: Eventbrite, Ticketmaster (plus Ticketweb and Frontgate aliases), SeatGeek, StubHub, Universe, Meetup, Eventful, Bandsintown, Songkick, and Eventfinda. Dozens of other platform strings use generic heuristics; unknown labels also use generic inference."),
            ("Do I need API keys for source platforms?", "No. This API operates purely on JSON payloads you supply. It does not call vendor APIs or scrape sites."),
            ("Can I normalize webhooks?", "Yes. POST the webhook body (and a platform hint when helpful) to /normalize; the response uses the same canonical event shape."),
            ("What is the canonical schema?", "A unified structure with fields such as title, startTimeIso, endTimeIso, location (physical, virtual, or hybrid), pricing, organizer, images, provenance, and interpretation (method and confidence)."),
            ("Does it fetch events from platforms?", "No. It only normalizes user-provided payloads."),
            ("What is the max request size?", "25MB per request."),
            ("Does it store data?", "No. The service is fully stateless."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic is free with 100 requests per month; Pro is $9.99/month with 10,000 requests; Ultra is $49.99/month (recommended) with 100,000 requests; Mega is $99.99/month with 250,000 requests. Overage pricing is shown on the live listing."),
            ("Can I request a new platform adapter?", "Yes. Open a thread on RapidAPI discussions for the Event Listing Data Normalization API with the vendor name and a redacted sample JSON payload."),
        ],
        [
            ("calendar-event-normalization.html", "Calendar Event Normalization", "Calendar-style events into a consistent format"),
            ("json-schema-validator.html", "JSON Schema Validator", "Validate payloads against JSON Schema"),
            ("api-error-status-normalization.html", "API Error & Status Normalization", "Unify error shapes across services"),
        ],
        "Event aggregators, discovery apps, data pipelines, and teams building a single unified event schema.",
        "Event normalizer API, Eventbrite Meetup Ticketmaster unifier, event listing canonical schema API, multi-platform event normalizer.",
    ),
    "calendar-event-normalization": (
        "Calendar Event Normalization",
        "calendar-event-normalization",
        "Unify calendar JSON or iCal across providers. Stateless, 25MB max.",
        [
            ("Does this API fetch events from Google or Microsoft for me?", "No. You pass payloads or .ics text you already obtained. No outbound calls to providers."),
            ("What is the maximum request size?", "25MB per request for POST /normalize and POST /normalize/ical."),
            ("Does it store my calendar data?", "No. Stateless in-memory processing."),
            ("Can I mix Google and Outlook in one request?", "Yes. Use multiple objects in inputs, each with calendarId and payload."),
            ("How do I normalize raw iCal (.ics) text?", "POST to /normalize/ical with Content-Type: text/plain and optional calendarId and defaultTimezone query params."),
            ("What if one input fails to parse?", "Other inputs still normalize. Check results[].error and the errors array."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic 100/mo free; Pro $9.99/10k; Ultra $49.99/100k; Mega $99.99/250k."),
            ("Do I need provider API keys for this normalization API?", "Only RapidAPI credentials. Provider OAuth is for your own fetch layer."),
        ],
        [("event-listing-normalization.html", "Event Listing Normalization", "Unify event listings"), ("job-posting-normalization.html", "Job Posting Normalization", "Normalize job data"), ("api-error-status-normalization.html", "API Error Normalization", "Canonical API errors"), ("json-schema-validator.html", "JSON Schema Validator", "Validate payloads")],
        "Calendar and scheduling apps, integration platforms, and teams unifying events across providers.",
        "Calendar event normalizer, calendar API unifier, unified calendar schema.",
    ),
    "job-posting-normalization": (
        "Job Posting Normalization",
        "job-posting-normalization",
        "One API call unifies job payloads from 25+ boards and ATS into a canonical schema for search and pipelines.",
        [
            ("Does it fetch jobs from job boards?", "No. It only normalizes JSON payloads you send. It does not call LinkedIn, Indeed, or ATS APIs."),
            ("Do I need API keys for LinkedIn or Indeed?", "No for this API. You obtain job JSON through your own integrations and pass it to /normalize."),
            ("Can I mix platforms in one request?", "Yes. Send an inputs array with platform buckets (platform plus data array) or inline blocks with platform and payload."),
            ("What is the canonical job schema?", "A unified structure with id, title, description, company, location, employmentType, experienceLevel, salary, postedDate, applyUrl, jobStatus, provenance, and interpretation (method and confidence)."),
            ("What is the max request size?", "25MB per request."),
            ("Does it store data?", "No. The service is fully stateless."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic is free with 100 requests per month; Pro is $9.99/month with 10,000 requests; Ultra is $49.99/month (recommended) with 100,000 requests; Mega is $99.99/month with 250,000 requests. Overage pricing is shown on the live listing."),
            ("Can I request a new platform adapter?", "Yes. Open a thread on RapidAPI discussions for the Job Posting Normalization API with the vendor name and a redacted sample JSON payload."),
        ],
        [("retail-data-normalization.html", "Retail Data Normalization", "Normalize product data"), ("event-listing-normalization.html", "Event Listing Normalization", "Unify event data"), ("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize API errors")],
        "HR tech, job aggregators, ATS and recruitment platforms needing one job schema.",
        "Job listing normalizer, job board unifier, job data normalization API.",
    ),
    "shipping-tracking-normalization": (
        "Shipping & Tracking Normalization",
        "shipping-tracking-data-normalization",
        "One API call unifies carrier tracking payloads into a canonical schema for dashboards, support, and analytics.",
        [
            ("Does it fetch live tracking from carriers?", "No. It normalizes JSON you send (tracking numbers plus optional pre-fetched carrier payloads). It does not call UPS, FedEx, USPS, or DHL APIs."),
            ("Do I need carrier API keys?", "No for this API. You obtain tracking responses through your own integrations and pass them in the request body."),
            ("What if I only send tracking numbers?", "The API can infer carrier from common patterns and return a minimal shipment with warnings. Full timelines need a payload from your carrier integration."),
            ("What is the canonical status taxonomy?", "Statuses map to a fixed set such as pending, label_created, accepted, in_transit, out_for_delivery, delivered, exception, failed_attempt, returned, cancelled, customs_cleared, and unknown. Original carrier wording is preserved on events."),
            ("What is the max request size?", "25MB per request."),
            ("Does it store data?", "No. The service is fully stateless."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic is free with 100 requests per month; Pro is $9.99/month with 10,000 requests; Ultra is $49.99/month (recommended) with 100,000 requests; Mega is $99.99/month with 250,000 requests. Overage pricing is shown on the live listing."),
            ("Can I request a new carrier adapter?", "Yes. Open a thread on RapidAPI discussions for the Shipping & Tracking Data Normalization API with the carrier name and a redacted sample JSON payload."),
        ],
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
        "POST /analyze with a JSON array or object; consistency warnings and summary. ~10MB body.",
        [
            ("What do I send in the request body?", "One JSON value: usually an array of objects to compare across items, or an object (nested arrays are analyzed recursively). No payloads wrapper."),
            ("What is the maximum request size?", "About 10MB for the JSON body. If the serialized payload exceeds 10MB after parse, the API returns HTTP 413 with PAYLOAD_TOO_LARGE."),
            ("Does the API store my JSON?", "No. Stateless in-memory processing."),
            ("Is this the same as JSON Schema validation?", "No. This finds inconsistencies across concrete samples (e.g. mixed types). Use JSON Schema Validator for contract enforcement."),
            ("What endpoint and host should I use?", "POST /analyze on json-payload-consistency-checker.p.rapidapi.com—confirm in RapidAPI."),
            ("How are invalid JSON and oversized payloads handled?", "400 with validJson false and invalidJson true for bad syntax; 413 with PAYLOAD_TOO_LARGE when the parsed payload is too large."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic 100/mo free; Pro $9.99/10k; Ultra $49.99/100k; Mega $99.99/250k."),
            ("Can I use this in CI/CD?", "Yes—gate on summary.warningCount or specific warning codes; output is deterministic."),
        ],
        [("json-schema-validator.html", "JSON Schema Validator", "Validate JSON against schema"), ("json-diff-checker.html", "JSON Diff Checker", "Compare JSON payloads"), ("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize errors")],
        "Backend and data teams analyzing payload consistency, API contract and quality checks.",
        "JSON consistency API, payload consistency checker, JSON structure analyzer.",
    ),
    "json-schema-validator": (
        "JSON Schema Validator",
        "json-schema-validator-api",
        "POST /validate with payload plus schema or schemaUrl. Strict structural subset, ~10MB payload.",
        [
            ("What goes in the POST body?", "payload (required) plus exactly one of schema (inline object) or schemaUrl (HTTPS string). You cannot send both schema and schemaUrl."),
            ("Does HTTP 200 mean the payload is valid?", "Not necessarily. Validation failures often return HTTP 200 with valid false and a populated errors array. Check the valid boolean. Client errors may return HTTP 400 or 413."),
            ("Can I load the schema from a URL?", "Yes. schemaUrl must be HTTPS; localhost and private IPs are blocked. Max about 1MB and 5 second timeout."),
            ("What is the maximum payload size?", "About 10MB for the serialized payload after parse. Oversize returns HTTP 413 with PAYLOAD_TOO_LARGE."),
            ("Does it store my JSON?", "No. Stateless in-memory processing."),
            ("Is this full JSON Schema?", "No. It supports a strict subset: type, required, properties, items, nesting. No $ref, anyOf, enum, pattern, or format validation."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic 100/mo free; Pro $9.99/10k; Ultra $49.99/100k; Mega $99.99/250k."),
            ("Can I use this in CI/CD?", "Yes. Output is deterministic; fail when valid is false or summary.errorCount is greater than zero."),
        ],
        [
            ("json-payload-consistency-checker.html", "JSON Payload Consistency Checker", "Cross-sample consistency"),
            ("json-diff-checker.html", "JSON Diff Checker", "Two-version diff"),
            ("api-error-status-normalization.html", "API Error & Status Normalization", "Canonical errors"),
        ],
        "Backend teams, CI/CD pipelines, and data ingestion needing structural contract checks.",
        "JSON schema API, contract validation, structural JSON validator.",
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
        "Reduce PDF size. Speed, lossless, or max. 80MB max. RapidAPI: Basic 15/mo free; Pro $9.99/500; Ultra $15/2k + $0.03 overage; Mega $30/10k + $0.02 overage.",
        [
            ("How is pricing different from your other APIs?", "Basic includes 15 requests/month (not 100). Pro is 500/mo at $9.99. Ultra is $15/mo for 2000 requests with about $0.03 per overage. Mega is $30/mo for 10000 with about $0.02 per overage. Confirm on RapidAPI."),
            ("Does it store files?", "No. Fully stateless."),
            ("Max file size?", "80MB."),
        ],
        [("pdf-table-extraction.html", "PDF Table Extraction", "Extract tables from PDFs"), ("html-to-markdown.html", "HTML to Markdown", "Convert HTML to Markdown")],
        "Developers and apps optimizing PDFs for email, storage, or web.",
        "PDF compressor API, PDF shrinker, PDF optimizer.",
    ),
    "pdf-table-extraction": (
        "PDF Table Extraction",
        "pdf-table-extraction-api",
        "Extract structured table data from PDFs. Stateless. RapidAPI: Basic 25/mo; Pro $9.99/3500 + $0.005 overage; Ultra $30/15k + $0.003; Mega $99/100k + $0.002.",
        [
            ("What are the RapidAPI quotas?", "Basic: 25/mo free. Pro: $9.99 for 3,500/mo plus about $0.005 per overage. Ultra: $30 for 15,000/mo plus about $0.003 overage. Mega: $99 for 100,000/mo plus about $0.002 overage. Confirm on RapidAPI."),
            ("Does it store PDFs?", "No. Fully stateless."),
            ("What formats?", "Returns structured table data (e.g. JSON), or Excel/CSV binary depending on outputFormat."),
        ],
        [("pdf-compression.html", "PDF Compression", "Compress PDFs"), ("json-schema-validator.html", "JSON Schema Validator", "Validate extracted JSON")],
        "Data teams and apps extracting tables from PDF reports and documents.",
        "PDF table extractor API, PDF to table, table extraction API.",
    ),
    "pii-detection-redaction": (
        "PII Detection & Redaction",
        "sensitive-data-detection-redaction-api",
        "Detect and redact PII in text. Stateless. RapidAPI: Basic 100/mo; Pro $9.99/10k; Ultra $29.99/35k + $0.003 overage; Mega $74.99/150k + $0.002.",
        [
            ("What are the RapidAPI quotas?", "Basic: 100/mo free. Pro: $9.99 for 10,000/mo with no overage listed. Ultra: $29.99 for 35,000/mo plus about $0.003 per overage. Mega: $74.99 for 150,000/mo plus about $0.002 overage. Confirm on RapidAPI."),
            ("Does it store the text?", "No. Fully stateless."),
            ("What PII types?", "Common types; see RapidAPI docs."),
        ],
        [("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize errors"), ("json-schema-validator.html", "JSON Schema Validator", "Validate payloads")],
        "Compliance and security teams redacting PII in logs, content, or exports.",
        "PII redaction API, sensitive data detection, PII scrubber API.",
    ),
    "qr-code-generator": (
        "QR Code Generator",
        "advanced-qr-code-generator-api1",
        "Advanced QR REST API: logos, colors, PNG/SVG/WEBP, scan verification. RapidAPI: Basic 25/mo; Pro $9.99/1500 + $0.006 overage (recommended); Ultra $30/25k + $0.005; Mega $49.99/50k + $0.002.",
        [
            ("How much does the QR API cost on RapidAPI?", "Basic is free with 25 requests per month. Pro is 9.99 dollars per month with 1500 requests and about 0.006 dollars per overage and is the recommended plan. Ultra is 30 dollars for 25000 with about 0.005 overage. Mega is 49.99 for 50000 with about 0.002 overage. Confirm on RapidAPI."),
            ("Can I add a logo to the QR code?", "Yes. Send base64 image data in the logo object with optional scale and padding. See RapidAPI docs for format limits."),
            ("What output formats are supported?", "PNG, SVG, and WEBP via the format field in JSON."),
            ("Does it store generated QR codes?", "No. Fully stateless."),
        ],
        [("url-signature-presigner.html", "URL Signature Presigner", "Sign URLs for QR targets"), ("html-to-markdown.html", "HTML to Markdown", "Content conversion")],
        "Apps and developers generating QR codes for links, tickets, or content.",
        "QR code API, QR generator API, REST QR code, branded QR, RapidAPI.",
    ),
    "adaptive-rate-limit-calculator": (
        "Adaptive Rate Limit Response Calculator",
        "adaptive-rate-limit-response-calculator",
        "Turn quota, tier, load, and idempotency signals into 429/503 decisions, Retry-After, and backoff—single POST or batch.",
        [
            ("Does this API enforce rate limits or store counters?", "No. It only calculates what response your gateway or service should return. You still own enforcement, token buckets, and storage."),
            ("What is the difference between POST /calculate and POST /calculate/batch?", "POST /calculate accepts one decision input object (requestContext, rateLimitSignals, systemStateSignals). POST /calculate/batch accepts a requests array and returns results plus a summary."),
            ("What is the max request body size?", "1MB per request (JSON body)."),
            ("Does it call my API or Redis?", "No. It does not make outbound calls. Send the signals your system already knows (quota, remaining, load, tier, idempotency, retry count)."),
            ("Is the output deterministic?", "Yes. The same input JSON produces the same decision output."),
            ("Which HTTP statuses can it recommend?", "Typically 200 when within limits, 429 when rate-limited, or 503 under critical load—plus optional degradation suggestions and Retry-After / X-RateLimit-* style headers in the response body."),
            ("Where are pricing and quotas defined?", "On RapidAPI for this API: Basic is free with 100 requests per month; Pro is $9.99/month (recommended on the listing) with 10,000 requests; Ultra is $39.99/month with 50,000 requests; Mega is $99.99/month with 500,000 requests. A second billable object (10,240/month with overage) also appears on the listing—see the live page for exact rates."),
            ("Can I use it from edge or serverless workers?", "Yes. The service is stateless and suitable for synchronous calls from gateways, sidecars, or edge functions as long as you stay within the body size limit."),
        ],
        [("api-error-status-normalization.html", "API Error & Status Normalization", "Normalize error responses"), ("http-error-root-trigger-analyzer.html", "HTTP Error Root Trigger Analyzer", "Analyze failure causes")],
        "Developers and platforms implementing retries and backoff from rate limits.",
        "Rate limit calculator API, retry strategy API, backoff calculator.",
    ),
    "http-error-root-trigger-analyzer": (
        "HTTP Error Root Trigger Analyzer",
        "api-fault-analysis-engine",
        "Rule-based 4xx/5xx root trigger analysis. POST /analyze or /analyze/batch. 1MB max.",
        [
            ("Does this API call my service or replay requests?", "No. You send a JSON description of an error event. Nothing is executed against your URLs."),
            ("What is the maximum request body size?", "1MB per request for both POST /analyze and POST /analyze/batch."),
            ("Does it store my payloads?", "Processing is stateless; payloads are not persisted for this product."),
            ("Is this AI or machine learning?", "No. Classification uses deterministic rules from HTTP semantics and common proxy or gateway patterns."),
            ("What status codes are supported?", "statusCode must be between 400 and 599 for each event."),
            ("What is the difference between /analyze and /analyze/batch?", "/analyze accepts one object. /analyze/batch accepts a non-empty array and returns results plus summary category counts."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic 100/mo free; Pro $9.99/10k; Ultra $49.99/100k; Mega $99.99/250k."),
            ("What is the minimum useful input?", "Only statusCode is required; duration and headers usually improve confidence."),
        ],
        [("api-error-status-normalization.html", "API Error & Status Normalization", "Canonical client errors"), ("adaptive-rate-limit-calculator.html", "Adaptive Rate Limit Calculator", "429/503 policy hints"), ("json-schema-validator.html", "JSON Schema Validator", "Validate payloads")],
        "Platform and SRE teams diagnosing API and HTTP failure causes.",
        "API fault analyzer, HTTP error analyzer, root cause API.",
    ),
    "api-error-status-normalization": (
        "API Error & Status Normalization",
        "api-error-status-normalization",
        "Normalize API error responses into a canonical taxonomy. 1MB max.",
        [
            ("Does this API call the upstream service or retry for me?", "No. You pass the error response you already captured. It returns classification and advisory retry fields only."),
            ("What body formats are supported?", "JSON objects, strings (plain text or HTML/XML), and other JSON-serializable values."),
            ("What is the max request size?", "1MB per request JSON body."),
            ("Does it store or log my payloads?", "No. The service is fully stateless."),
            ("What is canonicalError?", "A stable string such as AUTH_INVALID, RATE_LIMIT_EXCEEDED, or VALIDATION_FAILED—see the taxonomy in the README."),
            ("Is retry guidance mandatory to follow?", "No. retryRecommended and retryAfterSeconds are advisory."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic 100/mo free; Pro $9.99/10k; Ultra $49.99/100k; Mega $99.99/250k."),
            ("How do I use recommendedHttpStatus?", "Optional mapping when your API re-wraps upstream errors for your own clients."),
        ],
        [("json-schema-validator.html", "JSON Schema Validator", "Validate payloads"), ("json-diff-checker.html", "JSON Diff Checker", "Compare payloads"), ("http-error-root-trigger-analyzer.html", "HTTP Error Root Trigger Analyzer", "Analyze failure causes"), ("adaptive-rate-limit-calculator.html", "Adaptive Rate Limit Calculator", "Policy-based 429/503")],
        "Backend and integration teams unifying error handling and retry logic.",
        "Error normalization API, API error taxonomy, error response normalizer.",
    ),
    "json-diff-checker": (
        "JSON Diff Checker",
        "json-diff-checker-api",
        "Compare before/after JSON for breaking and non-breaking changes. ~10MB request body limit.",
        [
            ("What is the maximum request size?", "About 10MB for the entire JSON body (before and after together)."),
            ("Does the API store my JSON?", "No. Processing is stateless and in-memory."),
            ("Can I use this in CI/CD pipelines?", "Yes. Output is deterministic: same inputs yield the same diff and summary counts."),
            ("What counts as a breaking change?", "Examples include removed fields, type changes, root object vs array changes, non-nullable to nullable, and certain array element structure changes."),
            ("How are errors returned?", "Invalid or missing input often returns HTTP 400 with validJson false, empty change lists, and invalidSide when applicable."),
            ("Does it infer JSON Schema or OpenAPI?", "No. It compares two concrete JSON values only."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic 100/mo free; Pro $9.99/10k; Ultra $49.99/100k; Mega $99.99/250k."),
            ("How is this different from a text diff?", "It understands structure and types, classifies breaking vs non-breaking changes, and reports field paths."),
        ],
        [
            ("json-schema-validator.html", "JSON Schema Validator", "Validate against schema"),
            ("json-payload-consistency-checker.html", "JSON Payload Consistency Checker", "Cross-field consistency"),
            ("api-error-status-normalization.html", "API Error & Status Normalization", "Canonical errors"),
        ],
        "API and platform teams, CI/CD pipelines, QA regression.",
        "JSON diff API, breaking change detector, API contract diff.",
    ),
    "financial-invoice-normalization": (
        "Financial Invoice & Receipt Normalization",
        "financial-invoice-receipt-normalization",
        "Normalize invoice JSON from 40+ vendors into one schema. Stateless, 15MB max.",
        [
            ("Do I need API keys for QuickBooks, Stripe, or Xero to use this API?", "No. You only need your RapidAPI key. You obtain invoice JSON through your own integrations and POST it here."),
            ("What is the maximum request size?", "15MB per JSON body. Oversized bodies return HTTP 413."),
            ("Does it store or log my invoice data?", "No. Processing is stateless and in-memory."),
            ("Can I auto-detect the vendor from the payload?", "Yes. Omit the source field when the shape is recognizable; the response can include detectedSource."),
            ("What is generic normalization?", "For unknown JSON, heuristics such as webhook, stripe_like, csv_like, erp_export, pdf_extract, or invoice_shaped apply. sourceMeta.genericMode records the mode."),
            ("Does this API perform OCR on PDFs or images?", "No OCR here. Send structured JSON from your own extraction pipeline, often with source generic."),
            ("Where are pricing and quotas defined?", "On RapidAPI: Basic 100/mo free; Pro $9.99/10k; Ultra $49.99/100k; Mega $99.99/250k."),
            ("What must the JSON body include?", "A top-level payload object. source is optional."),
        ],
        [
            ("retail-data-normalization.html", "Retail Data Normalization", "Product and listing payloads"),
            ("calendar-event-normalization.html", "Calendar Event Normalization", "Calendar events"),
            ("api-error-status-normalization.html", "API Error Normalization", "Canonical API errors"),
            ("json-schema-validator.html", "JSON Schema Validator", "Validate payloads"),
        ],
        "Accounting integrators, expense platforms, payment products, and data teams unifying invoice JSON.",
        "Invoice normalization API, receipt normalizer, QuickBooks Stripe Xero invoice schema.",
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
