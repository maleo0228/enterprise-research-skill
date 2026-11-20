# -*- coding: utf-8 -*-
"""gap_lib.py — gap fidelity check core, shared by both entry points (v2.3.8).

Extracted from gap_fidelity_check.py so render.py can mount the same gate
via --gap-list without parsing a subprocess's text output. Both CLIs keep
their existing output format and exit codes.

Additions on top of the v2.3.7 checker (P1-4, v2.3.8): zero-result gaps may
carry an optional structured `zero_result_evidence: {channels[], actions[],
date}` field — graded enforcement:
  present -> strict format validation (malformed = error, blocks delivery)
  absent  -> the existing warnings-level reason checks apply (unchanged)
Zero network, standard library only.
"""
import json
import re

CARRIER_RE = re.compile(r"^(financial\.blocks\[(\d+)\]|basic_info:(.+)|mechanisms:(.+)|directions:(.+)|text:(.+))$")
SOURCE_ID_RE = re.compile(r"^E\d+$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
ZERO_RESULT_HINTS = ("检索未见", "公开渠道", "零结果", "not indexed", "no public", "zero-result")


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


def check_zero_result_evidence(g, gid, errors):
    """P1-4 (v2.3.8): optional structured zero-result evidence — graded.

    Present -> strict format validation (errors). Absence is NOT an error;
    the warnings-level reason checks in run_gap_check still apply.
    """
    zre = g.get("zero_result_evidence")
    if zre is None:
        return
    if not isinstance(zre, dict):
        errors.append("gap %s: zero_result_evidence must be an object "
                      "{channels[], actions[], date}, got %r" % (gid, type(zre).__name__))
        return
    for key in ("channels", "actions"):
        val = zre.get(key)
        if not (isinstance(val, list) and val
                and all(isinstance(x, str) and x.strip() for x in val)):
            errors.append("gap %s: zero_result_evidence.%s must be a non-empty "
                          "list of non-empty strings" % (gid, key))
    date = zre.get("date")
    if not (isinstance(date, str) and DATE_RE.search(date)):
        errors.append("gap %s: zero_result_evidence.date must be a string "
                      "containing YYYY-MM-DD" % gid)


def run_gap_check(raw, report, strict=False):
    """Run the full fidelity check.

    Returns (errors, warnings, oks, gap_count). `strict` only affects the
    caller-facing exit policy (warnings-as-failures); result lists are the
    same in both modes.
    """
    errors, warnings, oks = [], [], []
    if not isinstance(report, dict):
        return ["report.json is not a JSON object"], warnings, oks, 0
    gaps = raw.get("gaps") if isinstance(raw, dict) else raw
    if not isinstance(gaps, list) or not gaps:
        return ["gap list is empty or not a list — §7.3 gap list is a mandatory "
                "research-stage output; nothing to check against"], warnings, oks, 0

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
                oks.append("gap %s carried at %s" % (gid, g.get("carrier")))
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
                    oks.append("gap %s resolved with evidence %s" % (gid, ", ".join(ids)))
        if any(h in reason for h in ZERO_RESULT_HINTS):
            if not DATE_RE.search(reason + str(g.get("impact", ""))):
                warnings.append("gap %s: zero-result reason lacks an execution "
                                "date (§1.5 evidence trio: channels / actions / date)" % gid)
            if len(reason.strip()) < 8:
                warnings.append("gap %s: zero-result reason is too thin to carry "
                                "the §1.5 evidence trio" % gid)
        # P1-4 (v2.3.8): optional structured evidence — present means strict format
        check_zero_result_evidence(g, gid, errors)

    # check 4: bidirectional, financial scope — orphan missing blocks
    for idx, b in enumerate(blocks):
        if b.get("type") == "missing" and idx not in claimed_blocks:
            warnings.append("financial.blocks[%d] (missing) is not claimed by any "
                            "open gap — add it to the §7.3 gap list or keep the "
                            "on-site note self-contained" % idx)

    return errors, warnings, oks, len(gaps)
