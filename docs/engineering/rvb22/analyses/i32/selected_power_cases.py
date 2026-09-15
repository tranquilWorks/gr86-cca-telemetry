#!/usr/bin/env python3
"""Declared sensitivities for the physically fitted controlled reservoir circuit."""
from pathlib import Path
import json
D=Path(__file__).resolve().parent
BASE=dict(bulk=680,damp=.30,top=11300,fb_target=11800,fb_bottom_target=5050,
 bleed=1000,physical_dividers=True,physical_input_caps=True,input_cap_count=1,
 sns_top=6340,sns_bottom=1000,iso_en_top=4700,iso_en_bottom=1000,
 bulk_en_top=3010,bulk_en_bottom=1000,
 input_leak=.0094,bulk_leak=.008568,bulk_switch=True,bulk_bleed=1000,
 slew=.01157,bulk_slew=.01157,bulk_ron=.06,ron=.04,
 en_cap=220e-9,actual_en_cap=20e-12,enable_divider=True,pg_pullup=47000,active_discharge=True,
 q153_threshold=2.5,q152_threshold=2.5,r164=4700,r165=4.7,
 input_route_R=.06,input_route_L=300e-9,branch_R=.11,branch_L=200e-9,
 main_feed_R=.075,main_feed_L=300e-9,reset_fall=3.11605,
 reset_hys=3.11605*.025,reset_delay=.18,off_delay=250e-6,
 inductor_DCR_scale=1.49125,stop=.6,load_start=.45)
LOW=dict(slow=True,mode='load',release_zero=True,L151_scale=1.2,L121_scale=.8,
 vref=.9844,fb_top_scale=.9986,fb_bottom_scale=1.0014,ceramic=.5,
 bulk_scale=.448,bulk_local_cap_scale=.5,esr=.1,damp=.318,bulk_bleed=940)
HIGH=dict(LOW,vref=1.0156,fb_top_scale=1.0014,fb_bottom_scale=.9986,esr=.001,damp=.282,bulk_ron=.001,bulk_bleed=1060)
COLD=dict(constant=.75,input_poly_scale=.448,input_poly_esr=.1,cin_scale=.5,
 ceramic5=.5,bulk_scale=2.106,ceramic=1.265,tss=.001,tdelay151=0,
 vref=1.0156,ipos=2.4,ipos121=.95,ineg=1.49,rail5_dc=4.91,
 en_cap=110e-9,en_rise=1.425,en_top_scale=.94,en_bottom_scale=1.06,
 iso_en_rise=.75,iso_en_fall=.64,iso_en_top_scale=1.0014,iso_en_bottom_scale=.9986,
 sns_rise=.565,sns_fall=.5,sns_top_scale=1.0014,sns_bottom_scale=.9986,
 fb_top_scale=1.0014,fb_bottom_scale=.9986,q_ron=.001,
 slew=.00876628,bulk_slew=.00876628,bulk_en_rise=.75,bulk_en_fall=.64,
 bulk_en_top_scale=1.0014,bulk_en_bottom_scale=.9986)
OFF=dict(mode='off',no_off_load=True,off_start=.45,reapply=.85,stop=1.3,
 input_poly_scale=.448,input_poly_esr=.1,cin_scale=.5,ceramic5=.5,
 bulk_scale=2.106,ceramic=1.265,vref=1.0156,ineg=1.49,rail5_dc=4.91,
 en_cap=278.3e-9,en_fall=.9,en_top_scale=1.06,en_bottom_scale=.94,
 iso_en_rise=.65,iso_en_fall=.56,iso_en_top_scale=.9986,iso_en_bottom_scale=1.0014,iso_en_leak=-.1e-6,
 sns_rise=.465,sns_fall=.41,sns_top_scale=.9986,sns_bottom_scale=1.0014,sns_leak=-.1e-6,
 slew=.01461858,bulk_slew=.01461858,bulk_bleed=1060,
 bulk_en_rise=.65,bulk_en_fall=.56,bulk_en_top_scale=.9986,bulk_en_bottom_scale=1.0014,bulk_en_leak=-.1e-6)
def cases():
 out=[]
 def add(name,**kw):out.append(dict(BASE,**dict(kw,name=name)))
 add('nominal_hot_leakage')
 add('low_reference_slow_loop_aged_damping',**LOW)
 add('high_reference_slow_loop_low_damping',**HIGH)
 add('cold750_max_main_storage_min_upstream_limit',**COLD)
 add('cold750_min_U151_limit',**dict(COLD,ipos=1.5,tss=.0022))
 add('cold450_max_storage',**dict(COLD,constant=.45))
 add('cold750_all_storage_max',**dict(COLD,input_poly_scale=2.106))
 add('slowest_charging_earliest_boot',**dict(LOW,bulk_scale=2.106,input_poly_scale=2.106,ceramic=1.265,slew=.01461858,bulk_slew=.01461858))
 add('maximum_reset_delay',reset_delay=.42,stop=.75)
 add('minimum_reset_threshold',reset_fall=3.02395,reset_hys=.01535,mode='load')
 add('minimum_inductance_saturation_guard',**dict(HIGH,L151_scale=.64,L121_scale=.64))
 add('maximum_inductance_low_reference',**dict(LOW,L151_scale=1.2,L121_scale=1.2))
 add('nominal_loop_load_release',mode='load',release_zero=True)
 add('maximum_main_capacitance_load_release',mode='load',release_zero=True,bulk_scale=2.106,ceramic=1.265)
 for voltage in [4.91,5.09]:
  for ron in [.001,.04]:
   add(f'off_restart_5V{voltage}_Ron{ron}',**dict(OFF,rail5_dc=voltage,ron=ron,q_ron=.001,r165=4.7*.94))
 add('off_restart_slow_discharge',**dict(OFF,q_ron=.3,r165=4.7*1.06,r164=4700*.94,q153_threshold=1.0))
 add('off_restart_minimum_bulk',**dict(OFF,bulk_scale=.448))
 add('off_restart_maximum_reset_delay',**dict(OFF,reset_delay=.42,stop=1.6))
 add('SNS_falling_restart',sns_fault=True,fault_start=.45,stop=.9)
 add('SNS_falling_restart_stored_corner',**dict(OFF,mode='custom',sns_fault=True,fault_start=.45,stop=.9))
 add('external5_R128_open',external5=True,battery_pwl='0 0 .6 0')
 add('external3_R153_open',service3=True,battery_pwl='0 0 .6 0')
 add('live_crank_6V',**dict(OFF,mode='custom',live_fault=True,fault_start=.45,stop=1.3,battery_pwl='0 0 .001 0 .002 12 .45 12 .4501 6 .65 6 .651 12'))
 add('live_overvoltage_24V',**dict(OFF,mode='custom',live_fault=True,fault_start=.45,stop=1.3,battery_pwl='0 0 .001 0 .002 12 .45 12 .451 24 .65 24 .651 12'))
 add('slow_supply_collapse',**dict(OFF,mode='custom',live_fault=True,fault_start=.45,stop=1.4,battery_pwl='0 0 .001 0 .002 12 .45 12 .55 0 .85 0 .851 12'))
 add('rapid_reapplication_10ms',**dict(OFF,reapply=.4601,stop=1.0))
 add('rapid_reapplication_100ms',**dict(OFF,reapply=.5501,stop=1.1))
 add('high_reference_1us_resolution',**dict(HIGH,max_step=1e-6))
 for case in out:
  old=case["bulk_slew"]
  case["bulk_slew"]=(.35*68000*.947+20)*.8e-6 if old==.00876628 else (.35*68000*1.053+20)*1.2e-6 if old==.01461858 else (.35*68000+20)*1e-6
  case["bulk_CT_basis"]="C166 CGA5L1C0G2A683J160AE68nF C0G: tolerance+temperature0.947..1.053; IC timing allocation0.8..1.2; (.35*CT_pF+20)us/V. Physical correlation required."
  case['rail5_dc']=4.75 if case.get('rail5_dc')==4.91 else 5.25 if case.get('rail5_dc')==5.09 else 4.908
  case['upstream_voltage_basis']='Fitted1.2V*(1+309k/100k)=4.908V nominal. Retained interface4.75..5.25V includes reference/divider/ripple allowance; explicit off cases use endpoints.'
  if case['name']in ['low_reference_slow_loop_aged_damping','cold750_max_main_storage_min_upstream_limit','cold750_min_U151_limit','cold750_all_storage_max','slowest_charging_earliest_boot']:case['rail5_dc']=4.75
  if case['name']in ['high_reference_slow_loop_low_damping','high_reference_1us_resolution','minimum_inductance_saturation_guard','maximum_main_capacitance_load_release']:case['rail5_dc']=5.25
  case['name']=case['name'].replace('5V4.91','5V4.75').replace('5V5.09','5V5.25')
 return out
if __name__=='__main__':
 p=cases();(D/'SELECTED_POWER_CASES.json').write_text(json.dumps(p,indent=2)+'\n');print(len(p),'declared cases')
