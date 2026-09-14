#!/usr/bin/env python3
"""Recheck adopted C05/W02/T03, populated and mated envelopes on I32 CAD."""
from pathlib import Path
import argparse,copy,hashlib,json,math,sys
from shapely.geometry import box,Polygon,Point,LineString
from shapely import from_wkt
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent; W=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'convergence_01/support'))
import check_combined_copper as c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pcb',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    b,items,u=c.collect(a.pcb);assert not u
    fps={c.prop(f)['Reference']:f for f in c.child(b,'footprint')}
    old=json.loads((HERE.parent/'mated_i22/RESULTS.json').read_text())
    rows={r['ref']:copy.deepcopy(r)for r in old['body_rows']}
    heights={'U152':.8,'U153':.8,'C159':1.5,'C166':1.9,'R151':.6,'R155':.55,'R156':.55,'R158':.889,'R165':.7,'D105':2.62,'Q152':1.10,'Q153':1.10}
    parts=json.loads((HERE/'CONTROLLED_RESERVOIR_CHANGES.json').read_text())['parts']
    # Only newly fitted or physically moved I32 bodies need their old envelope
    # replaced. Metadata-only changes (including mounting-hole silk) retain the
    # exact existing supplier maximum-height model.
    changed=sorted({'U152','U153','C159','C161','C162','C165','C166','C167','D105','Q152','Q153','R151','R155','R156','R158','R159','R160','R161','R162','R163','R164','R165','R166','R167','R168','R169','R170','R204'})
    for ref in ['C163','C164']:rows.pop(ref,None)
    for ref in changed:
        f=fps[ref];x,y,*aa=c.get(f,'at');theta=math.radians(aa[0]if aa else 0);pts=[]
        for q in c.child(f,'fp_line')+c.child(f,'fp_rect'):
            if not (c.get(q,'layer')or [''])[0].endswith('CrtYd'):continue
            lo,hi=c.get(q,'start'),c.get(q,'end')
            vv=[lo,hi]if c.tag(q)=='fp_line'else[(lo[0],lo[1]),(lo[0],hi[1]),(hi[0],lo[1]),(hi[0],hi[1])]
            pts += [(x+u*math.cos(theta)+v*math.sin(theta),y-u*math.sin(theta)+v*math.cos(theta))for u,v in vv]
        assert pts,ref
        bounds=(min(q[0]for q in pts)-.3,min(q[1]for q in pts)-.3,max(q[0]for q in pts)+.3,max(q[1]for q in pts)+.3)
        if ref in ['C162','C163','C164']:bounds=(x-3.95,y-2.45,x+3.95,y+2.45)
        height=4.3 if ref in ['C162','C163','C164']else heights.get(ref,.9 if ref.startswith('C')else .55)
        rows[ref]=dict(ref=ref,side=c.get(f,'layer')[0],height_max_mm=height,courtyard_plus0p3_bounds_mm=bounds,XY_basis='Actual source courtyard plus0.30mm; polymer sourced maximum body plus0.30mm.')
    inventory=json.loads((W/'candidate/cad/FITTED_REFERENCES.json').read_text())['fitted_references'];assert set(rows)==set(inventory)
    M=W/'current/mechanics';G=json.loads((M/'COOLING_GEOMETRY.json').read_text())
    obstacles=[('C05_base',from_wkt(G['carrier_base_WKT']).buffer(.15),-9,-6),('C05_supports',unary_union([from_wkt(x['WKT']).buffer(.15)for x in json.loads((M/'C05_SUPPORT_RELIEF.json').read_text())['support_plans']]),-6,0)]
    obstacles += [(x['name'],box(*x['bounds_xy_mm']),*x['Z_mm'])for x in json.loads((M/'LANDING_CLEARANCE.json').read_text())['landings']]
    checks=[]
    def prism(ref,name,xy,z,og,oz):
        zgap=max(0,oz[0]-z[1],z[0]-oz[1]);overlap=xy.intersection(og).area*max(0,min(z[1],oz[1])-max(z[0],oz[0]))
        checks.append(dict(ref=ref,obstacle=name,overlap_mm3=overlap,clearance_mm=math.hypot(xy.distance(og),zgap)))
    for ref,r in rows.items():
        x0,y0,x1,y1=r['courtyard_plus0p3_bounds_mm'];h=r['height_max_mm']+1.71
        if r['side']=='F.Cu':
            checks.append(dict(ref=ref,obstacle='16mm_front_reservation',overlap_mm3=max(0,h-16)*(x1-x0)*(y1-y0),clearance_mm=16-h));continue
        for name,og,z0,z1 in obstacles:prism(ref,name,box(x0,y0,x1,y1),(-h,0),og,(z0,z1))
        prism(ref,'T03_full_packet_plus_bow',box(x0,-h,x1,0),(y0,y1),Polygon(G['direct_T02_foil_xz_mm']).buffer(.8,join_style=2),(12.0,28.7))
        for name,key in [('W02_upper','upper_foil_yz_mm'),('W02_lower','lower_foil_yz_mm')]:prism(ref,name,box(y0,-h,y1,0),(x0,x1),Polygon(G[key]).buffer(.8,join_style=2),(14.2,53.8))
    populated_count=len(checks)
    for e in old['envelopes']:
        for r in rows.values():
            if r['side']!=e['side']or r['ref']in e['exclude']:continue
            h=r['height_max_mm']+1.71;z=(1.6,1.6+h)if r['side']=='F.Cu'else(-h,0)
            prism(r['ref'],e['name'],box(*r['courtyard_plus0p3_bounds_mm']),z,box(*e['bounds_xy_mm']),e['z'])
    cable=LineString(old['pigtail']['centerline_mm']).buffer(1.5,quad_segs=64)
    for r in rows.values():
        if r['side']=='B.Cu'and r['ref']!='J401':prism(r['ref'],'Adafruit851_full150mm_pigtail',box(*r['courtyard_plus0p3_bounds_mm']),(-r['height_max_mm']-1.71,0),cable,(-3.6,-.6))
    probes=[]
    for f in fps.values():
        ref=c.prop(f)['Reference']
        if not ref.startswith('TP'):continue
        for p in c.child(f,'pad'):
            xy=c.pad_shape(f,p).centroid;side=c.get(f,'layer')[0];tip=xy.buffer(.25)
            hits=[r['ref']for r in rows.values()if r['side']==side and tip.intersects(box(*r['courtyard_plus0p3_bounds_mm']))]
            probes.append(dict(ref=ref,xy_mm=list(xy.coords)[0],side=side,needle_diameter_mm=.3,position_allowance_mm=.1,slender_shaft_min_mm=5,component_hits=hits,backside_access='Carrier removed'if side=='B.Cu'else'Front service'))
    hits=[x for x in checks if x['overlap_mm3']>1e-7]
    out=dict(source_PCB_sha256=hashlib.sha256(a.pcb.read_bytes()).hexdigest(),status='PASS_DECLARED_ENVELOPES'if not hits else'FINDINGS',fitted_count=len(rows),extra_height_mm=1.71,full_stack_terms_mm=dict(solder=.25,capture=.51,warp=.75,deflection=.2),populated_checks=populated_count,mated_checks=len(checks)-populated_count,interferences=hits,nearest=sorted(checks,key=lambda x:x['clearance_mm'])[:25],body_rows=list(rows.values()),all_checks=checks,probes=probes,scope='Source-bound allocated maximum envelopes. Exact supplier geometry, installed fit, fatigue and material acceptance remain physical gates. Existing connector-to-cooler geometry is unchanged; I22 frozen non-component checks remain applicable.',mechanics_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in M.iterdir()if p.is_file()})
    (a.out/'MECHANICAL.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k]for k in ['status','fitted_count','populated_checks','mated_checks','interferences','nearest']},indent=2))
    print('probe component hits',[(p['ref'],p['component_hits'])for p in probes if p['component_hits']])

if __name__=='__main__':main()
