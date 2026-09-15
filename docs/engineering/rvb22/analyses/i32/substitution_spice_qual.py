#!/usr/bin/env python3
"""Fresh ngspice qualification of frozen I32 JLC substitution electrical bounds.

No ECAD mutation. Reuses the exact I32 selected transient model/case matrix and
applies frozen replacement component electrical corners.
"""
from pathlib import Path
import copy, json, shutil, sys, time

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import power_chain as pc
import selected_power_cases as spc

CAND = {
    "R155": {"mpn":"PTFR0603B11K8N9", "nom":11800.0, "tol":0.0010, "tcr_ppm":10.0, "drift":0.0010},
    "R156": {"mpn":"PLT1206Z5051LBTS", "nom":5050.0, "tol":0.0001, "tcr_ppm":5.0, "drift":0.0010},
    "R160": {"mpn":"RT0805BRB076K34L", "nom":6340.0, "tol":0.0010, "tcr_ppm":10.0, "drift":0.0010},
    "R161": {"mpn":"PTFR0603Q1K00N9", "nom":1000.0, "tol":0.0002, "tcr_ppm":10.0, "drift":0.0010},
    "R162": {"mpn":"PTFR0603Q4K70N9", "nom":4700.0, "tol":0.0002, "tcr_ppm":10.0, "drift":0.0010},
    "R163": {"mpn":"PTFR0603Q1K00N9", "nom":1000.0, "tol":0.0002, "tcr_ppm":10.0, "drift":0.0010},
    "R169": {"mpn":"PTFR0603B3K01N9", "nom":3010.0, "tol":0.0010, "tcr_ppm":10.0, "drift":0.0010},
    "R170": {"mpn":"PTFR0603Q1K00N9", "nom":1000.0, "tol":0.0002, "tcr_ppm":10.0, "drift":0.0010},
}
DT_HOT_C = 130.0
for ref, v in CAND.items():
    dt = 100.0 if ref in {"R156", "R169"} else DT_HOT_C
    v["total_frac"] = v["tol"] + v["tcr_ppm"]*1e-6*dt + v["drift"]
# The Q-grade 0603 allocations retain the recovered 0.25% total bounds.
for ref in ("R161", "R162", "R163", "R170"):
    CAND[ref]["total_frac"] = 0.0025

L121 = {
    "mpn":"BPCI00121280470M00",
    "nom_H":47e-6,
    "tol":0.20,
    "DCR_25C_max_ohm":0.100,
    "Isat_A":2.5,
    "Irated_A":2.5,
}
CU_TC = 0.00393
L121["DCR_155C_max_ohm"] = L121["DCR_25C_max_ohm"] * (1 + CU_TC*130.0)
L121["DCR_m55C_est_ohm"] = L121["DCR_25C_max_ohm"] * (1 - CU_TC*80.0)

def scale_direction(original, err):
    if original > 1.00000001:
        return 1.0 + err
    if original < 0.99999999:
        return 1.0 - err
    return 1.0

def candidate_case(src):
    p = copy.deepcopy(src)
    p["name"] = "swap__" + src["name"]
    p["_swap_qualification"] = True
    p["fb_top_scale"] = scale_direction(src.get("fb_top_scale",1.0), CAND["R155"]["total_frac"])
    p["fb_bottom_scale"] = scale_direction(src.get("fb_bottom_scale",1.0), CAND["R156"]["total_frac"])
    p["sns_top_scale"] = scale_direction(src.get("sns_top_scale",1.0), CAND["R160"]["total_frac"])
    p["sns_bottom_scale"] = scale_direction(src.get("sns_bottom_scale",1.0), CAND["R161"]["total_frac"])
    p["iso_en_top_scale"] = scale_direction(src.get("iso_en_top_scale",1.0), CAND["R162"]["total_frac"])
    p["iso_en_bottom_scale"] = scale_direction(src.get("iso_en_bottom_scale",1.0), CAND["R163"]["total_frac"])
    p["bulk_en_top_scale"] = scale_direction(src.get("bulk_en_top_scale",1.0), CAND["R169"]["total_frac"])
    p["bulk_en_bottom_scale"] = scale_direction(src.get("bulk_en_bottom_scale",1.0), CAND["R170"]["total_frac"])
    if src.get("L121_scale",1.0) < 1.0:
        p["L121_scale"] = 0.80
    elif src.get("L121_scale",1.0) > 1.0:
        p["L121_scale"] = 1.20
    else:
        p["L121_scale"] = 1.0
    p["_L121_DCR_ohm"] = L121["DCR_155C_max_ohm"]
    p["_source_case"] = src["name"]
    return p

_orig_build = pc.build
def build_swap(p):
    s = _orig_build(p)
    if p.get("_swap_qualification"):
        target = p.get("_L121_DCR_ohm", L121["DCR_155C_max_ohm"])
        lines=[]
        found=0
        for line in s.splitlines():
            if line.startswith("R_L121 winding5 source5 "):
                line=f"R_L121 winding5 source5 {target:.12g}"
                found += 1
            lines.append(line)
        if found != 1:
            raise RuntimeError(f"Expected exactly one R_L121, got {found}")
        s="\n".join(lines)+"\n"
    return s
pc.build = build_swap

def run_cases(cases, root, jobs=4):
    import concurrent.futures as cf
    root.mkdir(parents=True, exist_ok=True)
    results=[]
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        fut={ex.submit(pc.run_local,p,root):p for p in cases}
        for f in cf.as_completed(fut):
            p=fut[f]
            try:
                r=f.result()
            except Exception as e:
                r={"parameters":p,"completed":False,"exception":repr(e)}
            results.append(r)
            print(json.dumps({"case":p["name"],"completed":r.get("completed"),"main_peak_V":r.get("main_peak_V"),"normal_main_min_V":r.get("normal_main_min_V"),"I121_max_A":r.get("I121_max_A"),"ready_rises":r.get("ready_rises"),"sns_faults":r.get("sns_faults")}), flush=True)
    order={p["name"]:i for i,p in enumerate(cases)}
    results.sort(key=lambda r: order[r["parameters"]["name"]])
    return results

def accepted_summary(results):
    assert len(results) == 32
    assert all(v.get("completed") for v in results), "All 32 cases, including superstress, must complete"
    main=results[:31]
    assert all(v.get("completed") for v in main), [v["parameters"]["name"] for v in main if not v.get("completed")]
    normal=[v for v in main if v["parameters"].get("mode")!='off' and not v["parameters"].get("sns_fault") and not v["parameters"].get("live_fault")]
    assert len(normal)==17
    normal_sequence_ok=all(v["ready_rises"]==1 and v["sns_faults"]==0 and v["ready_final"]>.5 for v in normal)
    minrail=min(v.get("load_window_min_V",v["unmasked_post_ready_min_V"]) for v in normal)
    maxrail=max(v["main_peak_V"] for v in results)
    reverse=min(v["minimum_vin_minus_output_V"] for v in main if v["minimum_vin_minus_output_V"] is not None)
    max_i121=max(v["I121_max_A"] for v in results if v.get("completed") and v.get("I121_max_A") is not None)
    return {
        "completed":sum(bool(v.get("completed")) for v in results),
        "normal_case_count":len(normal),
        "normal_sequence_ok":normal_sequence_ok,
        "main_normal_min_V":minrail,
        "reset_limit_V":3.11605,
        "reset_margin_V":minrail-3.11605,
        "main_max_V":maxrail,
        "overshoot_margin_V":3.6-maxrail,
        "VIN_minus_source_min_V":reverse,
        "reverse_margin_V":reverse+0.3,
        "L121_peak_A":max_i121,
        "L121_Isat_A":L121["Isat_A"],
        "L121_Isat_margin_A":L121["Isat_A"]-max_i121,
        "L121_Isat_utilization":max_i121/L121["Isat_A"],
        "pass":bool(normal_sequence_ok and minrail>3.11605 and maxrail<3.6 and reverse>-0.3 and max_i121<L121["Isat_A"]),
    }

def main():
    out=Path(__import__("os").environ.get("I32_PROCUREMENT_SPICE_OUT",str(D/"procurement_redline/spice")))
    if out.exists(): raise FileExistsError("Preserve prior qualification; choose a new output directory")
    out.mkdir()
    selected=spc.cases()
    assert len(selected)==31
    swap=[candidate_case(x) for x in selected]

    source=next(x for x in selected if x["name"]=="minimum_inductance_saturation_guard")
    supercase=candidate_case(source)
    supercase["name"]="swap__extra_superstress_30p08uH_coldDCR"
    supercase["L121_scale"]=0.64
    supercase["_L121_DCR_ohm"]=max(0.001,L121["DCR_m55C_est_ohm"])
    supercase["max_step"]=1e-6

    control_names={"nominal_hot_leakage","low_reference_slow_loop_aged_damping","high_reference_slow_loop_low_damping","minimum_inductance_saturation_guard","live_crank_6V","live_overvoltage_24V"}
    controls=[copy.deepcopy(x) for x in selected if x["name"] in control_names]
    for x in controls: x["name"]="control__"+x["name"]

    t0=time.time()
    control_results=run_cases(controls,out/"controls",jobs=4)
    swap_results=run_cases(swap+[supercase],out/"swaps",jobs=4)
    summary=accepted_summary(swap_results)
    summary.update({
        "status":"PASS" if summary["pass"] else "FAIL",
        "elapsed_s":time.time()-t0,
        "candidate_bounds":CAND,
        "L121":L121,
        "C152_C154_C165":"No electrical parameter change; same 220nF 50V X7R +/-10% behavior retained.",
        "U101":"No electrical model change: LTC4367HMS8#PBF is the same H-grade LTC4367 electrical device; #W pedigree difference is manufacturing qualification, not circuit function.",
        "R156_note":"Final wrapper applies PLT1206Z5051LBTS exact limits and source binding.",
        "solver":shutil.which("ngspice"),
    })
    (out/"QUALIFICATION_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    (out/"CONTROL_RESULTS.json").write_text(json.dumps(control_results,indent=2)+"\n")
    (out/"SWAP_RESULTS.json").write_text(json.dumps(swap_results,indent=2)+"\n")
    print("QUALIFICATION_FINAL "+json.dumps(summary,sort_keys=True), flush=True)
    if not summary["pass"]:
        raise SystemExit(2)

if __name__=="__main__": main()
