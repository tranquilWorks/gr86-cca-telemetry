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

# Capture the exact redlined inputs before starting a fresh replay.
import hashlib, os, xml.etree.ElementTree as ET
root = Path(__file__).resolve().parents[2]
cad = root / "candidate/cad"
binding = {p.relative_to(cad).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(cad.rglob("*")) if p.is_file()}
q.main()
assert binding == {p.relative_to(cad).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(cad.rglob("*")) if p.is_file()}, "CAD changed during replay"


# Correct/augment the summary with procurement-specific metadata after the common
# runner has completed its acceptance calculation.
out = Path(os.environ.get("I32_PROCUREMENT_SPICE_OUT",str(Path(__file__).resolve().parent / "procurement_redline/spice"))) / "QUALIFICATION_SUMMARY.json"
s = json.loads(out.read_text())
s["procurement_bound_final"] = final
s["native_CAD_sha256"] = binding
s["source_PCB_sha256"] = binding["GR86_CCA_RevB.kicad_pcb"]
cases=json.loads(out.with_name("SWAP_RESULTS.json").read_text())
fine=next(x for x in cases if x["parameters"]["name"]=="swap__high_reference_1us_resolution")
coarse=next(x for x in cases if x["parameters"]["name"]=="swap__high_reference_slow_loop_low_damping")
supercase=cases[-1]
assert fine["completed"] and fine["main_peak_V"]<3.6
assert abs(fine["main_peak_V"]-coarse["main_peak_V"])<1e-5
assert supercase["completed"] and supercase["I121_max_A"]<2.5 and supercase["main_peak_V"]<3.6
s["high_side_1us_confirmation_V"]=fine["main_peak_V"]
s["superstress_30p08uH_PASS"]=True
s["L121_rating_note"]="Manufacturer operating range is -40..125 C including self-heating; -55/155 C resistance corners are deliberate model superstress, not rated operating claims."
s["physical_tests"]=0
s["R156_note"] = "Final JLC procurement choice is PLT1206Z5051LBTS / C4074185, exact 5.05k, +/-0.01%, 5ppm/C. Its manufacturer-qualified 1206 land pattern is applied to the native CAD."
s["R160_note"] = "Final JLC procurement choice is RT0805BRB076K34L / C864499, exact 6.34k, +/-0.1%, 10ppm/C; electrically tighter than the first-run R160 total-error envelope."
s["R169_note"] = "Final JLC procurement choice is PTFR0603B3K01N9 / C2692830, exact 3.01k, +/-0.1%, 10ppm/C; this run explicitly requalifies its looser corner."
s["thermal_rating_screen"] = {
    "historical_pre_redline_board_screen_C": 113.69713864995664,
    "R156_rated_max_C": 125,
    "R169_rated_max_C": 125,
    "board_screen_margin_to_125C_C": 11.30286135004336,
    "note": "Historical comparison only. Final procurement_redline/thermal evidence independently rechecks new copper, placements and package limits. Physical correlation remains a first-article gate."
}
out.write_text(json.dumps(s, indent=2)+"\n")
print("FINAL_PROCUREMENT_QUALIFICATION "+json.dumps(s, sort_keys=True), flush=True)
