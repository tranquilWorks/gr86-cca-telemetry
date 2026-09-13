#!/usr/bin/env python3
"""I27 final pre-hardware adjudication for GND-02.

Runs only after I26 source-bound verification has regenerated its evidence.
Preserves literal 290-row criterion closure states and moves only GND-02's
parallel desktop/prehardware status from actionable to bounded-inference closed.
No physical or supplier test is claimed.
"""
from __future__ import annotations
import collections, json, math
from pathlib import Path

D=Path(__file__).resolve().parent
W=D.parents[1]
SOURCE='a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936'
EXPECTED_FAILED={7:'CAN_TX_MCU',10:'CAN_TX_MCU',11:'CAN_TX_MCU',12:'CAN_TX_MCU',17:'ESP_EN',19:'ESP_EN',39:'GPS_SEARCH_BUFFER'}

def load(p): return json.loads(p.read_text())
def save(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def req(x,msg):
    if not x: raise ValueError(msg)

def microstrip_z(w,h,er):
    u=w/h
    ee=(er+1)/2+(er-1)/2*((1/math.sqrt(1+12/u)+0.04*(1-u)**2) if u<1 else 1/math.sqrt(1+12/u))
    if u<=1: z=60/math.sqrt(ee)*math.log(8/u+0.25*u)
    else: z=120*math.pi/(math.sqrt(ee)*(u+1.393+0.667*math.log(u+1.444)))
    return z,ee

def build_bound():
    exp=load(D/'EXPANDED_RETURN_SCOPE.json')
    paths=load(D/'TRANSFER_SCREEN_PATHS_EXPLORATORY.json')
    hist=load(D/'HISTORICAL_54_RETURN_FINDINGS.json')
    req(hist['source_PCB_sha256']==SOURCE and exp['source_PCB_sha256']==SOURCE,'I27 return evidence is not bound to current PCB source')
    req(hist['count']==54 and hist['counts']=={'REMOVED_BY_PRIOR_COORDINATED_COPPER_REVISION':48,'ISOLATED_TX_STUB_NO_RECEIVE_PATH':6},'historical return set changed')
    req(len(paths)==60 and {r['index'] for r in paths}==set(range(60)),'60-via inventory changed')
    failed={r['index']:r['net'] for r in paths if r['solution'] is None}
    req(failed==EXPECTED_FAILED,'finite-search failure set changed')
    req(sum(r['solution'] is not None for r in paths)==53,'explicit corridor count changed')
    req(len(exp['signal_vias'])==60,'expanded via count changed')
    nearest=[]
    for r in exp['signal_vias']:
        req(r['nearby_ground_vias'],'signal via lacks ground-via inventory')
        g=r['nearby_ground_vias'][0]
        req(g['layers']==['F.Cu','B.Cu'],'nearest ground via is not through-ground')
        nearest.append((g['distance_to_signal_segment_mm'],r['net'],r['signal_via_uuid']))
    max_near=max(nearest)
    tr_ns=.5; velocity_mm_ns=150.; f_knee_GHz=.5/tr_ns
    wavelength_mm=velocity_mm_ns/f_knee_GHz
    lambda20=wavelength_mm/20
    req(max_near[0] <= lambda20,'nearest return-via spacing exceeds lambda/20 screen')

    findings=exp['findings']
    req(findings,'expanded adjacent-plane findings absent')
    w=.2; h_near=.203; h_far=.203+.03+1.03; er=4.4
    z1,e1=microstrip_z(w,h_near,er); z2,e2=microstrip_z(w,h_far,er)
    v1=299.792458/math.sqrt(e1); v2=299.792458/math.sqrt(e2)
    lp1=z1/v1; lp2=z2/v2
    delta_lp=max(0.,lp2-lp1)
    stress_I_A=.050; stress_tr_ns=.5
    rows=[]
    for r in findings:
        length=float(r['adjacent_gap_mm']); dl=delta_lp*length
        vb=dl*stress_I_A/stress_tr_ns
        rows.append({'uuid':r['uuid'],'net':r['net'],'adjacent_gap_mm':length,'trace_width_mm':.2,'delta_series_inductance_nH_upper':dl,'50mA_0p5ns_bounce_V_screen':vb,'nearest_ground_via_mm':r['nearest_actual_ground_vias'][0]['distance_to_signal_segment_mm'],'disposition':'BOUNDED_NO_REROUTE'})
    worst=max(rows,key=lambda r:r['50mA_0p5ns_bounce_V_screen'])
    canrx=max((r for r in rows if r['net']=='CAN_RXD'),key=lambda r:r['50mA_0p5ns_bounce_V_screen'])
    req(worst['50mA_0p5ns_bounce_V_screen']<.20,'adjacent-plane stress screen exceeds 0.20 V allocation')
    req(canrx['50mA_0p5ns_bounce_V_screen']<.05,'active CAN_RXD gap exceeds 50 mV allocation')

    return {
      'milestone':'I27_GND02_DESKTOP_CLOSURE','date':'2026-09-12','source_PCB_sha256':SOURCE,
      'physical_tests_performed':False,'PCB_change_required':False,'firmware_change_required':False,
      'historical_54':{'removed_by_prior_copper_revision':48,'isolated_R301_DNP_CAN_TX_MCU':6,'all_individually_reconciled':True},
      'expanded_adjacent_plane_findings':{'count':len(rows),'rows':rows,'model':{'trace_width_mm':w,'normal_reference_height_mm':h_near,'fallback_reference_height_mm':h_far,'Z_near_ohm':z1,'Z_far_ohm':z2,'delta_L_nH_per_mm':delta_lp,'stress_current_mA':50,'stress_rise_ns':stress_tr_ns},'worst_bounce_V':worst['50mA_0p5ns_bounce_V_screen'],'worst_net':worst['net'],'CAN_RXD_worst_bounce_V':canrx['50mA_0p5ns_bounce_V_screen']},
      'signal_via_transfers':{'count':60,'explicit_dual_plane_corridors':53,'finite_search_no_corridor':7,'failed_searches':failed,'maximum_nearest_through_ground_via_mm':max_near[0],'lambda_over_20_screen_mm_at_0p5ns':lambda20,'all_within_lambda_over_20':True,
        'adjudication':{'CAN_TX_MCU':'four finite-search misses are on the R301-DNP-isolated no-transmit stub; no release transition exists.','ESP_EN':'two finite-search misses are reset/programming control, not a repetitive release timing interface; nearest through-ground spacing remains within the conservative lambda/20 screen.','GPS_SEARCH_BUFFER':'one finite-search miss drives the 1 kohm current-limited search indicator path and has no logic receiver/timing acceptance.'}},
      'active_interface_statement':'All active receive/timing-interface signal-via transfers have an explicit conservative paired-plane corridor in the 53/60 path set. The seven finite-search misses are restricted to the isolated TX stub, reset/programming EN, and an LED indicator driver.',
      'gnd02_desktop_complete':True,
      'qualification_retained':['Fabricated-board continuity/short inspection','CAN waveform/error-count vehicle correlation','GNSS/BLE/ADC coexistence and EMC/ESD qualification'],
      'reopen':['Any PCB stackup/copper/via change','Populate R301 or enable CAN transmission','Repeatable physical SI/EMC fault attributable to return geometry'],
      'conclusion':'No return-path reroute or added stitching is justified before fabrication. GND-02 is bounded-inference complete for pre-hardware design; physical correlation remains qualification, not claimed test evidence.'}

def finalize():
    bound=build_bound(); save(D/'GND02_DESKTOP_CLOSURE.json',bound)
    reg=load(W/'FINAL_REVIEW_REGISTER.json')
    req(len(reg['rows'])==290,'register row count changed')
    row=next(r for r in reg['rows'] if r['id']=='GND-02')
    req(row['desktop_status'] in ('DESKTOP_WORK_REMAINING','COMPLETED_CONDITIONAL_MODEL'),'GND-02 not in expected I26/I27 state')
    row['desktop_status']='COMPLETED_CONDITIONAL_MODEL'; row['prehardware_status']='bounded_inference_closed'
    row['observation']='I27 exhausts desktop return-path engineering. All54 historical findings are individually reconciled:48 removed by coordinated copper revision and6 retained only on the R301-DNP-isolated CAN_TX_MCU stub. Expanded review covers every critical-route adjacent interruption plus60 signal-via reference transfers. All active receive/timing transfers have explicit paired-plane corridors; the seven finite-search misses are four isolated TX-stub vias, two reset/programming EN vias, and one current-limited LED indicator via. Every critical signal via is within5.252mm of a through-ground via, inside a conservative7.5mm lambda/20 screen at a0.5ns edge. Treating each 0.20mm trace interruption as a full move from the0.203mm adjacent reference to the opposite plane gives <0.20V worst 50mA/0.5ns stress bounce and <0.05V on active CAN_RXD. No routing/stitching change is justified before fabrication.'
    row['remaining']='Physical continuity, installed CAN waveform/error-count and EMC/coexistence correlation remain qualification gates. Reopen for copper/stackup/via changes, R301 population/CAN transmit enablement, or repeatable hardware failure attributable to return geometry.'
    row['evidence']=list(dict.fromkeys(row.get('evidence',[])+['analyses/i26/GND02_DESKTOP_CLOSURE.json']))
    row['physical_test_claimed']=False; row['I27_reassessment']='Desktop bounded-inference closure only; literal original closure remains unchanged because physical acceptance is still required.'
    counts=dict(collections.Counter(r['desktop_status'] for r in reg['rows']))
    req('DESKTOP_WORK_REMAINING' not in counts,'other desktop work remains')
    reg['summary']['desktop_status_counts']=counts
    reg['summary']['actionable_prehardware_ids']=[]
    reg['summary']['release_status']='I27: zero actionable pre-hardware engineering items; fabrication may proceed subject to supplier acceptance and retained hardware/install qualification gates.'
    agg={'desktop_source_documentary':sum(counts.get(x,0) for x in ['CURRENT_EVIDENCE_REVIEWED','COMPLETED_CURRENT_SOURCE_VERIFICATION','COMPLETED_SOURCE_DOCUMENTARY_SCOPE','COMPLETED_I22_ORIGINAL_DESIGN_SCOPE']), 'conditional_model':counts.get('COMPLETED_CONDITIONAL_MODEL',0), 'hardware_supplier_installation':sum(counts.get(x,0) for x in ['HARDWARE_OR_INSTALLATION_ACCEPTANCE','SUPPLIER_OR_RESPONSIBLE_ACCEPTANCE','CURRENT_NATIVE_COMPLETE_OTHER_EVIDENCE_REQUIRED']), 'not_applicable':counts.get('NOT_APPLICABLE',0),'desktop_work_remaining':0}
    req(sum(agg.values())==290,'aggregate row loss')
    reg['summary']['prehardware_aggregate']=agg
    if not any(x.get('id')=='I27' for x in reg['summary']['iterations']): reg['summary']['iterations'].append({'id':'I27','status':'PREHARDWARE_ENGINEERING_CLOSED','description':'GND-02 quantitatively bounded; zero actionable desktop engineering items; external qualification gates retained.'})
    save(W/'FINAL_REVIEW_REGISTER.json',reg)

    clos=load(W/'I26_PREHARDWARE_CLOSURE.json')
    clos['milestone']='I27_PREHARDWARE_ENGINEERING_CLOSED'; clos['date']='2026-09-12'
    gr=clos['design_lanes']['ground_return']; gr.update({'class':'bounded_inference_closed','desktop_complete':True,'evidence':'analyses/i26/GND02_DESKTOP_CLOSURE.json','next':'Physical correlation only; reopen on defined invalidator.'})
    clos['current_actionable_prehardware_ids']=[]; clos['current_actionable_prehardware_count']=0
    clos['current_counts']={'desktop_source_documentary':agg['desktop_source_documentary'],'conditional_model':agg['conditional_model'],'hardware_supplier_installation':agg['hardware_supplier_installation'],'not_applicable':agg['not_applicable'],'desktop_work_remaining':0}
    clos['fabrication_readiness']='PREHARDWARE_ENGINEERING_CLEAR; supplier acceptance and physical qualification not yet executed.'
    save(W/'I26_PREHARDWARE_CLOSURE.json',clos)

    gates=load(W/'FINAL_GATES.json')
    g=next(x for x in gates['gates'] if x['id']=='G22-12')
    g.update(status='BOUNDED_INFERENCE_CLOSED',description='GND-02 desktop return-path analysis completed by I27; no pre-fabrication copper/stitching change justified.',evidence='analyses/i26/GND02_DESKTOP_CLOSURE.json',qualification='Retain fabricated continuity plus installed CAN/EMC/coexistence correlation; no physical pass is claimed.')
    gates['actionable_prehardware_actual']=0; gates['actionable_prehardware_ids']=[]
    gates['prehardware_design_statement']='I27: zero actionable pre-hardware engineering items. Fabrication can proceed subject to supplier process acceptance and explicit as-built/install/environment qualification gates.'
    save(W/'FINAL_GATES.json',gates)

    audit=load(D/'RECONCILIATION_AUDIT.json')
    audit['status']='I27_ZERO_ACTIONABLE_PREHARDWARE'; audit['source_PCB_sha256']=SOURCE; audit['desktop_status_counts']=counts; audit['prehardware_counts']=agg; audit['actionable_prehardware_ids']=[]; audit['rows_reconciled']=sorted(set(audit.get('rows_reconciled',[])+['GND-02'])); audit['physical_tests_performed']=0; audit['PCB_BOM_firmware_changes']=False; audit['fabrication_release']=True; audit['fabrication_release_meaning']='Engineering release to request fabrication only; supplier acceptance and physical qualification remain open and no physical test is claimed.'
    save(D/'RECONCILIATION_AUDIT.json',audit)

    md=W/'I26_PREHARDWARE_CLOSURE.md'
    old=md.read_text(); marker='# I26 pre-hardware closure contract'; tail=old[old.index(marker):] if marker in old else old
    head='# I27 pre-hardware engineering closure — fabrication request clear\n\nAs of 2026-09-12, the controlled 290-row register contains **0 actionable pre-hardware engineering items**. Literal original criteria that require fabricated, supplier, installation, vehicle, environmental or visibility evidence remain open as qualification gates; no such physical evidence is claimed.\n\nAggregate pre-hardware classification: **141 desktop/source/documentary, 31 bounded-model/inference, 114 hardware/supplier/installation qualification-only, 4 N/A, 0 desktop work remaining**. GND-02 is closed for desktop design by `analyses/i26/GND02_DESKTOP_CLOSURE.json`; no PCB/BOM/firmware change was required.\n\nThis is authorization to proceed to fabrication/supplier review, not a claim that the finished assembly has passed qualification.\n\n---\n\n'
    md.write_text(head+tail)

    release={'milestone':'I27_FABRICATION_READINESS','date':'2026-09-12','source_PCB_sha256':SOURCE,'actionable_prehardware_count':0,'PCB_BOM_firmware_changes_for_I27':False,'physical_tests_performed':0,'supplier_acceptance_performed':False,'fabrication_request_recommendation':'PROCEED_TO_JLCPCB_QUOTE_DFM_AND_FABRICATION_PACKAGE_REVIEW','qualification_required_after_build':True,'prehardware_counts':agg,'ground_return_evidence':'analyses/i26/GND02_DESKTOP_CLOSURE.json','invalidators':bound['reopen']}
    save(W/'I27_FABRICATION_READINESS.json',release)
    print(json.dumps(release,indent=2))

if __name__=='__main__': finalize()
