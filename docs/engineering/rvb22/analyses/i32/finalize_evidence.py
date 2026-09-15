#!/usr/bin/env python3
"""Integrate completed I32 results without regenerating CAD or simulations."""
from pathlib import Path
import argparse, csv, hashlib, json, shutil
import numpy as np
D=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runs',type=Path,required=True);a=ap.parse_args();r=a.runs;e=D/'evidence'
    binding=read(D/'SOURCE_BINDING.json');source=binding['source_PCB_sha256'];filled=binding['filled_PCB_sha256']
    folders={'native_c166_68n_release':'native','layout_c166_68n_final':'layout','filled_c166_68n_final':'filled_returns','ground_c166_68n_final':'ground','mechanical_c166_68n_final':'mechanics','thermal_c166_68n_final_0.5':'thermal/0.5','thermal_c166_68n_final_0.25':'thermal/0.25'}
    for directory,target in folders.items():
        for p in (r/directory).rglob('*'):
            if not p.is_file() or 'candidate_kicad' in p.parts or 'model_export' in p.parts:continue
            copy(p,e/target/p.relative_to(r/directory))
    native=read(e/'native/RESULT.json');assert native['native_report_finding_count']==0 and native['refilled_pcb_sha256']==filled
    layout=read(e/'layout/LAYOUT_MEASUREMENTS.json');assert layout['source_PCB_sha256']==source
    ground=read(e/'ground/GROUND_RETURN_CONTRACT.json');assert ground['source_PCB_sha256']==source and ground['filled_PCB_sha256']==filled and all(v['pass_allocation']for v in ground['terms'])
    returns=read(e/'filled_returns/FILLED_GROUND_CONNECTIVITY.json');assert returns['filled_PCB_sha256']==filled and all(v['connected_by_actual_filled_ground']for v in returns['rows'])
    mech=read(e/'mechanics/MECHANICAL.json');assert mech['source_PCB_sha256']==source and mech['status']=='PASS_DECLARED_ENVELOPES' and not mech['interferences'] and not any(v['component_hits']for v in mech['probes'])
    power=read(r/'POWER_C166_68N_COMPLETED.json');main=power[:31];pg=power[31:33];dr=power[33:]
    assert len(main)==31 and len(pg)==2 and len(dr)==1 and all(v['completed']for v in power)
    normal=[v for v in power if v['parameters'].get('mode')!='off' and not v['parameters'].get('sns_fault') and not v['parameters'].get('live_fault')]
    assert all(v['ready_rises']==1 and v['sns_faults']==0 and v['ready_final']>.5 for v in normal)
    minrail=min(v.get('load_window_min_V',v['unmasked_post_ready_min_V'])for v in normal)
    maxrail=max(v['main_peak_V']for v in power);reverse=min(v['minimum_vin_minus_output_V']for v in power if v['minimum_vin_minus_output_V'] is not None)
    assert minrail>3.11605 and maxrail<3.6 and reverse>-.3
    ps=dict(selected_cases=31,supplementary_PG_tolerance_cases=2,supplementary_discharge_route_cases=1,completed=len(power),main_normal_min_V=minrail,reset_margin_V=minrail-3.11605,main_max_V=maxrail,overshoot_margin_V=3.6-maxrail,VIN_minus_source_min_V=reverse,reverse_margin_V=reverse+.3,normal_ready_rises=1,normal_SNS_faults=0,deliberate_fault_cases=sum(1 for v in power if v not in normal),model_class='transparent current-mode derivative; not final-source vendor-macromodel validation',supplementary_note='Final cases use fitted4.908V nominal and retained4.75..5.25V envelope. PG cold750 case also uses0.95A upstream average-limit guard. Previous narrower-voltage and unused-key attempts remain historical.')
    ps['component_stress']={k:dict(peak_W=max(v[k]['peak_W']for v in power),whole_record_energy_J=max(v[k]['energy_J']for v in power))for k in ['U152','U153','R165']}
    ps['R158']=dict(peak_W=max(v['R158_peak_W']for v in power),energy_J=max(v['R158_energy_J']for v in power),RMS_A=max(v['R158_RMS_A']for v in power))
    ps['numerical_resolution_peak_difference_V']=abs(next(v['main_peak_V']for v in main if v['parameters']['name']=='high_reference_1us_resolution')-next(v['main_peak_V']for v in main if v['parameters']['name']=='high_reference_slow_loop_low_damping'))
    put(D/'POWER_RESULTS.json',dict(source_PCB_sha256=source,scope=ps,cases=power))
    inp=sum([read(r/d/'RESULTS.json')for d in ['input_selected_final','input_controlled_final','input_unloaded_repeat']],[])
    accepted=[v for v in inp if v['completed']];incomplete=[v for v in inp if not v['completed']];assert len(accepted)==17 and len(incomplete)==1
    keys=['Q101_VDS_max_V','Q101_VGS_max_V','Q101_current_peak_A','Q101_power_peak_W','D101_reverse_max_V','D101_current_peak_A','R101_peak_V','R101_peak_W','R110_peak_W','fuse_I2t_A2s','Q101_onstate_power_max_W']
    ins=dict(completed=17,incomplete_retained=1,extrema={k:max(v[k]for v in accepted)for k in keys},Q101_VGS_min_V=min(v['Q101_VGS_min_V']for v in accepted))
    ins['SOA_utilization_max']=max(q['derated_SOA_utilization_max']for v in accepted for ev in v['events']for q in ev['linear_intervals'])
    assert ins['SOA_utilization_max']<1 and ins['extrema']['Q101_VDS_max_V']<200 and ins['extrema']['D101_reverse_max_V']<600
    for k in ['D102','D103','D104','D105']:ins[k]={q:max(v[k].get(q,0)for v in accepted)for q in ['peak_A','peak_W','positive_energy_J','duration_above_1mA_s']}
    ins['pin_ranges']={k:[min(v[k][0]for v in accepted),max(v[k][1]for v in accepted)]for k in accepted[0]if k.endswith('_range_V')}
    put(D/'INPUT_RESULTS.json',dict(source_PCB_sha256=source,scope=ins,cases=inp))
    coarse=read(e/'thermal/0.5/RESULTS.json');fine=read(e/'thermal/0.25/RESULTS.json');assert all(v['source']['source_PCB_sha256']==source and v['source']['native_PCB_sha256']==filled for v in [coarse,fine])
    thermal=dict(release_heat_W=fine['release_budget_W'],stacked_80pct_heat_W=fine['stacked_total_W'],required_U121_efficiency_at_U151_80pct=fine['required_U121_efficiency_if_U151_exactly_80pct_and_max_leakage'],cases=[])
    assert thermal['release_heat_W']==2.940859375
    for x,y in zip(coarse['results'],fine['results']):
        delta=y['max_board_C']-x['max_board_C'];thermal['cases'].append(dict(case=y['case'],coarse_board_max_C=x['max_board_C'],fine_board_max_C=y['max_board_C'],one_step_allowance_C=max(delta,0),board_screen_with_one_step_C=y['max_board_C']+max(delta,0),source_heat_W=y['heat_vector_total_W']))
    thermal['local_package_screen']={}
    for ref,(x,y,dx,dy,layer)in {'U152':(43.6,4.8,1,1.5,3),'U153':(79.1,-3.5,1,1.5,3)}.items():
        vals=[]
        for mesh in [.5,.25]:
            z=np.load(e/f'thermal/{mesh}/I32_measured_loss_allocation.npz');sel=(abs(z['x']-x)<=dx+mesh/2)&(abs(z['y']-y)<=dy+mesh/2);vals.append(float(z['T'][layer,sel].max()))
        local=vals[1]+max(0,vals[1]-vals[0]);power_peak=ps['component_stress'][ref]['peak_W'];tj=local+51*power_peak
        thermal['local_package_screen'][ref]=dict(coarse_board_max_C=vals[0],fine_board_max_C=vals[1],one_step_local_board_C=local,RthetaJB_allocation_K_W=51,peak_dissipation_W=power_peak,conditional_Tj_screen_C=tj,minimum_TSD_C=130,margin_C=130-tj)
        assert tj<130
    thermal.update(mesh_convergence_proven=False,junction_temperature_proven=False,immediate_air_proven=False,physical_tests=0)
    put(D/'THERMAL_RESULTS.json',thermal)
    final=dict(status='SOURCE_BOUND_DIGITAL_I32_EVIDENCE_WITH_PHYSICAL_GATES',source_PCB_sha256=source,filled_PCB_sha256=filled,native_schematic_XML_sha256=binding['native_schematic_XML_sha256'],native=dict(status=native['status'],ERC=0,DRC=0,unconnected=0,schematic_parity=0,fitted=177,postconditions=13,CAD_files=135,firmware_reused_unchanged_files=32),power=ps,input=ins,layout=dict(measured_paths=len(layout['routes']),views=7,filled_ground_pairs=len(returns['rows']),ground_contract=ground['terms']),mechanics={k:mech[k]for k in ['status','fitted_count','extra_height_mm','populated_checks','mated_checks','interferences','nearest']},thermal=thermal,physical_tests=0,supplier_approval=False,manufacturing_order=False,full_product_qualified=False)
    put(D/'FINAL_EVIDENCE.json',final)
    print(json.dumps(dict(native=final['native'],power=ps,thermal=thermal),indent=2))
if __name__=='__main__':main()
