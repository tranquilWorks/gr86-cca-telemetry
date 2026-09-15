#!/usr/bin/env python3
"""Source-bound explicit conductor paths. No zone, field-solver or silicon credit.

Pads/vias are conductive regions; track distances are measured along the actual
saved centerlines between intersections with those regions. A zero-length pad
edge means contact with that copper region, not a zero-inductance connection.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import networkx as nx
import numpy as np
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points, unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'convergence_01/support'))
import check_combined_copper as c

PAIRS=[
 ('U121 input bypass VIN','C123.1','U121.2'),
 ('U121 input bypass ground','C123.2','U121.1'),
 ('U121 input bypass exposed pad','C123.2','U121.9'),
 ('U121 bootstrap BST','C124.1','U121.7'),
 ('U121 bootstrap SW','C124.2','U121.8'),
 ('U121 switch to inductor','U121.8','L121.1'),
 ('U121 inductor to output cap','L121.2','C127.1'),
 ('U121 output cap return','C127.2','U121.1'),
 ('U121 FB upper','R122.2','U121.5'),
 ('U121 FB lower','R123.1','U121.5'),
 ('U121 FB ground','R123.2','U121.1'),
 ('U151 input bypass VIN13','C152.1','U151.13'),
 ('U151 input bypass VIN12','C152.1','U151.12'),
 ('U151 input bypass PGND15','C152.2','U151.15'),
 ('U151 input bypass PGND16','C152.2','U151.16'),
 ('U151 input bypass exposed pad','C152.2','U151.17'),
 ('U151 bulk input feed','C151.1','U151.13'),
 ('U151 VCC','C153.1','U151.4'),
 ('U151 VCC ground','C153.2','U151.10'),
 ('U151 bootstrap BOOT','C154.1','U151.3'),
 ('U151 bootstrap SW','C154.2','U151.1'),
 ('U151 switch to inductor','U151.1','L151.1'),
 ('U151 inductor to first cap','L151.2','C155.1'),
 ('U151 inductor to last cap','L151.2','C157.1'),
 ('U151 cap ground to PGND','C155.2','U151.16'),
 ('U151 cap ground to EP','C157.2','U151.17'),
 ('U151 source sense','C157.1','R155.1'),
 ('U151 FB upper','R155.2','U151.9'),
 ('U151 FB lower','R156.1','U151.9'),
 ('U151 quiet feedback return','R156.2','U151.10'),
 ('R153 power input','C157.1','R153.1'),
 ('R153 source test point','R153.1','TP151.1'),
 ('R153 output test point','R153.2','TP203.1'),
 ('Main feed to U201','R153.2','U201.2'),
 ('Main load to C206 charger','U201.2','U153.1'),
 ('Main load to C201','U201.2','C201.1'),
 ('Main load to C204','U201.2','C204.1'),
 ('U152 service feed','R151.2','U152.1'),
 ('U152 local bypass feed','C161.1','U152.1'),
 ('U152 local bypass ground','C161.2','U152.5'),
 ('U152 ground to exposed pad','U152.5','U152.11'),
 ('U152 output to U151 input','U152.10','C151.1'),
 ('C162 reservoir to U151','C162.1','C151.1'),
 ('C162 reservoir ground','C162.2','U151.17'),
 ('U152 SNS pin to divider','U152.8','R160.2'),
 ('U152 CT pin to capacitor','U152.6','C159.1'),
 ('U152 PG to enable divider','U152.7','R166.1'),
 ('U151 actual enable','R166.2','U151.11'),
 ('Q153 remote enable','U152.7','Q153.1'),
 ('U152 timing return','C159.2','U152.11'),
 ('U153 input bypass','C167.1','U153.1'),
 ('U153 input bypass return','C167.2','U153.11'),
 ('U153 timing capacitor','U153.6','C166.1'),
 ('U153 timing return','C166.2','U153.11'),
 ('U153 ground to EP','U153.5','U153.11'),
 ('U153 reservoir switch output','U153.10','R158.1'),
 ('U153 SNS local','U153.8','C167.1'),
 ('U153 enable','R169.2','U153.4'),
 ('Reservoir bleed','R168.1','C206.1'),
 ('Reservoir bleed return','R168.2','U153.11'),
 ('Bulk enable divider return','R170.2','U153.11'),
 ('U202 reset delay supply','R204.1','U202.5'),
 ('U202 reset delay CT','R204.2','U202.4'),
 ('Q152 drain feed','R165.2','Q152.3'),
 ('R165 source-discharge feed','C157.1','R165.1'),
 ('R164 discharge gate supply','C151.1','R164.1'),
 ('C206 local damping branch','R158.2','C206.1'),
 ('C206 charger main feed','R153.2','U153.1'),
 ('D105 raw clamp feed','D101.1','D105.1'),
 ('D105 return to input controller','D105.2','U101.4'),
 ('Input drain feed','D101.1','Q101.2'),
 ('Input controller gate','U101.8','R106.1'),
 ('Input gate stopper','R106.2','Q101.1'),
 ('Input gate clamp','D104.1','Q101.1'),
 ('Input gate clamp source','D104.2','Q101.3'),
 ('Input output clamp','Q101.3','D103.1'),
 ('Input controller sense','Q101.3','U101.7'),
 ('Input clamp controller return','D103.2','U101.4'),
 ('Input controller VIN bypass','C101.1','U101.1'),
 ('Input controller bypass return','C101.2','U101.4'),
]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pcb',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--no-views',action='store_true',help='Compute measurements without optional plot rendering');a=ap.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 b,items,unsupported=c.collect(a.pcb);assert not unsupported,unsupported
 names={x[1]:x[2] for x in c.child(b,'net')}
 pads={x['id'].split('@')[0]:x for x in items if x['type']=='pad'}
 fps={c.prop(f)['Reference']:f for f in c.child(b,'footprint')}
 segments=[]
 for s in c.child(b,'segment'):
  segments.append(dict(id=c.get(s,'uuid')[0],net=c.get(s,'net')[0],layer=c.get(s,'layer')[0],width=c.get(s,'width')[0],line=LineString([c.get(s,'start'),c.get(s,'end')])))
 graphs={}
 def graph(net):
  if net in graphs:return graphs[net]
  g=nx.Graph();ss=[s for s in segments if s['net']==net];regions=[i for i in items if i['net']==net and i['type']!='segment']
  def node(layer,p):return (layer,round(p[0],7),round(p[1],7))
  cuts={s['id']:[0,s['line'].length] for s in ss}
  joins=[]
  for j,s in enumerate(ss):
   ln=s['line'];key=s['id']
   for q in ss[j+1:]:
    if q['layer']!=s['layer']:continue
    inter=ln.intersection(q['line'])
    if inter.is_empty:continue
    pp=[inter] if inter.geom_type=='Point' else list(inter.geoms) if inter.geom_type=='MultiPoint' else [Point(inter.bounds[:2]),Point(inter.bounds[2:])]
    for p in pp:cuts[key].append(ln.project(p));cuts[q['id']].append(q['line'].project(p))
   for r in regions:
    if r['layer']!=s['layer']:continue
    inter=ln.intersection(r['geometry'].buffer(1e-7))
    if inter.is_empty:
     # Copper can touch with off-center overlap. Preserve the transverse link.
     if ln.distance(r['geometry'])>s['width']/2+1e-7:continue
     p,q=nearest_points(ln,r['geometry']);dist=ln.project(p);cuts[key].append(dist)
     joins.append((node(s['layer'],p.coords[0]),r,p.distance(q)))
    else:
     geom=[inter] if not hasattr(inter,'geoms') else list(inter.geoms)
     for part in geom:
      pts=[part]if part.geom_type=='Point'else[Point(part.coords[0]),Point(part.coords[-1])]
      for p in pts:
       dist=ln.project(p);cuts[key].append(dist);joins.append((node(s['layer'],p.coords[0]),r,0))
  for s in ss:
   dd=sorted(set(round(d,8)for d in cuts[s['id']]))
   for d,e in zip(dd,dd[1:]):
    p=s['line'].interpolate(d);q=s['line'].interpolate(e)
    if e-d>1e-8:g.add_edge(node(s['layer'],p.coords[0]),node(s['layer'],q.coords[0]),weight=e-d,width=s['width'],kind='track',uuid=s['id'],layer=s['layer'])
  for n,r,d in joins:g.add_edge(n,('region',r['id'],r['layer']),weight=d,kind=r['type'],uuid=r.get('bridge')or r['id'],layer=r['layer'])
  for i,r in enumerate(regions):
   rn=('region',r['id'],r['layer']);g.add_node(rn)
   for q in regions[i+1:]:
    if (r['layer']==q['layer']and r['geometry'].distance(q['geometry'])<2e-7)or(r['bridge']and r['bridge']==q['bridge']):
     g.add_edge(rn,('region',q['id'],q['layer']),weight=0,kind='via'if r['bridge']else'pad',uuid=r.get('bridge')or r['id'],layer=r['layer'])
  graphs[net]=g;return g
 rows=[]
 for label,pa,pb in PAIRS:
  row=dict(path=label,start=pa,end=pb)
  if pa not in pads or pb not in pads:row['status']='PAD_NOT_PRESENT';rows.append(row);continue
  p,q=pads[pa],pads[pb];row.update(net=names.get(p['net']),start_xy_mm=list(p['geometry'].centroid.coords[0]),end_xy_mm=list(q['geometry'].centroid.coords[0]),pad_edge_gap_mm=p['geometry'].distance(q['geometry']))
  if p['net']!=q['net']:row['status']='DIFFERENT_NETS';rows.append(row);continue
  g=graph(p['net']);start=('region',p['id'],p['layer']);end=('region',q['id'],q['layer'])
  try:
   path=nx.shortest_path(g,start,end,weight='weight');ee=[g.edges[u,v]for u,v in zip(path,path[1:])];tracks=[x for x in ee if x['kind']=='track']
   row.update(status='EXPLICIT_ROUTE',route_centerline_outside_pads_mm=sum(x['weight']for x in ee),minimum_track_width_mm=min([x['width']for x in tracks],default=None),layers=sorted(set(x['layer']for x in ee)),via_ids=sorted(set(x['uuid']for x in ee if x['kind']=='via')),track_ids=sorted(set(x['uuid']for x in tracks)),path_nodes=[list(x)for x in path])
   row['track_R_150C_ohm']=sum(1.724e-8*(1+.00393*130)*(e['weight']/1000)/((e['width']-.06)/1000*((50 if e['layer']in ['F.Cu','B.Cu']else 24)*1e-6))for e in tracks)
  except nx.NetworkXNoPath:row['status']='ZONE_RETURN_REQUIRED_OR_EXPLICIT_DISCONTINUITY'
  rows.append(row)
 switch=[]
 for name in ['5V_SW','3V3_SW']:
  ids=[n for n,v in names.items()if v==name]
  if not ids:continue
  nn=ids[0]
  for layer in c.L:
   ge=[i['geometry']for i in items if i['net']==nn and i['layer']==layer]
   if not ge:continue
   sw=unary_union(ge);sensitive=[i for i in items if i['layer']==layer and any(k in names.get(i['net'],'')for k in ['FB','RESET','PPS','OIL_ADC','GPS_UART'])]
   near=sorted([dict(net=names[i['net']],item=i['id'],gap_mm=sw.distance(i['geometry']))for i in sensitive],key=lambda x:x['gap_mm'])[:6]
   switch.append(dict(net=name,layer=layer,explicit_area_mm2=sw.area,nearest_sensitive=near))
 out=dict(source_PCB_sha256=hashlib.sha256(a.pcb.read_bytes()).hexdigest(),scope=__doc__,routes=rows,switch_copper=switch,pad_count=len(pads),segment_count=len(segments))
 (a.output/'LAYOUT_MEASUREMENTS.json').write_text(json.dumps(out,indent=2)+'\n')
 if a.no_views:
  print(json.dumps(dict(source_PCB_sha256=out['source_PCB_sha256'],measured_paths=len(rows),views_generated=0)))
  return
 for title,bounds,layers in [('U152',(14,54,-11,14),['F.Cu','B.Cu']),('Reservoir_tab',(72,90,-10,6),['F.Cu','B.Cu']),('Discharge',(23,53,39,51),['F.Cu','In2.Cu']),('U151',(22,49,8,29),['B.Cu','In1.Cu']),('U121',(35,69,19,41),['F.Cu','In1.Cu']),('Input',(21,48,22,47),['F.Cu','B.Cu']),('Reset_delay',(69,82,2,15),['B.Cu','In2.Cu'])]:
  fig,axes=plt.subplots(1,2,figsize=(15,8),layout='constrained')
  colors={'GND':'#92adb5','5V_SW':'#e49324','3V3_SW':'#e49324','5V_FB':'#cf4d9c','3V3_FB':'#cf4d9c','3V3_FB_ADJ':'#cf4d9c','3V3_ENABLE':'#5c36a3','3V3_ISO_SNS':'#da4398','3V3_ISO_IN':'#ce922b','3V3_DISCHARGE_GATE':'#da4398','3V3_VIN':'#d34b47','5V_VIN':'#d34b47','3V3_SOURCE':'#3189bf','5V_SOURCE':'#3189bf','INPUT_GATE':'#765ba0','PROTECTED_12V':'#3189bf','REV_BLOCKED_12V':'#d34b47'}
  for ax,layer in zip(axes,layers):
   for it in items:
    if it['layer']!=layer:continue
    g=it['geometry'];x,y=g.centroid.coords[0]
    if not(bounds[0]-3<x<bounds[1]+3 and bounds[2]-3<y<bounds[3]+3):continue
    net=names.get(it['net'],'');color=colors.get(net,'#c8c8c8')
    gg=[g]if g.geom_type=='Polygon'else list(g.geoms)
    for z in gg:ax.add_patch(Patch(np.asarray(z.exterior.coords),facecolor=color,edgecolor='none',alpha=.85 if net in colors else .4))
   for ref,f in fps.items():
    at=c.get(f,'at');side=c.get(f,'layer')[0]
    if side==layer and bounds[0]<at[0]<bounds[1]and bounds[2]<at[1]<bounds[3]:ax.text(at[0],at[1],ref,fontsize=7,ha='center',va='center',bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=.5))
   ax.set(xlim=bounds[:2],ylim=bounds[2:][::-1],xlabel='Board X (mm)',ylabel='Board Y (mm)',title=layer+' — source coordinate view')
   ax.set_aspect('equal');ax.grid(alpha=.15)
  prefix={'Reservoir_tab':'U153','Discharge':'Q152','Reset_delay':'U202'}.get(title,title)
  for ax,layer in zip(axes,layers):
   notes=[r for r in rows if r['status']=='EXPLICIT_ROUTE' and r['path'].startswith(prefix) and layer in r['layers'] and bounds[0]<r['start_xy_mm'][0]<bounds[1] and bounds[2]<r['start_xy_mm'][1]<bounds[3]]
   if not notes:continue
   r0=notes[0];xx,yy=r0['start_xy_mm']
   ax.annotate(f"{r0['path']}\n{r0['route_centerline_outside_pads_mm']:.2f} mm; min {r0['minimum_track_width_mm']} mm",xy=(xx,yy),xycoords='data',xytext=(.02,.03),textcoords='axes fraction',fontsize=8,bbox=dict(boxstyle='round',fc='white',alpha=.95),arrowprops=dict(arrowstyle='->',color='black'))
  fig.suptitle(f'{title} power copper | {out["source_PCB_sha256"][:16]}\nExplicit pads/tracks/vias; ground-plane fill is verified separately',fontsize=12)
  fig.savefig(a.output/(title+'_power_routes.png'),dpi=190);plt.close(fig)
 print(json.dumps({k:v for k,v in out.items()if k not in ['routes','scope','switch_copper']}));print('\n'.join(f'{r["path"]}: {r["status"]} {r.get("route_centerline_outside_pads_mm",0):.4f} mm'for r in rows))

if __name__=='__main__':main()
