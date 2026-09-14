#!/usr/bin/env python3
"""I32 actual-filled-copper screen; adopted C05/W02/T03, never a junction model."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
from shapely.geometry import box
D=Path(__file__).resolve().parent
sys.path[:0]=[str(D.parent/'convergence_01'),str(D.parent/'convergence_02')]
import thermal_native as tn
import board_matrix as bm
from shared_network import solve_network

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--native-dir',type=Path,required=True);ap.add_argument('--source-pcb',type=Path,required=True);ap.add_argument('--source-hash',required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--mesh',type=float,required=True)
 a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 nr=json.loads((a.native_dir/'RESULT.json').read_text());assert nr['native_report_finding_count']==0 and all(v['pass']for v in nr['output_postconditions'].values())
 assert nr['inputs']['cad']['GR86_CCA_RevB.kicad_pcb']==a.source_hash
 ex,b=tn.extract_native(a.native_dir/'candidate_kicad/GR86_CCA_RevB.kicad_pcb',source_pcb=a.source_pcb,expected_source_hash=a.source_hash)
 profile=json.loads((D.parent/'convergence_04/RELEASE_POWER_PROFILE.json').read_text())
 names={'U201':'u201_heat_allocation_W','U151':'u151_loss_allocation_W','U121':'u121_heat_allocation_W','U403':'gps_5v_allocation_W','U401':'oil_5v_allocation_W','other5V_allocation':'other_5v_allocation_W'}
 old=[(n,profile[names[n]],g)for n,_,g in tn.model.heat]
 # TNPU H/W: .02% initial +2ppm/K x100K +.1% 8000h qualification
 # envelope. Full-temperature U151 reference bound; not an unlimited life claim.
 vmax=1.0156*(1+11800*1.0014/(5050*.9986));pload=.45*vmax
 # Source-local heat regions from the final footprint positions. Conversion
 # efficiency includes each converter's inductor loss, so do not count it twice.
 fps={tn.c.prop(f)['Reference']:f for f in tn.c.child(b,'footprint')}
 def region(ref,dx=.85,dy=.5):
  x,y,*_=tn.c.get(fps[ref],'at');return box(x-dx,y-dy,x+dx,y+dy)
 newparts=[('C162',.0094*5.25,region('C162',3.65,2.15)),
           ('C206',.008568*vmax,region('C206',3.65,2.15)),
           ('U152',.012,region('U152',1,1.5)),
           ('U153',.001,region('U153',1,1.5)),
           ('R168',vmax*vmax/940,region('R168')),
           ('R169',vmax*vmax/4004.386*3010/4010,region('R169')),
           ('R170',vmax*vmax/4004.386*1000/4010,region('R170')),
           ('R164',.006,region('R164')),
           ('R160',5.25**2/7329.724*6340/7340,region('R160')),
           ('R161',5.25**2/7329.724*1000/7340,region('R161')),
           ('R162',5.25**2/5692.02*4700/5700,region('R162')),
           ('R163',5.25**2/5692.02*1000/5700,region('R163')),
           ('other_sequence_loss',.003,region('R159'))]
 extra=sum(p for _,p,_ in newparts)
 p151=pload*(1/.8-1);burden=pload+p151+.396+extra;p121=burden*(1/.8-1)+.025
 powers=dict(U201=pload,U151=p151,U121=p121)
 stacked=[(n,powers.get(n,p),g)for n,p,g in old]+newparts
 total=sum(p for _,p,_ in stacked);budget=profile['release_total_heat_allocation_W']
 # Measured-loss alternative holds exactly the adopted total. Reduce only the
 # upstream conversion allocation, never scale unrelated heat or silently raise
 # the release budget. Required U121 efficiency is derived, not claimed measured.
 delta=total-budget;measured=[(n,p-delta if n=='U121'else p,g)for n,p,g in stacked]
 required_eff=burden/(burden+p121-delta-.025)
 cases=[('retained_I25_vector_on_I32_copper',old),('I32_measured_loss_allocation',measured),('I32_stacked_80pct_sensitivity',stacked)]
 assert abs(sum(p for _,p,_ in old)-budget)<1e-9 and abs(sum(p for _,p,_ in measured)-budget)<1e-9
 contacts=json.loads((D.parent/'convergence_02/CONTACT_PROPOSALS.json').read_text())['baseline_contacts']
 tn.model.heat=old
 for n in ('G','board','carrier','heat'):setattr(bm,n,getattr(tn.model,n))
 m=bm.prepare(ex,step=a.mesh,mode='provisional',plating_um=15.)
 # New heat sources must use their actual board side as well as actual XY.
 for ref,_,_ in newparts:
  owner='R159' if ref=='other_sequence_loss' else ref
  m['source_layers'][ref]=3 if tn.c.get(fps[owner],'layer')[0]=='B.Cu' else 0
 results=[]
 for name,heat in cases:
  m['heat']=heat;m['q']=np.zeros(4*m['N'])
  for ref,power,geom in heat:
   weights=m['overlap'](geom);assert sum(weights)>0;l=m['source_layers'].get(ref,0)
   m['q'][l*m['N']:(l+1)*m['N']]+=power*weights/sum(weights)
  r=solve_network(m,contacts,sink_R=1.,save_map=a.output/(name+'.npz'))
  r.update(source_layers={n:m['source_layers'].get(n,0) for n,_,_ in heat},case=name,source_heat_vector_W={n:p for n,p,_ in heat},heat_vector_total_W=sum(p for _,p,_ in heat));results.append(r)
  (a.output/(name+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(name,r['max_board_C'],flush=True)
 out=dict(source=ex[-1],results=results,profile=profile,steady_voltage_bound_V=vmax,stacked_total_W=total,release_budget_W=budget,required_U121_efficiency_if_U151_exactly_80pct_and_max_leakage=required_eff,additional_loss_allocation_W=extra,source_regions='Inherited component/source-pad regions plus actual new footprint body regions; U201 source region is silicon/EP within module, not whole module body.',adopted_cooling_only=True,physical_test=False,package_temperature_proven=False,scope=__doc__)
 (a.output/'RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
