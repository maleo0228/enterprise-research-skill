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
      "zero_result_evidence": {  # optional (v2.3.8, §1.5 structured form)
        "channels": ["官网", "招聘平台"],   # non-empty list of strings
        "actions":  ["站点检索", "JD 扫描"], # non-empty list of strings
        "date":     "2026-11-20"            # containing YYYY-MM-DD
      }                              # present -> strict format check (errors);
                                     # absent  -> warnings-level reason checks
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
       non-trivial reason; structured zero_result_evidence format-checked
       when present — v2.3.8)

Exit code: 0 = pass (warnings allowed), 1 = failures listed.
--strict upgrades warnings to failures (due-diligence deliveries).
Zero network, standard library only.

Implementation note (v2.3.8): the check core lives in gap_lib.py and is
shared with render.py's --gap-list gate; this file is the thin CLI wrapper.
Output format and exit codes are unchanged from v2.3.7.
"""
import sys

import gap_lib


def fail(msg):
    print("FAIL  " + msg)


def warn(msg):
    print("WARN  " + msg)


def ok(msg):
    print("ok    " + msg)


def main(argv):
    args = [a for a in argv[1:] if a != "--strict"]
    strict = "--strict" in argv[1:]
    if len(args) != 2:
        print(__doc__)
        return 2
    errors, warnings = [], []
    raw = gap_lib.load_json(args[0], "gap-list", errors)
    report = gap_lib.load_json(args[1], "report.json", errors)
    if errors:
        for e in errors:
            fail(e)
        return 1

    errors, warnings, oks, ngaps = gap_lib.run_gap_check(raw, report, strict=strict)
    for line in oks:
        ok(line)
    for w in warnings:
        warn(w)
    if errors:
        for e in errors:
            fail(e)
    print("\n%d gap(s): %d error(s), %d warning(s)"
          % (ngaps, len(errors), len(warnings)))
    if strict and warnings and not errors:
        print("--strict: warnings treated as failures")
        return 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
