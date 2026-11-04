# -*- coding: utf-8 -*-
"""gap_fidelity_check.py — research-stage output → deliverable fidelity gate.

Scope (agreed 2026-11-04): the contract carries gaps ONLY in the financial
section (`overview.financial.blocks`, type=missing) and as annotated
basic_info cells; the research-stage gap list (spec §7.3) covers the whole
study. This script therefore checks fidelity only where a mechanical mapping
exists, and never demands carriers the contract cannot express.

Usage:
    python renderer/gap_fidelity_check.py <gap-list.json> report.json [--strict]

gap-list.json (machine form of spec §7.3; top-level list or {"gaps": [...]}):
    [{
      "id": "G1",                # optional; auto-assigned in order
      "item": "...",             # required — what was sought but not obtained
      "reason": "...",           # required — why it is missing
      "impact": "...",           # required — which conclusions are narrowed
      "status": "open|resolved", # default "open"
      "carrier": "...",          # required when open — where the gap lives in
                                 # the report; syntax:
                                 #   financial.blocks[N]  (0-based index of an
                                 #                        overview.financial block;
                                 #                        type=missing preferred)
                                 #   basic_info:<label>   (basic_info row whose
                                 #                        value carries the gap)
                                 #   mechanisms:<substr>  (text searched in the
                                 #                        mechanisms section JSON)
                                 #   directions:<substr>  (text searched in the
                                 #                        directions section JSON)
                                 #   text:<substr>        (text searched in the
                                 #                        whole report JSON)
      "resolution_evidence": "E5" # required when resolved — source id backing
                                  # the now-available data
    }]

Checks:
    1. gap-list schema (required fields, status enum)
    2. every open gap resolves to a real carrier in report.json
       (financial/baic_info carriers additionally validated structurally)
    3. every resolved gap cites an existing source id that is actually used
    4. bidirectional, financial scope only: every type=missing block is
       claimed by some open gap (or at minimum carries a non-empty on-site
       note — always true under the schema, so unclaimed blocks warn)
    5. zero-result gaps (reason suggests 检索未见/公开渠道不可得) carry the
       §1.5 evidence trio as far as is mechanically checkable (a date and a
       non-trivial reason)

Exit code: 0 = pass (warnings allowed), 1 = failures listed.
--strict upgrades warnings to failures (due-diligence deliveries).
Zero network, standard library only.
"""
import json
import re
import sys

CARRIER_RE = re.compile(r"^(financial\.blocks\[(\d+)\]|basic_info:(.+)|mechanisms:(.+)|directions:(.+)|text:(.+))$")
SOURCE_ID_RE = re.compile(r"^E\d+$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
ZERO_RESULT_HINTS = ("检索未见", "公开渠道", "零结果", "not indexed", "no public", "zero-result")


def fail(msg):
    print("FAIL  " + msg)


def warn(msg):
    print("WARN  " + msg)


def ok(msg):
    print("ok    " + msg)


def load_json(path, label, errors):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001 - gate reports any read/parse error
        errors.append("%s unreadable/invalid: %s" % (label, e))
        return None


def section_json(report, name):
    return json.dumps(report.get(name, {}), ensure_ascii=False)


def check_gap_list_shape(gaps, errors):
    seen_ids = set()
    for i, g in enumerate(gaps):
        if not isinstance(g, dict):
            errors.append("gap[%d] is not an object" % i)
            continue
        for field in ("item", "reason", "impact"):
            if not str(g.get(field, "")).strip():
                errors.append("gap[%d] missing required field '%s'" % (i, field))
        gid = str(g.get("id") or "G%d" % (i + 1))
        if gid in seen_ids:
            errors.append("duplicate gap id %s" % gid)
        seen_ids.add(gid)
        if g.get("status", "open") not in ("open", "resolved"):
            errors.append("gap %s: status must be open|resolved" % gid)
        if g.get("status", "open") == "open" and not str(g.get("carrier", "")).strip():
            errors.append("gap %s is open but has no carrier" % gid)
        if g.get("status") == "resolved" and not str(g.get("resolution_evidence", "")).strip():
            errors.append("gap %s is resolved but has no resolution_evidence" % gid)


def resolve_carrier(gap, report, warnings):
    """Return (hard_errors, carrier_claims_financial_block_index_or_None)."""
    gid = gap.get("id") or "?"
    carrier = str(gap.get("carrier", "")).strip()
    errs, claimed = [], None
    m = CARRIER_RE.match(carrier)
    if not m:
        errs.append("gap %s: carrier syntax not recognized: %r "
                    "(expected financial.blocks[N] | basic_info:<label> | "
                    "mechanisms:<substr> | directions:<substr> | text:<substr>)"
                    % (gid, carrier))
        return errs, claimed
    blocks = report.get("overview", {}).get("financial", {}).get("blocks", [])
    if m.group(2) is not None:
        idx = int(m.group(2))
        if idx >= len(blocks):
            errs.append("gap %s: financial.blocks[%d] out of range (%d blocks)"
                        % (gid, idx, len(blocks)))
        else:
            claimed = idx
            if blocks[idx].get("type") != "missing":
                warnings.append("gap %s: carrier financial.blocks[%d] is type=%s, "
                                "not missing — prefer a missing block or a '—' cell note"
                                % (gid, idx, blocks[idx].get("type")))
    elif m.group(3) is not None:
        label, infos = m.group(3), report.get("overview", {}).get("basic_info", [])
        row = next((r for r in infos if r.get("label") == label), None)
        if row is None:
            errs.append("gap %s: basic_info has no row labelled %r" % (gid, label))
        elif "未公开披露" not in row.get("value_html", ""):
            errs.append("gap %s: basic_info row %r does not carry the "
                        "'未公开披露' marker in value_html" % (gid, label))
    else:
        kind = carrier.split(":", 1)[0]
        needle = carrier.split(":", 1)[1]
        hay = (section_json(report, "mechanisms") if kind == "mechanisms"
               else section_json(report, "directions") if kind == "directions"
               else json.dumps(report, ensure_ascii=False))
        if needle not in hay:
            errs.append("gap %s: carrier text %r not found in %s section"
                        % (gid, needle, kind))
    return errs, claimed


def main(argv):
    args = [a for a in argv[1:] if a != "--strict"]
    strict = "--strict" in argv[1:]
    if len(args) != 2:
        print(__doc__)
        return 2
    errors, warnings = [], []
    raw = load_json(args[0], "gap-list", errors)
    report = load_json(args[1], "report.json", errors)
    if errors:
        for e in errors:
            fail(e)
        return 1
    gaps = raw.get("gaps") if isinstance(raw, dict) else raw
    if not isinstance(gaps, list) or not gaps:
        fail("gap list is empty or not a list — §7.3 gap list is a mandatory "
             "research-stage output; nothing to check against")
        return 1

    check_gap_list_shape(gaps, errors)
    sources = {s.get("id") for s in report.get("sources", {}).get("items", [])}
    report_blob = json.dumps(report, ensure_ascii=False)
    blocks = report.get("overview", {}).get("financial", {}).get("blocks", [])

    claimed_blocks = set()
    for i, g in enumerate(gaps):
        if not isinstance(g, dict):
            continue
        gid = str(g.get("id") or "G%d" % (i + 1))
        g["id"] = gid
        status = g.get("status", "open")
        reason = str(g.get("reason", ""))
        if status == "open":
            errs, claimed = resolve_carrier(g, report, warnings)
            errors.extend(errs)
            if claimed is not None:
                claimed_blocks.add(claimed)
            if not errs:
                ok("gap %s carried at %s" % (gid, g.get("carrier")))
        else:  # resolved
            ev = str(g.get("resolution_evidence", "")).strip()
            ids = [t for t in re.split(r"[,\s，、]+", ev) if t]
            if not ids or not all(SOURCE_ID_RE.match(t) for t in ids):
                errors.append("gap %s: resolution_evidence must cite source id(s) "
                              "E<n>, got %r" % (gid, ev))
            else:
                for sid in ids:
                    if sid not in sources:
                        errors.append("gap %s: resolved evidence %s not in "
                                      "sources.items" % (gid, sid))
                    elif report_blob.count('"%s"' % sid) < 2:
                        errors.append("gap %s: resolved evidence %s exists but is "
                                      "never cited in the report body" % (gid, sid))
                if not any(e.startswith("gap %s" % gid) for e in errors):
                    ok("gap %s resolved with evidence %s" % (gid, ", ".join(ids)))
        if any(h in reason for h in ZERO_RESULT_HINTS):
            if not DATE_RE.search(reason + str(g.get("impact", ""))):
                warnings.append("gap %s: zero-result reason lacks an execution "
                                "date (§1.5 evidence trio: channels / actions / date)" % gid)
            if len(reason.strip()) < 8:
                warnings.append("gap %s: zero-result reason is too thin to carry "
                                "the §1.5 evidence trio" % gid)

    # check 4: bidirectional, financial scope — orphan missing blocks
    for idx, b in enumerate(blocks):
        if b.get("type") == "missing" and idx not in claimed_blocks:
            warnings.append("financial.blocks[%d] (missing) is not claimed by any "
                            "open gap — add it to the §7.3 gap list or keep the "
                            "on-site note self-contained" % idx)

    for w in warnings:
        warn(w)
    if errors:
        for e in errors:
            fail(e)
    print("\n%d gap(s): %d error(s), %d warning(s)"
          % (len(gaps), len(errors), len(warnings)))
    if strict and warnings and not errors:
        print("--strict: warnings treated as failures")
        return 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
