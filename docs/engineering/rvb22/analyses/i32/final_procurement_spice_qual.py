#!/usr/bin/env python3
"""Run the I32 substitution suite against the exact final procurement choices.

No ECAD mutation. This wrapper reuses substitution_spice_qual.py and replaces
only the procurement-bound resistor identities/corners that changed after the
first qualification run.
"""
from pathlib import Path
import json
import substitution_spice_qual as q

# Final procurement-bound choices.  Error allocations include initial tolerance,
# full 25C-to-rated-maximum TCR excursion, plus the same independent 0.10% drift
# allowance used by the first qualification.
final = {
    "R156": {"mpn":"PLT1206Z5051LBTS", "jlc":"C4074185", "nom":5050.0, "tol":0.0001, "tcr_ppm":5.0, "drift":0.0010, "dt_C":100.0, "package":"1206", "rated_max_C":125},
    "R160": {"mpn":"RT0805BRB076K34L", "jlc":"C864499", "nom":6340.0, "tol":0.0010, "tcr_ppm":10.0, "drift":0.0010, "dt_C":130.0, "package":"0805", "rated_max_C":155},
    "R169": {"mpn":"PTFR0603B3K01N9", "jlc":"C2692830", "nom":3010.0, "tol":0.0010, "tcr_ppm":10.0, "drift":0.0010, "dt_C":100.0, "package":"0603", "rated_max_C":125},
}
for ref, v in final.items():
    q.CAND[ref] = {k:v[k] for k in ("mpn","nom","tol","tcr_ppm","drift")}
    q.CAND[ref]["total_frac"] = v["tol"] + v["tcr_ppm"]*1e-6*v["dt_C"] + v["drift"]

q.main()

# Correct/augment the summary with procurement-specific metadata after the common
# runner has completed its acceptance calculation.
out = Path(__file__).resolve().parent / "substitution_spice_results" / "QUALIFICATION_SUMMARY.json"
s = json.loads(out.read_text())
s["procurement_bound_final"] = final
s["R156_note"] = "Final JLC procurement choice is PLT1206Z5051LBTS / C4074185, exact 5.05k, +/-0.01%, 5ppm/C. Its 1206 footprint change is intentionally deferred to redline/CAD work."
s["R160_note"] = "Final JLC procurement choice is RT0805BRB076K34L / C864499, exact 6.34k, +/-0.1%, 10ppm/C; electrically tighter than the first-run R160 total-error envelope."
s["R169_note"] = "Final JLC procurement choice is PTFR0603B3K01N9 / C2692830, exact 3.01k, +/-0.1%, 10ppm/C; this run explicitly requalifies its looser corner."
s["thermal_rating_screen"] = {
    "existing_I32_stacked_board_screen_C": 113.69713864995664,
    "R156_rated_max_C": 125,
    "R169_rated_max_C": 125,
    "board_screen_margin_to_125C_C": 11.30286135004336,
    "note": "Existing I32 board-region stacked sensitivity remains below the 125C ratings; resistor self-heating is milliwatt-scale. Physical thermal correlation remains a first-article gate."
}
out.write_text(json.dumps(s, indent=2)+"\n")
print("FINAL_PROCUREMENT_QUALIFICATION "+json.dumps(s, sort_keys=True), flush=True)
