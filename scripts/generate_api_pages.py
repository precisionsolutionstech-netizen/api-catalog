#!/usr/bin/env python3
"""Generate static API pages from config. Run from api-catalog root.
When API source folders are present (sibling to api-catalog), reads Rapid.md
from each to get request/response schemas, example body, and long description for SEO."""

import json
import os
import re
from datetime import date
from urllib.parse import urlparse

# RapidAPI links (exact URLs from catalog) loaded from rapid_api_links.json
RAPID_LINKS = None

# Catalog slug -> API folder name (sibling to api-catalog). No entry = no source folder.
SLUG_TO_API_FOLDER = {
    "event-listing-normalization": "event-listing-normalization-api",
    "calendar-event-normalization": "calendar-event-normalization-api",
    "job-posting-normalization": "job-posting-normalization-api",
    "shipping-tracking-normalization": "shipping-tracking-normalization-api",
    "retail-data-normalization": "retail-data-normalization-api",
    "social-media-data-normalization": "social-media-data-normalization-api",
    "json-diff-checker": "json-diff-checker-api",
    "html-to-markdown": "html-to-markdown-api",
    "url-signature-presigner": "url-signature-presigner-api",
    "pdf-table-extraction": "pdf-table-extraction-api",
    "pii-detection-redaction": "pii-detection-redaction-api",
    "qr-code-generator": "qr-code-generator-api",
    "adaptive-rate-limit-calculator": "adaptive-rate-limit-response-calculator-api",
    "http-error-root-trigger-analyzer": "http-error-root-trigger-analyzer-api",
    "api-error-status-normalization": "api-error-status-normalization-api",
    "json-payload-consistency-checker": "json-sanity-checker-api",
    "json-schema-validator": "json-schema-validator",
    "pdf-compression": "pdf-lossless-optimizer",
}


def host_from_rapid_url(rapid_url):
    """Derive the actual API host from the RapidAPI page URL. The REST call uses this host."""
    if not rapid_url:
        return None
    path = urlparse(rapid_url).path.rstrip("/")
    segment = path.split("/")[-1] if path else None
    return (segment + ".p.rapidapi.com") if segment else None


def _infer_type_from_value(val):
    """Infer JSON schema-like type from a value."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, int):
        return "integer"
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return "number"
    if isinstance(val, str):
        return "string"
    if isinstance(val, list):
        return "array"
    if isinstance(val, dict):
        return "object"
    return "any"


# Default descriptions for request fields that accept user-defined payloads (we don't know structure ahead of time).
REQUEST_PAYLOAD_DESCRIPTIONS = {
    "payload": "Your data to process (JSON object, array, or string). Structure is defined by you—e.g. object with keys to scan for PII, or raw event/job/shipment payload. Not stored or logged.",
    "inputs": "Array of input buckets. Each item typically has a platform/source id (e.g. platform, calendarId, retailerId) and a payload or data array. Structure per item is defined by the endpoint; see example and docs.",
    "data": "Raw payload array or object for this bucket (e.g. events, jobs, tracking data). Structure depends on the platform; you send what you have.",
    "before": "The original (before) JSON payload to compare. Object or array; structure is defined by your API or data.",
    "after": "The new (after) JSON payload to compare. Must match general structure of before for a meaningful diff.",
}


def _expand_schema_properties(properties, for_request=False, prefix=""):
    """Recursively expand JSON schema properties into rows. For arrays with items.properties, add field[].subfield rows."""
    if not properties or not isinstance(properties, dict):
        return []
    rows = []
    for name, defn in properties.items():
        if not isinstance(defn, dict):
            continue
        typ = defn.get("type")
        if isinstance(typ, list):
            typ = "|".join(str(t) for t in typ)
        typ = str(typ) if typ else "any"
        desc = (defn.get("description") or "").strip()
        if for_request and not desc and name in REQUEST_PAYLOAD_DESCRIPTIONS:
            desc = REQUEST_PAYLOAD_DESCRIPTIONS[name]
        field_name = (prefix + name) if prefix else name
        items_def = defn.get("items")
        if typ == "array" and isinstance(items_def, dict):
            item_props = items_def.get("properties")
            if item_props:
                for subname, subdef in item_props.items():
                    if not isinstance(subdef, dict):
                        continue
                    subtyp = subdef.get("type", "any")
                    if isinstance(subtyp, list):
                        subtyp = "|".join(str(t) for t in subtyp)
                    subdesc = (subdef.get("description") or "").strip()
                    rows.append({
                        "field": f"{field_name}[].{subname}",
                        "type": str(subtyp),
                        "description": subdesc or f"Per-item: {subname}",
                    })
            else:
                rows.append({"field": field_name, "type": "array", "description": desc or "Array of objects; see response example for item shape."})
        elif typ == "object":
            nested = defn.get("properties")
            if nested:
                for subname, subdef in nested.items():
                    if not isinstance(subdef, dict):
                        continue
                    subtyp = subdef.get("type", "any")
                    if isinstance(subtyp, list):
                        subtyp = "|".join(str(t) for t in subtyp)
                    subdesc = (subdef.get("description") or "").strip()
                    rows.append({
                        "field": f"{field_name}.{subname}",
                        "type": str(subtyp),
                        "description": subdesc or f"{subname}",
                    })
            else:
                rows.append({"field": field_name, "type": "object", "description": desc or "Object; structure depends on context."})
        else:
            rows.append({"field": field_name, "type": typ, "description": desc})
    return rows


def _example_to_rows(obj, prefix=""):
    """Build schema-like rows from an example JSON object so every field is documented. One level of expansion; arrays of objects get [].key."""
    if not isinstance(obj, dict):
        return []
    rows = []
    for key, val in obj.items():
        field = (prefix + key) if prefix else key
        typ = _infer_type_from_value(val)
        if typ == "array" and isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
            # Describe array of objects: one row per key in first item
            first = val[0]
            for k, v in first.items():
                rows.append({
                    "field": f"{field}[].{k}",
                    "type": _infer_type_from_value(v),
                    "description": f"Per-item: {k}",
                })
        elif typ == "object" and isinstance(val, dict):
            for k, v in val.items():
                rows.append({
                    "field": f"{field}.{k}",
                    "type": _infer_type_from_value(v),
                    "description": "",
                })
        else:
            rows.append({"field": field, "type": typ, "description": ""})
    return rows


def _json_schema_to_rows(schema_json, for_request=False):
    """Convert JSON schema to list of {field, type, description}, expanded so users see every field."""
    if not schema_json or not isinstance(schema_json, dict):
        return []
    props = schema_json.get("properties")
    if not props:
        return []
    return _expand_schema_properties(props, for_request=for_request, prefix="")


def _response_schema_from_schema_and_example(schema_json, example_json):
    """Build full response schema rows: expand schema; where schema is minimal (e.g. events: array of object), use example to list fields."""
    rows = []
    if schema_json and isinstance(schema_json, dict) and schema_json.get("properties"):
        rows = _expand_schema_properties(schema_json["properties"], for_request=False, prefix="")
    if not rows and example_json and isinstance(example_json, dict):
        rows = _example_to_rows(example_json)
    elif example_json and isinstance(example_json, dict):
        # Expand any row that is just "field": "events" (or similar) type "array" with no [].x rows: use example to add [].key
        expanded = []
        array_fields_without_items = set()
        for r in rows:
            if r["type"] == "array" and "[]" not in r["field"] and (not r["description"] or "see response example" in r["description"].lower()):
                array_fields_without_items.add(r["field"])
            expanded.append(r)
        for key in array_fields_without_items:
            val = example_json.get(key)
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                # Replace the single "events" row with events[].id, events[].title, ...
                expanded = [r for r in expanded if r["field"] != key]
                for k, v in val[0].items():
                    expanded.append({
                        "field": f"{key}[].{k}",
                        "type": _infer_type_from_value(v),
                        "description": f"Per-item: {k}",
                    })
        rows = expanded
        # Add any top-level key from example not yet documented
        seen = {r["field"].split("[")[0].split(".")[0] for r in rows}
        for key in example_json:
            if key in seen:
                continue
            val = example_json[key]
            typ = _infer_type_from_value(val)
            if typ == "array" and isinstance(val, list) and val and isinstance(val[0], dict):
                for k in val[0]:
                    rows.append({"field": f"{key}[].{k}", "type": _infer_type_from_value(val[0][k]), "description": f"Per-item: {k}"})
            elif typ == "object" and isinstance(val, dict):
                for k, v in val.items():
                    rows.append({"field": f"{key}.{k}", "type": _infer_type_from_value(v), "description": ""})
            else:
                rows.append({"field": key, "type": typ, "description": ""})
    return rows


def parse_rapid_md(content):
    """Parse Rapid.md content. Returns dict with short_description, long_description, path, body, request_schema, response_schema (or None for missing)."""
    out = {}
    # Short description: first ``` block after "Short Description" (not ```markdown; avoid matching Step 3 Tags)
    m = re.search(
        r"(?:Short Description|API Description \(Short\))[\s\S]*?```(?!markdown)\s*\n(.*?)```",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        out["short_description"] = m.group(1).strip()
    # Long description: first ```markdown ... ``` block
    m = re.search(r"```markdown\s*\n(.*?)```", content, re.DOTALL)
    if m:
        out["long_description"] = m.group(1).strip()
    # Path: **Path:** `/normalize` or Path: `/normalize`
    m = re.search(r"(?:\*\*)?Path(?:\*\*)?\s*:\s*`?(/[a-zA-Z0-9_-]+)`?", content)
    if m:
        out["path"] = m.group(1) if m.group(1).startswith("/") else "/" + m.group(1)
    # Example request body: first ```json after "Example Request Body" or "Request body — Example"
    m = re.search(
        r"(?:Example Request Body|Request body — Example(?:\s*\([^)]*\))?|\*\*Example Request Body\*\*)[\s\S]*?```json\s*\n(.*?)```",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        raw = m.group(1).strip()
        try:
            json.loads(raw)
            out["body"] = raw
        except json.JSONDecodeError:
            pass
    # If no "Example Request Body" pattern, try first ```json in "Request body" section
    if "body" not in out:
        m = re.search(
            r"Request body[\s\S]*?```json\s*\n(.*?)```",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if m:
            raw = m.group(1).strip()
            try:
                json.loads(raw)
                out["body"] = raw
            except json.JSONDecodeError:
                pass
    # Request schema: "Request body — JSON Schema" or "JSON body schema" then ```json
    m = re.search(
        r"(?:Request body — JSON Schema|JSON body schema)[\s\S]*?```json\s*\n(.*?)```",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        try:
            schema = json.loads(m.group(1).strip())
            out["request_schema"] = _json_schema_to_rows(schema, for_request=True)
        except json.JSONDecodeError:
            pass
    # Response: prefer "Response 200 — JSON Schema" then "Response 200 — Example" or "200 Success Response"
    response_schema_json = None
    response_example_json = None
    m_schema = re.search(
        r"Response 200 — JSON Schema[\s\S]*?```json\s*\n(.*?)```",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if m_schema:
        try:
            response_schema_json = json.loads(m_schema.group(1).strip())
            if not response_schema_json.get("properties") and "$schema" not in response_schema_json:
                response_schema_json = None  # might be example mislabelled
        except json.JSONDecodeError:
            pass
    m_example = re.search(
        r"(?:Response 200 — Example|200 Success Response(?:\s*\([^)]*\))?)[\s\S]*?```json\s*\n(.*?)```",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if m_example:
        try:
            response_example_json = json.loads(m_example.group(1).strip())
            if not isinstance(response_example_json, dict):
                response_example_json = None
        except json.JSONDecodeError:
            pass
    if not response_schema_json and not response_example_json:
        # Fallback: first ```json after "Response 200" or "**200 Success"
        m_any = re.search(
            r"(?:Response 200|\*\*200 Success Response)[\s\S]*?```json\s*\n(.*?)```",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if m_any:
            try:
                blob = json.loads(m_any.group(1).strip())
                if isinstance(blob, dict):
                    if blob.get("properties") or blob.get("$schema"):
                        response_schema_json = blob
                    else:
                        response_example_json = blob
            except json.JSONDecodeError:
                pass
    out["response_schema"] = _response_schema_from_schema_and_example(response_schema_json, response_example_json)
    # Error and warning codes: "**Error codes:** `CODE1`, `CODE2`" or "Error codes:" then backtick-wrapped codes
    out["error_codes"] = _parse_error_codes(content)
    return out


# Well-known error/warning codes with clear descriptions for API users.
ERROR_CODE_DESCRIPTIONS = {
    "MISSING_PAYLOAD": "Request body is missing the required payload or inputs. Send a JSON object with either payload or inputs array.",
    "INVALID_REQUEST": "Request is malformed or missing required fields (e.g. payload/inputs). Check the request body and try again.",
    "INVALID_JSON": "Request body is not valid JSON. Ensure Content-Type is application/json and the body parses correctly.",
    "INVALID_MODE": "The mode parameter is not one of the allowed values. Check the endpoint docs for valid modes.",
    "INVALID_REDACTION_STRATEGY": "One or more redaction strategy values are not supported. Use mask, replace, hash, or remove.",
    "CONFIG_ERROR": "Configuration for the request is invalid (e.g. types, coverageLevel, or redaction options).",
    "UNSUPPORTED_INPUT": "The input format or structure is not supported by this endpoint.",
    "MAX_DEPTH_EXCEEDED": "JSON nesting depth exceeds the allowed limit. Flatten or reduce nesting.",
    "UNSUPPORTED_MEDIA_TYPE": "Content-Type is not supported. Use application/json or the documented type.",
    "PAYLOAD_TOO_LARGE": "Request body exceeds the maximum allowed size (e.g. 25MB). Send a smaller payload or split the request.",
    "INTERNAL_ERROR": "An unexpected server error occurred. Retry later; if it persists, check status or contact support.",
    "MISSING_HTML": "Request must include an html field (string) in the body.",
    "INVALID_HTML": "The html field must be a non-empty string.",
    "URL_FETCH_NOT_SUPPORTED": "URL fetching is not supported; send HTML in the body instead.",
    "AMBIGUOUS_INPUT": "Cannot provide both html and url; use one.",
    "FIELD_REMOVED": "A field was removed between before and after (breaking change).",
    "TYPE_CHANGED": "A field's type changed (e.g. number to string) (breaking change).",
    "FIELD_ADDED": "A new field was added (non-breaking).",
    "NULLABILITY_CHANGED": "Nullability of a field changed (breaking or non-breaking depending on direction).",
    "AUTH_INVALID": "Authentication failed or credentials are invalid.",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Retry after the suggested Retry-After period.",
    "INVALID_TRACKING_NUMBER": "Empty or missing trackingNumber for one or more inputs.",
    "INVALID_PAYLOAD": "Payload is not an object (e.g. number or array where object expected).",
    "NO_TRACKING_DATA": "Payload could not be normalized to any events or status.",
    "PARSE_ERROR": "Unhandled parse failure for one item.",
}


def _parse_readme_error_table(content):
    """Parse a markdown table from README with columns Code, When it happens (or similar), HTTP. Returns list of {code, http_status, description}."""
    # Match table: header line has Code and HTTP (and optional When it happens / Description)
    # Pattern: | Code | When it happens | HTTP | then separator then rows
    lines = content.split("\n")
    codes = []
    header_idx = None
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells:
            continue
        first = (cells[0] or "").upper().replace("*", "")
        if first == "CODE":
            header_idx = i
            break
    if header_idx is None:
        return []
    # Next line should be separator (|---|...); then data rows
    header = [c.strip() for c in lines[header_idx].split("|")[1:-1]]
    code_col = 0
    if len(header) >= 3:
        desc_col, http_col = 1, 2
    elif len(header) == 2:
        desc_col, http_col = 1, -1  # No HTTP column; use "—"
    else:
        return []
    for i in range(header_idx + 2, len(lines)):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) <= code_col:
            continue
        code = (cells[code_col] or "").strip().strip("*").strip("`")
        if not code or code.startswith("-"):
            continue
        http_status = (cells[http_col] or "").strip() if http_col >= 0 and http_col < len(cells) else "—"
        desc = (cells[desc_col] or "").strip().strip("*").strip("`") if desc_col < len(cells) else ERROR_CODE_DESCRIPTIONS.get(code, "See RapidAPI docs for details.")
        codes.append({"code": code, "http_status": http_status or "—", "description": desc})
    return codes


def _parse_error_codes(content):
    """Extract error/warning codes from Rapid.md and return list of {code, http_status, description}."""
    codes = []
    # Match "**Error codes:** `CODE1`, `CODE2`, ..." or "Error codes:" ... `CODE`
    m = re.search(
        r"(?:\*\*)?Error codes(?:\*\*)?\s*:\s*([^\n]+)",
        content,
        re.IGNORECASE,
    )
    if m:
        raw = m.group(1)
        for match in re.finditer(r"`([A-Z][A-Z0-9_]+)`", raw):
            code = match.group(1)
            desc = ERROR_CODE_DESCRIPTIONS.get(code, "See RapidAPI docs for details.")
            codes.append({"code": code, "http_status": "4xx/5xx", "description": desc})
    # Also collect from Response 400/413/500 — Schema (enum) or Example (error field)
    for status, label in [("400", "400"), ("413", "413"), ("500", "500")]:
        m_ex = re.search(
            rf"Response {status}[\s\S]*?```json\s*\n(.*?)```",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if m_ex:
            try:
                obj = json.loads(m_ex.group(1).strip())
                err = obj.get("error") or obj.get("code")
                msg = obj.get("message") or obj.get("details", "")
                if err and isinstance(err, str) and err not in [c["code"] for c in codes]:
                    desc = ERROR_CODE_DESCRIPTIONS.get(err) or (msg if isinstance(msg, str) else "See RapidAPI docs.")
                    codes.append({"code": err, "http_status": status, "description": desc})
            except json.JSONDecodeError:
                pass
    return codes


def load_rapid_data(apis_base, slug):
    """Load and parse Rapid.md from the API folder for this slug. Returns merged dict or None."""
    folder = SLUG_TO_API_FOLDER.get(slug)
    if not folder:
        return None
    rapid_path = os.path.join(apis_base, folder, "Rapid.md")
    if not os.path.isfile(rapid_path):
        return None
    try:
        with open(rapid_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None
    out = parse_rapid_md(content)
    readme_path = os.path.join(apis_base, folder, "README.md")
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
            readme_codes = _parse_readme_error_table(readme_content)
            if readme_codes:
                out["error_codes"] = readme_codes
        except OSError:
            pass
    return out

CONFIG = [
    {"slug": "event-listing-normalization", "title": "Event Listing Normalization API", "nav": "Event Listing Normalization",
     "description": "Normalize event data from multiple platforms into a canonical schema. Unify event listings for comparison and aggregation.",
     "why": "Event data from different platforms (Meetup, Eventbrite, etc.) has different shapes. This API normalizes payloads into one canonical schema so you can compare, aggregate, and display events consistently.",
     "what": "POST /normalize with a single event object or array. Returns normalized event(s) with a consistent structure.",
     "host": "event-listing-normalization-api.p.rapidapi.com", "path": "/normalize",
     "body": '{"source":"meetup","raw":{}}',
     "request_schema": [{"field": "source", "type": "string", "description": "Platform identifier (e.g. meetup, eventbrite)."}, {"field": "raw", "type": "object", "description": "Raw event payload from the source."}],
     "response_schema": [{"field": "normalized", "type": "object|array", "description": "Canonical normalized event(s)."}]},
    {"slug": "calendar-event-normalization", "title": "Calendar Event Normalization API", "nav": "Calendar Event Normalization",
     "description": "Unify calendar event payloads from Google, Outlook, Apple, and more into one canonical event schema.",
     "why": "Calendar APIs return different structures. Normalize events from Google Calendar, Outlook, Apple Calendar, etc. into one schema for storage, display, or sync.",
     "what": "POST /normalize with calendar provider payload(s). Returns normalized event(s).",
     "host": "calendar-event-normalization-api.p.rapidapi.com", "path": "/normalize",
     "body": '{"source":"google","raw":{}}',
     "request_schema": [{"field": "source", "type": "string", "description": "Calendar provider (google, outlook, apple, etc.)."}, {"field": "raw", "type": "object", "description": "Raw calendar event payload."}],
     "response_schema": [{"field": "normalized", "type": "object|array", "description": "Normalized event(s)."}]},
    {"slug": "job-posting-normalization", "title": "Job Posting Normalization API", "nav": "Job Posting Normalization",
     "description": "Transform job listing data from multiple sources into a standard schema for comparison and analytics.",
     "why": "Job data from LinkedIn, Indeed, or ATS systems varies. Normalize into one schema for search, comparison, and analytics.",
     "what": "POST /normalize with job payload(s). Returns normalized job(s).",
     "host": "job-posting-normalization-api.p.rapidapi.com", "path": "/normalize",
     "body": '{"source":"linkedin","raw":{}}',
     "request_schema": [{"field": "source", "type": "string", "description": "Job source (linkedin, indeed, etc.)."}, {"field": "raw", "type": "object", "description": "Raw job payload."}],
     "response_schema": [{"field": "normalized", "type": "object|array", "description": "Normalized job(s)."}]},
    {"slug": "shipping-tracking-normalization", "title": "Shipping & Tracking Normalization API", "nav": "Shipping & Tracking Normalization",
     "description": "Standardize shipment tracking data across carriers (UPS, FedEx, USPS, etc.) into one schema.",
     "why": "Each carrier returns tracking data in different formats. Normalize for unified tracking dashboards and logistics apps.",
     "what": "POST /normalize with carrier tracking payload(s). Returns normalized tracking data.",
     "host": "shipping-tracking-data-normalization.p.rapidapi.com", "path": "/normalize",
     "body": '{"source":"ups","raw":{}}',
     "request_schema": [{"field": "source", "type": "string", "description": "Carrier (ups, fedex, usps, etc.)."}, {"field": "raw", "type": "object", "description": "Raw tracking payload."}],
     "response_schema": [{"field": "normalized", "type": "object|array", "description": "Normalized tracking data."}]},
    {"slug": "retail-data-normalization", "title": "Retail Data Normalization API", "nav": "Retail Data Normalization",
     "description": "Normalize product and retail listing data for comparison, analytics, and unified catalogs.",
     "why": "Product data from multiple retailers or marketplaces has different schemas. Normalize for price comparison, analytics, and catalog management.",
     "what": "POST /normalize with product/retail payload(s). Returns normalized product(s).",
     "host": "retail-data-normalization-api.p.rapidapi.com", "path": "/normalize",
     "body": '{"source":"amazon","raw":{}}',
     "request_schema": [{"field": "source", "type": "string", "description": "Retailer/marketplace."}, {"field": "raw", "type": "object", "description": "Raw product payload."}],
     "response_schema": [{"field": "normalized", "type": "object|array", "description": "Normalized product(s)."}]},
    {"slug": "social-media-data-normalization", "title": "Social Media Data Normalization API", "nav": "Social Media Data Normalization",
     "description": "Unify social media content payloads (posts, profiles) into a structured format.",
     "why": "Social APIs (Twitter, LinkedIn, etc.) return different structures. Normalize for aggregation, analytics, or content moderation pipelines.",
     "what": "POST /normalize with social payload(s). Returns normalized content.",
     "host": "social-media-data-normalization-api.p.rapidapi.com", "path": "/normalize",
     "body": '{"source":"twitter","raw":{}}',
     "request_schema": [{"field": "source", "type": "string", "description": "Social platform."}, {"field": "raw", "type": "object", "description": "Raw post/profile payload."}],
     "response_schema": [{"field": "normalized", "type": "object|array", "description": "Normalized content."}]},
    {"slug": "json-diff-checker", "title": "JSON Diff Checker API", "nav": "JSON Diff Checker",
     "description": "Compare JSON payloads to detect breaking and non-breaking changes. API versioning, backward compatibility, CI/CD.",
     "why": "API responses change over time. This API detects breaking changes (removed fields, type changes) and non-breaking changes so you can safely evolve APIs or fail CI when contracts break.",
     "what": "POST /diff with before and after JSON. Returns classified changes (breaking vs non-breaking).",
     "host": "json-diff-checker-api1.p.rapidapi.com", "path": "/diff",
     "body": '{"before":{"id":1,"name":"John"},"after":{"id":"1","name":"John Doe","email":"j@e.com"}}',
     "request_schema": [{"field": "before", "type": "object", "description": "Original JSON payload."}, {"field": "after", "type": "object", "description": "New JSON payload to compare."}],
     "response_schema": [{"field": "breaking", "type": "array", "description": "Breaking changes."}, {"field": "nonBreaking", "type": "array", "description": "Non-breaking changes."}]},
    {"slug": "html-to-markdown", "title": "HTML to Markdown Converter API", "nav": "HTML to Markdown",
     "description": "Convert HTML from CMS, scrapers, and WYSIWYG editors into clean GitHub Flavored Markdown.",
     "why": "HTML from many sources is bloated and inconsistent. Get deterministic, clean Markdown for docs, search, or LLM pipelines without maintaining per-language libraries.",
     "what": "POST /convert with JSON { \"html\": \"...\", \"mode\": \"readable\" } or raw text/html body. Returns { \"markdown\": \"...\" }.",
     "host": "html-to-markdown-api.p.rapidapi.com", "path": "/convert",
     "body": '{"html":"<h1>Hello</h1><p>World <strong>bold</strong></p>","mode":"readable"}',
     "request_schema": [{"field": "html", "type": "string", "description": "HTML content to convert."}, {"field": "mode", "type": "string", "description": "Conversion mode (e.g. readable)."}],
     "response_schema": [{"field": "markdown", "type": "string", "description": "Converted Markdown."}]},
    {"slug": "url-signature-presigner", "title": "URL Signature Presigner API", "nav": "URL Signature Presigner",
     "description": "Generate cryptographically signed URLs with expiration, method binding, and IP restrictions. Stateless presigned URLs.",
     "why": "Grant temporary access to downloads, uploads, or callbacks without databases or sessions. HMAC-SHA256 signatures; works with any CDN or server.",
     "what": "POST /sign with URL and constraints (expiry, method, IP, etc.). Returns signed URL. POST /verify to verify a request.",
     "host": "url-signature-presigner-api1.p.rapidapi.com", "path": "/sign",
     "body": '{"url":"https://example.com/file.pdf","expiresInSeconds":3600}',
     "request_schema": [{"field": "url", "type": "string", "description": "URL to sign."}, {"field": "expiresInSeconds", "type": "number", "description": "Expiration in seconds."}],
     "response_schema": [{"field": "signedUrl", "type": "string", "description": "Signed URL."}]},
    {"slug": "pdf-table-extraction", "title": "PDF Table Extraction API", "nav": "PDF Table Extraction",
     "description": "Extract structured table data from PDFs. Returns JSON, Excel, or CSV. File upload required.",
     "why": "Tables in PDFs are hard to extract programmatically. This API detects and extracts tables for spreadsheets, data pipelines, or automation.",
     "what": "POST /extract with multipart file (field: file). Optional query: outputFormat=json|xlsx|csv, pages=all|1,3-5.",
     "host": "pdf-table-extraction-api1.p.rapidapi.com", "path": "/extract",
     "file_upload": True,
     "request_schema": [{"field": "file", "type": "file", "description": "PDF file (multipart)."}, {"field": "outputFormat", "type": "string", "description": "Query: json, xlsx, or csv."}, {"field": "pages", "type": "string", "description": "Query: all or 1,3-5."}],
     "response_schema": [{"field": "tables", "type": "array", "description": "Extracted tables (JSON). Or file for xlsx/csv."}]},
    {"slug": "pii-detection-redaction", "title": "PII Detection & Redaction API", "nav": "PII Detection & Redaction",
     "description": "Detect and redact personally identifiable information (emails, SSNs, names, etc.) in text data.",
     "why": "Compliance (GDPR, CCPA) and security require identifying and redacting PII before logging, sharing, or storing data.",
     "what": "POST /scan with JSON { \"payload\": { ... } }. Returns detected PII and/or redacted payload.",
     "host": "pii-detection-redaction-api1.p.rapidapi.com", "path": "/scan",
     "body": '{"payload":{"user":"alice","email":"alice@example.com","ssn":"123-45-6789"}}',
     "request_schema": [{"field": "payload", "type": "object", "description": "Object to scan for PII (e.g. user, email, ssn)."}],
     "response_schema": [{"field": "redacted", "type": "string", "description": "Text with PII redacted."}, {"field": "detections", "type": "array", "description": "List of detected PII spans."}]},
    {"slug": "qr-code-generator", "title": "QR Code Generator API", "nav": "QR Code Generator",
     "description": "Create QR codes for URLs, text, or data. Configurable size and format.",
     "why": "Generate QR codes for tickets, payments, menus, or marketing without hosting your own generator.",
     "what": "POST /generate with payload (e.g. content, size). Returns image or URL to QR image.",
     "host": "qr-code-generator-api1.p.rapidapi.com", "path": "/generate",
     "body": '{"content":"https://example.com","size":200}',
     "request_schema": [{"field": "content", "type": "string", "description": "URL or text to encode."}, {"field": "size", "type": "number", "description": "Image size in pixels."}],
     "response_schema": [{"field": "imageUrl", "type": "string", "description": "URL or base64 of QR image."}]},
    {"slug": "adaptive-rate-limit-calculator", "title": "Adaptive Rate Limit Response Calculator API", "nav": "Adaptive Rate Limit Calculator",
     "description": "Analyze API rate limit headers and calculate adaptive retry-after and backoff strategies.",
     "why": "APIs return rate limits in different formats. This API helps clients compute when to retry and how to back off.",
     "what": "POST with rate limit headers or payload. Returns retry-after, backoff, or strategy.",
     "host": "adaptive-rate-limit-response-calculator-api.p.rapidapi.com", "path": "/calculate",
     "body": '{"requestContext":{},"rateLimitSignals":{}}',
     "request_schema": [{"field": "requestContext", "type": "object", "description": "Method, endpoint, clientId, clientTier, isIdempotent."}, {"field": "rateLimitSignals", "type": "object", "description": "currentRequestRate, allowedQuota, remainingAllowance, etc."}],
     "response_schema": [{"field": "recommendedStatus", "type": "number", "description": "Recommended HTTP status (429, 503, 200)."}, {"field": "retryAfter", "type": "number", "description": "Retry-After in seconds."}]},
    {"slug": "http-error-root-trigger-analyzer", "title": "HTTP Error Root Trigger Analyzer API", "nav": "HTTP Error Root Trigger Analyzer",
     "description": "Identify underlying causes of API failures and HTTP errors for debugging and monitoring.",
     "why": "HTTP 5xx or 4xx can have multiple causes. This API helps categorize and diagnose root triggers.",
     "what": "POST with error context (status, headers, body). Returns analysis and suggested causes.",
     "host": "http-error-root-trigger-analyzer-api.p.rapidapi.com", "path": "/analyze",
     "body": '{"statusCode":500,"message":"Internal Server Error"}',
     "request_schema": [{"field": "statusCode", "type": "number", "description": "HTTP status code."}, {"field": "message", "type": "string", "description": "Error message or body."}],
     "response_schema": [{"field": "rootCause", "type": "string", "description": "Identified root cause."}, {"field": "suggestions", "type": "array", "description": "Remediation suggestions."}]},
    {"slug": "api-error-status-normalization", "title": "API Error & Status Normalization API", "nav": "API Error & Status Normalization",
     "description": "Normalize diverse API error responses into a consistent taxonomy for monitoring and UX.",
     "why": "Every API returns errors differently. Normalize into a single taxonomy for dashboards, alerts, and user-facing messages.",
     "what": "POST with raw error response (status, body). Returns normalized error code and category.",
     "host": "api-error-status-normalization-api.p.rapidapi.com", "path": "/normalize",
     "body": '{"httpStatusCode":404,"responseBody":{}}',
     "request_schema": [{"field": "httpStatusCode", "type": "number", "description": "HTTP status (0-599)."}, {"field": "responseBody", "type": "string|object", "description": "Raw response body."}, {"field": "headers", "type": "object", "description": "Optional (e.g. Retry-After)."}],
     "response_schema": [{"field": "canonicalError", "type": "string", "description": "One of AUTH_INVALID, RATE_LIMIT_EXCEEDED, etc."}, {"field": "retry", "type": "object", "description": "retryRecommended, retryAfterSeconds, retryStrategy."}, {"field": "summary", "type": "string", "description": "Human-readable summary."}]},
    {"slug": "json-schema-validator", "title": "JSON Schema Validator API", "nav": "JSON Schema Validator",
     "description": "Validate JSON payloads against JSON Schema definitions.",
     "why": "Ensure request or response payloads conform to a schema before processing or storing.",
     "what": "POST with JSON and schema. Returns validation result and errors.",
     "host": "json-schema-validator.p.rapidapi.com", "path": "/validate",
     "body": '{"document":{},"schema":{}}',
     "request_schema": [{"field": "document", "type": "object", "description": "JSON to validate."}, {"field": "schema", "type": "object", "description": "JSON Schema."}],
     "response_schema": [{"field": "valid", "type": "boolean", "description": "Whether the document is valid."}, {"field": "errors", "type": "array", "description": "Validation errors if invalid."}]},
    {"slug": "json-payload-consistency-checker", "title": "JSON Payload Consistency Checker API", "nav": "JSON Payload Consistency Checker",
     "description": "Analyze JSON structure consistency across datasets for API and data quality.",
     "why": "Detect schema drift and inconsistent payloads across samples or versions.",
     "what": "POST with payload(s). Returns consistency analysis and recommendations.",
     "host": "json-sanity-checker-api.p.rapidapi.com", "path": "/check",
     "body": '{"payloads":[]}',
     "request_schema": [{"field": "payloads", "type": "array", "description": "JSON payloads to analyze."}],
     "response_schema": [{"field": "consistent", "type": "boolean", "description": "Whether payloads are consistent."}, {"field": "issues", "type": "array", "description": "Reported issues."}]},
    {"slug": "pdf-compression", "title": "PDF Compression API", "nav": "PDF Compression",
     "description": "Optimize PDF files with lossless compression to reduce size.",
     "why": "Shrink PDFs for storage or transfer without losing quality.",
     "what": "POST with PDF file. Returns optimized PDF or download URL.",
     "host": "pdf-lossless-optimizer.p.rapidapi.com", "path": "/compress",
     "file_upload": True,
     "body": "{}",
     "request_schema": [{"field": "file", "type": "file", "description": "PDF file to compress."}],
     "response_schema": [{"field": "url", "type": "string", "description": "URL or base64 of compressed PDF."}]},
]

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "apis")
LINKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapid_api_links.json")
# Base URL for sitemap and canonicals (no trailing slash). Set via API_CATALOG_BASE_URL env if different.
SITEMAP_BASE_URL = os.environ.get("API_CATALOG_BASE_URL", "https://precisionsolutionstech-netizen.github.io/api-catalog")

def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def schema_table(rows):
    if not rows:
        return "<p>See <a href=\"#\" data-rapid-docs>RapidAPI docs</a> for full schema.</p>"
    t = "<table class=\"schema-table\"><thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead><tbody>"
    for r in rows:
        t += f"<tr><td><code>{escape(r.get('field', ''))}</code></td><td><code>{escape(r.get('type', ''))}</code></td><td>{escape(r.get('description', ''))}</td></tr>"
    t += "</tbody></table>"
    return t


def long_description_to_html(md_text):
    """Convert long description markdown to safe HTML for SEO (paragraphs, no script)."""
    if not md_text:
        return ""
    lines = md_text.strip().split("\n")
    out = []
    in_list = False
    for line in lines:
        s = line.strip()
        if not s:
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        # Strip markdown headers but keep text
        if s.startswith("## "):
            s = s[3:]
        elif s.startswith("# "):
            s = s[2:]
        if s.startswith("- ") or s.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + escape(s[2:]) + "</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<p>" + escape(s) + "</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)

def template(c):
    global RAPID_LINKS
    slug = c["slug"]
    title = c["title"]
    nav = c["nav"]
    desc = escape(c["description"])
    why = escape(c["why"])
    what = escape(c["what"])
    base_url = SITEMAP_BASE_URL.rstrip("/")
    rapid_url = (RAPID_LINKS or {}).get(slug) or c.get("rapid_url") or ("https://rapidapi.com/precisionsolutionstech/api/" + slug)
    # Use host derived from RapidAPI page URL so the real REST call matches RapidAPI
    host = host_from_rapid_url(rapid_url) or c["host"]
    path = c["path"]
    body = c.get("body", "{}")
    file_upload = c.get("file_upload", False)
    req_schema = c.get("request_schema", [])
    res_schema = c.get("response_schema", [])
    long_description = c.get("long_description") or ""

    playground_body = ""
    if file_upload:
        playground_body = """
                    <label for="mode">Output format</label>
                    <select id="mode">
                        <option value="json">json</option>
                        <option value="xlsx">xlsx</option>
                        <option value="csv">csv</option>
                    </select>
                    <label for="file-input">PDF file (required)</label>
                    <input type="file" id="file-input" accept=".pdf,application/pdf">
                    <p class="file-upload-note">File is sent to RapidAPI; not stored here.</p>"""
        run_script = """
    var fileInput=document.getElementById('file-input');
    if(!fileInput.files||!fileInput.files[0]){resultDiv.style.display='block';resultDiv.className='result error';resultDiv.textContent='Please select a PDF file.';return;}
    runBtn.disabled=true;resultDiv.style.display='block';resultDiv.className='result';resultDiv.textContent='Uploading…';
    var formData=new FormData();formData.append('file',fileInput.files[0]);
    var mode=document.getElementById('mode').value||'json';
    fetch('https://'+host+path+'?outputFormat='+encodeURIComponent(mode),{method:'POST',headers:{'X-RapidAPI-Key':key,'X-RapidAPI-Host':host},body:formData})
    .then(function(r){return r.text();})
    .then(function(t){resultDiv.className='result success';try{resultDiv.textContent=JSON.stringify(JSON.parse(t),null,2);}catch(_){resultDiv.textContent=t;}})
    .catch(function(e){resultDiv.className='result error';resultDiv.textContent='Request failed: '+e.message;})
    .finally(function(){runBtn.disabled=false;});"""
    else:
        playground_body = """
                    <label for="body-json">Request body (JSON)</label>
                    <textarea id="body-json" placeholder='{}'>""" + escape(body) + """</textarea>"""
        run_script = """
    var bodyStr=document.getElementById('body-json').value.trim(),body;
    try{body=JSON.parse(bodyStr);}catch(e){resultDiv.style.display='block';resultDiv.className='result error';resultDiv.textContent='Invalid JSON: '+e.message;return;}
    runBtn.disabled=true;resultDiv.style.display='block';resultDiv.className='result';resultDiv.textContent='Loading…';
    fetch('https://'+host+path,{method:'POST',headers:{'Content-Type':'application/json','x-rapidapi-key':key,'x-rapidapi-host':host},body:JSON.stringify(body)})
    .then(function(r){return r.text().then(function(t){return{status:r.status,body:t};});})
    .then(function(o){resultDiv.className='result '+(o.status>=200&&o.status<300?'success':'error');try{resultDiv.textContent=JSON.stringify(JSON.parse(o.body),null,2);}catch(_){resultDiv.textContent=o.status+'\\n'+o.body;}})
    .catch(function(e){resultDiv.className='result error';resultDiv.textContent='Request failed: '+e.message;})
    .finally(function(){runBtn.disabled=false;});"""

    curl_example = f"curl --request POST \\\n  --url 'https://{host}{path}' \\\n  --header 'Content-Type: application/json' \\\n  --header 'x-rapidapi-host: {host}' \\\n  --header 'x-rapidapi-key: YOUR_RAPIDAPI_KEY' \\\n  --data '{body}'"
    if file_upload:
        curl_example = f"curl --request POST \\\n  --url 'https://{host}{path}?outputFormat=json' \\\n  --header 'X-RapidAPI-Host: {host}' \\\n  --header 'X-RapidAPI-Key: YOUR_RAPIDAPI_KEY' \\\n  --form 'file=@document.pdf'"

    body_js = body.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    js_snippet = f"""const res = await fetch('https://{host}{path}', {{
  method: 'POST',
  headers: {{
    'Content-Type': 'application/json',
    'x-rapidapi-key': 'YOUR_RAPIDAPI_KEY',
    'x-rapidapi-host': '{host}'
  }},
  body: '{body_js}'
}});
const data = await res.json();
console.log(data);"""
    if file_upload:
        js_snippet = f"""const formData = new FormData();
formData.append('file', document.querySelector('input[type=file]').files[0]);
const res = await fetch('https://{host}{path}?outputFormat=json', {{
  method: 'POST',
  headers: {{ 'X-RapidAPI-Key': 'YOUR_RAPIDAPI_KEY', 'X-RapidAPI-Host': '{host}' }},
  body: formData
}});
const data = await res.json();
console.log(data);"""
    body_py_esc = body.replace("\\", "\\\\").replace("'", "\\'")
    python_snippet = f"""import http.client
import json

conn = http.client.HTTPSConnection("{host}")
payload = '{body_py_esc}'
headers = {{
    'Content-Type': 'application/json',
    'x-rapidapi-key': 'YOUR_RAPIDAPI_KEY',
    'x-rapidapi-host': '{host}'
}}
conn.request("POST", "{path}", payload, headers)
res = conn.getresponse()
print(res.read().decode())"""
    if file_upload:
        python_snippet = f"""import requests

url = "https://{host}{path}"
headers = {{'X-RapidAPI-Key': 'YOUR_RAPIDAPI_KEY', 'X-RapidAPI-Host': '{host}'}}
with open('document.pdf', 'rb') as f:
    r = requests.post(url, files={{'file': f}}, headers=headers, params={{'outputFormat': 'json'}})
print(r.json())"""
    body_java = body.replace("\\", "\\\\").replace('"', '\\"')
    java_snippet = f"""HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://{host}{path}"))
    .header("Content-Type", "application/json")
    .header("x-rapidapi-key", "YOUR_RAPIDAPI_KEY")
    .header("x-rapidapi-host", "{host}")
    .method("POST", HttpRequest.BodyPublishers.ofString("{body_java}"))
    .build();
HttpResponse<String> response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
System.out.println(response.body());"""
    if file_upload:
        java_snippet = f"""// Use multipart: add file part with name 'file'. See RapidAPI docs for full example."""

    schema_req_html = schema_table(req_schema)
    schema_res_html = schema_table(res_schema)
    long_desc_html = long_description_to_html(long_description)
    about_section = (
        f'<section><h2 id="about">About this API</h2>\n<div class="long-desc">\n{long_desc_html}\n</div></section>'
        if long_desc_html
        else ""
    )
    error_codes = c.get("error_codes") or []
    error_codes_rows = ""
    for row in error_codes:
        error_codes_rows += f"<tr><td><code>{escape(row.get('code', ''))}</code></td><td><code>{escape(row.get('http_status', ''))}</code></td><td>{escape(row.get('description', ''))}</td></tr>"
    errors_link = ' &middot; <a href="#error-codes" class="schema-toggle" id="toggle-errors" aria-expanded="false">View error &amp; warning codes</a>' if error_codes_rows else ""
    errors_content = (
        '<div id="error-codes" class="schema-content" aria-hidden="true">'
        '<table class="schema-table"><thead><tr><th>Code</th><th>HTTP</th><th>Description</th></tr></thead><tbody>'
        + error_codes_rows + "</tbody></table></div>"
    ) if error_codes_rows else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="../favicon.svg" type="image/svg+xml">
    <link rel="icon" href="../favicon.png" type="image/png" sizes="32x32">
    <title>{title} | RapidAPI</title>
    <meta name="description" content="{desc}">
    <meta name="keywords" content="{slug}, API, RapidAPI, developer">
    <link rel="canonical" href="{base_url}/apis/{slug}.html">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebPage","name":"{escape(title)}","description":"{desc}","url":"{base_url}/apis/{slug}.html"}}
    </script>
    <style>
        :root {{ --bg: #0f172a; --surface: #1e293b; --border: #334155; --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8; --success: #34d399; --error: #f87171; }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        .wrap {{ max-width: 900px; margin: 0 auto; padding: 24px 20px; }}
        a {{ color: var(--accent); }}
        nav {{ margin-bottom: 32px; font-size: 0.9rem; }}
        h1 {{ font-size: 1.9rem; margin: 0 0 12px; }}
        .lead {{ font-size: 1.1rem; color: var(--muted); margin-bottom: 32px; }}
        h2 {{ font-size: 1.35rem; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
        section {{ margin-bottom: 28px; }}
        .playground {{ background: var(--surface); border-radius: 12px; padding: 20px; margin: 24px 0; border: 1px solid var(--border); }}
        .playground label {{ display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.9rem; }}
        .playground input[type="password"], .playground select {{ width: 100%; max-width: 320px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text); margin-bottom: 12px; }}
        .playground textarea {{ width: 100%; min-height: 120px; padding: 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text); font-family: ui-monospace, monospace; font-size: 13px; resize: vertical; }}
        .playground input[type="file"] {{ margin-bottom: 12px; }}
        .playground button {{ padding: 10px 20px; background: var(--accent); color: var(--bg); border: none; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 8px; }}
        .playground button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .playground .result {{ margin-top: 16px; padding: 12px; border-radius: 8px; background: var(--bg); border: 1px solid var(--border); white-space: pre-wrap; word-break: break-all; font-family: ui-monospace, monospace; font-size: 12px; max-height: 320px; overflow: auto; }}
        .playground .result.error {{ border-color: var(--error); color: var(--error); }}
        .playground .result.success {{ border-color: var(--success); }}
        .file-upload-note {{ font-size: 0.85rem; color: var(--muted); margin-top: 4px; }}
        .code-wrap {{ position: relative; margin: 16px 0; }}
        .code-wrap pre {{ margin: 0; padding: 14px 16px; background: var(--surface); border-radius: 8px; border: 1px solid var(--border); overflow-x: auto; font-size: 13px; }}
        .code-wrap .copy-btn {{ position: absolute; top: 10px; right: 10px; padding: 6px 12px; background: var(--border); color: var(--text); border: none; border-radius: 6px; font-size: 12px; cursor: pointer; }}
        .code-wrap .copy-btn:hover {{ background: var(--accent); color: var(--bg); }}
        .lang-tabs {{ display: flex; gap: 4px; margin-bottom: 8px; flex-wrap: wrap; }}
        .lang-tabs button {{ padding: 8px 14px; background: var(--surface); border: 1px solid var(--border); color: var(--muted); border-radius: 6px; cursor: pointer; font-size: 0.9rem; }}
        .lang-tabs button.active {{ background: var(--accent); color: var(--bg); border-color: var(--accent); }}
        .code-block {{ display: none; }}
        .code-block.active {{ display: block; }}
        .schema-section {{ margin: 16px 0; }}
        .schema-toggle {{ color: var(--accent); cursor: pointer; text-decoration: none; font-weight: 600; }}
        .schema-toggle:hover {{ text-decoration: underline; }}
        .schema-content {{ display: none; margin-top: 12px; padding: 12px; background: var(--surface); border-radius: 8px; border: 1px solid var(--border); overflow-x: auto; }}
        .schema-content.show {{ display: block; }}
        .schema-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        .schema-table th, .schema-table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
        .schema-table code {{ font-size: 0.85em; }}
        .long-desc {{ color: var(--muted); font-size: 0.98rem; }}
        .long-desc p {{ margin: 0.75em 0; }}
        .long-desc ul {{ margin: 0.75em 0; padding-left: 1.5em; }}
        .long-desc li {{ margin: 0.35em 0; }}
        .postman-btn {{ display: inline-block; margin-top: 12px; padding: 10px 18px; background: var(--surface); border: 1px solid var(--border); color: var(--accent); border-radius: 8px; cursor: pointer; font-weight: 600; text-decoration: none; }}
        .postman-btn:hover {{ background: var(--border); }}
        footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.9rem; text-align: center; }}
    </style>
</head>
<body>
    <div class="wrap">
        <nav aria-label="Breadcrumb"><a href="../index.html">API Catalog</a> → {nav}</nav>
        <article>
            <header>
                <h1>{title}</h1>
                <p class="lead">{desc}</p>
            </header>
            <section><h2 id="why">Why use this API?</h2><p>{why}</p></section>
            <section><h2 id="what">What the API does</h2><p>{what}</p></section>
            <section>
                <h2 id="schemas">Request &amp; response schema</h2>
                <p><a href="#request-schema" class="schema-toggle" id="toggle-req" aria-expanded="false">View request schema</a> &middot; <a href="#response-schema" class="schema-toggle" id="toggle-res" aria-expanded="false">View response schema</a>{errors_link}</p>
                {errors_content}
                <div id="request-schema" class="schema-content" aria-hidden="true">{schema_req_html}</div>
                <div id="response-schema" class="schema-content" aria-hidden="true">{schema_res_html}</div>
            </section>
            <section>
                <h2 id="playground">Try it in the playground</h2>
                <p>Add your <a href="{rapid_url}" target="_blank" rel="noopener">RapidAPI key</a> and run. Key is sent only to RapidAPI.</p>
                <div class="playground">
                    <label for="api-key">RapidAPI Key (required)</label>
                    <input type="password" id="api-key" placeholder="Your RapidAPI key" autocomplete="off">
                    {playground_body}
                    <button type="button" id="run-btn">Run request</button>
                    <div id="play-result" class="result" style="display:none;" aria-live="polite"></div>
                </div>
            </section>
            <section>
                <h2 id="code">Copy code</h2>
                <p>Host: <code>{host}</code>, endpoint: <code>POST {path}</code>. Choose language:</p>
                <div class="lang-tabs" role="tablist">
                    <button type="button" role="tab" aria-selected="true" data-lang="curl" class="active">cURL</button>
                    <button type="button" role="tab" aria-selected="false" data-lang="javascript">JavaScript</button>
                    <button type="button" role="tab" aria-selected="false" data-lang="python">Python</button>
                    <button type="button" role="tab" aria-selected="false" data-lang="java">Java</button>
                </div>
                <div id="snippet-curl" class="code-block active"><div class="code-wrap"><button type="button" class="copy-btn" data-copy="snippet-curl">Copy</button><pre><code>{escape(curl_example)}</code></pre></div></div>
                <div id="snippet-javascript" class="code-block"><div class="code-wrap"><button type="button" class="copy-btn" data-copy="snippet-javascript">Copy</button><pre><code>{escape(js_snippet)}</code></pre></div></div>
                <div id="snippet-python" class="code-block"><div class="code-wrap"><button type="button" class="copy-btn" data-copy="snippet-python">Copy</button><pre><code>{escape(python_snippet)}</code></pre></div></div>
                <div id="snippet-java" class="code-block"><div class="code-wrap"><button type="button" class="copy-btn" data-copy="snippet-java">Copy</button><pre><code>{escape(java_snippet)}</code></pre></div></div>
                <p><button type="button" class="postman-btn" id="postman-download">Download Postman collection</button></p>
            </section>
            <section><h2 id="expect">What to expect</h2><p>Response format depends on the endpoint. Use your RapidAPI key in headers. Stateless; no data stored. See <a href="{rapid_url}" target="_blank" rel="noopener">RapidAPI docs</a> for full response schema.</p></section>
            {about_section}
        </article>
        <footer>
            <p><a href="{rapid_url}" target="_blank" rel="noopener">Subscribe on RapidAPI</a> · <a href="../index.html">API Catalog</a></p>
            <p>© 2026 Precision Solutions Tech</p>
        </footer>
    </div>
    <script>
(function(){{
    var host='{host}',path='{path}',body={json.dumps(body)},fileUpload={str(file_upload).lower()},rapidUrl={json.dumps(rapid_url)};
    document.querySelectorAll('[data-rapid-docs]').forEach(function(a){{ a.href = rapidUrl; }});
    document.getElementById('toggle-req').addEventListener('click',function(e){{ e.preventDefault(); var d=document.getElementById('request-schema'); d.classList.toggle('show'); this.setAttribute('aria-expanded',d.classList.contains('show')); }});
    document.getElementById('toggle-res').addEventListener('click',function(e){{ e.preventDefault(); var d=document.getElementById('response-schema'); d.classList.toggle('show'); this.setAttribute('aria-expanded',d.classList.contains('show')); }});
    var toggleErrors=document.getElementById('toggle-errors');if(toggleErrors){{ toggleErrors.addEventListener('click',function(e){{ e.preventDefault(); var d=document.getElementById('error-codes'); d.classList.toggle('show'); this.setAttribute('aria-expanded',d.classList.contains('show')); }}); }}
    document.querySelectorAll('.lang-tabs button').forEach(function(btn){{
        btn.addEventListener('click',function(){{
            document.querySelectorAll('.lang-tabs button').forEach(function(b){{ b.classList.remove('active'); b.setAttribute('aria-selected','false'); }});
            document.querySelectorAll('.code-block').forEach(function(b){{ b.classList.remove('active'); }});
            this.classList.add('active'); this.setAttribute('aria-selected','true');
            var el=document.getElementById('snippet-'+this.getAttribute('data-lang')); if(el) el.classList.add('active');
        }});
    }});
    document.querySelectorAll('.copy-btn').forEach(function(btn){{
        btn.addEventListener('click',function(){{
            var id=this.getAttribute('data-copy'),block=document.getElementById(id),pre=block?block.querySelector('pre code'):null,btn=this;
            if(pre) navigator.clipboard.writeText(pre.textContent).then(function(){{ var t=btn.textContent; btn.textContent='Copied!'; setTimeout(function(){{ btn.textContent=t; }},1500); }});
        }});
    }});
    document.getElementById('postman-download').addEventListener('click',function(){{
        var coll = {{ info: {{ name: {json.dumps(title)}, schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json' }}, item: [{{ name: 'Request', request: {{ method: 'POST', header: [{{ key: 'Content-Type', value: 'application/json' }}, {{ key: 'x-rapidapi-key', value: 'YOUR_RAPIDAPI_KEY' }}, {{ key: 'x-rapidapi-host', value: host }}], url: 'https://'+host+path }} }} ] }};
        if(!fileUpload){{ coll.item[0].request.body = {{ mode: 'raw', raw: typeof body==='string'?body:JSON.stringify(body) }}; }}
        else {{ coll.item[0].request.header = [{{ key: 'X-RapidAPI-Key', value: 'YOUR_RAPIDAPI_KEY' }}, {{ key: 'X-RapidAPI-Host', value: host }}]; coll.item[0].request.url = 'https://'+host+path+'?outputFormat=json'; coll.item[0].request.body = {{ mode: 'formdata', formdata: [{{ key: 'file', type: 'file', src: '' }}] }}; }}
        var blob = new Blob([JSON.stringify(coll,null,2)], {{ type: 'application/json' }});
        var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '{slug}-postman-collection.json'; a.click(); URL.revokeObjectURL(a.href);
    }});
    var runBtn=document.getElementById('run-btn'),keyInput=document.getElementById('api-key'),resultDiv=document.getElementById('play-result');
    runBtn.addEventListener('click',function(){{
        var key=(keyInput.value||'').trim();
        if(!key){{ resultDiv.style.display='block'; resultDiv.className='result error'; resultDiv.textContent='Please enter your RapidAPI key.'; return; }}
        {run_script}
    }});
}})();
    </script>
</body>
</html>"""


def main():
    global RAPID_LINKS
    if os.path.exists(LINKS_PATH):
        with open(LINKS_PATH) as f:
            RAPID_LINKS = json.load(f)
    else:
        RAPID_LINKS = {}
    os.makedirs(OUT, exist_ok=True)
    apis_base = os.path.dirname(BASE)
    for c in CONFIG:
        rapid_data = load_rapid_data(apis_base, c["slug"])
        if rapid_data:
            if rapid_data.get("short_description"):
                c["description"] = rapid_data["short_description"]
            if rapid_data.get("long_description"):
                c["long_description"] = rapid_data["long_description"]
            if rapid_data.get("path"):
                c["path"] = rapid_data["path"]
            if rapid_data.get("body"):
                c["body"] = rapid_data["body"]
            if rapid_data.get("request_schema"):
                c["request_schema"] = rapid_data["request_schema"]
            if rapid_data.get("response_schema"):
                c["response_schema"] = rapid_data["response_schema"]
            if rapid_data.get("error_codes"):
                c["error_codes"] = rapid_data["error_codes"]
        path = os.path.join(OUT, c["slug"] + ".html")
        with open(path, "w") as f:
            f.write(template(c))
        print("Wrote", path)

    # Write sitemap.xml for Google and other search engines
    today = date.today().isoformat()
    base = SITEMAP_BASE_URL.rstrip("/")
    urls = [
        (f"{base}/", "1.0", "weekly"),
    ]
    for c in CONFIG:
        urls.append((f"{base}/apis/{c['slug']}.html", "0.8", "monthly"))
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, priority, changefreq in urls:
        sitemap_lines.append("  <url>")
        sitemap_lines.append(f"    <loc>{escape(loc)}</loc>")
        sitemap_lines.append(f"    <lastmod>{today}</lastmod>")
        sitemap_lines.append(f"    <changefreq>{changefreq}</changefreq>")
        sitemap_lines.append(f"    <priority>{priority}</priority>")
        sitemap_lines.append("  </url>")
    sitemap_lines.append("</urlset>")
    sitemap_path = os.path.join(BASE, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_lines))
    print("Wrote", sitemap_path)

    # Write robots.txt so crawlers can find the sitemap
    robots_path = os.path.join(BASE, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: {}/sitemap.xml\n".format(SITEMAP_BASE_URL.rstrip("/")))
    print("Wrote", robots_path)


if __name__ == "__main__":
    main()
