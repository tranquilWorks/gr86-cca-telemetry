#!/usr/bin/env python3
"""Independent connectivity of actual filled ground islands and physical bridges."""
from pathlib import Path
import argparse,hashlib,json,sys
import shapely as sh
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
import networkx as nx
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import layout_audit as la
c=la.c

def parts(g):
 if g.geom_type=='Polygon':return [g]
 return [p for a in getattr(g,'geoms',[])for p in parts(a)]
def patch(g,**kw):
 g=orient(g,1);vs=[];cs=[]
 for ring in [g.exterior,*g.interiors]:
  v=list(ring.coords);vs+=v;cs += [MPath.MOVETO]+[MPath.LINETO]*(len(v)-2)+[MPath.CLOSEPOLY]
 return PathPatch(MPath(np.asarray(vs),cs),**kw)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pcb',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 b,it,u=c.collect(a.pcb);assert not u;gn=next(x[1]for x in c.child(b,'net')if x[2]=='GND')
 gg={l:[x['geometry']for x in it if x['layer']==l and x['net']==gn]for l in c.L}
 for z in c.child(b,'zone'):
  if c.get(z,'net')!=[gn]or c.child(z,'keepout'):continue
  for q in c.child(z,'filled_polygon'):
   gg[c.get(q,'layer')[0]].append(sh.make_valid(Polygon([v[1:]for v in c.child(c.child(q,'pts')[0],'xy')])))
 gg={l:parts(unary_union(v))for l,v in gg.items()};g=nx.Graph();bridges={};padnodes={}
 for l,polys in gg.items():
  for j,p in enumerate(polys):g.add_node((l,j));sh.prepare(p)
 for x in it:
  if x['net']!=gn:continue
  hits=[(x['layer'],j)for j,p in enumerate(gg[x['layer']])if p.intersects(x['geometry'])]
  if x['type']=='pad':padnodes.setdefault(x['id'].split('@')[0],[]).extend(hits)
  if x['bridge']:bridges.setdefault(x['bridge'],[]).extend(hits)
 for nodes in bridges.values():
  for n in nodes[1:]:g.add_edge(nodes[0],n)
 components={n:j for j,ns in enumerate(nx.connected_components(g))for n in ns};rows=[]
 for label,p,q in la.PAIRS:
  if p not in padnodes or q not in padnodes:continue
  ps=padnodes[p];qs=padnodes[q];ok=bool({components[n]for n in ps}&{components[n]for n in qs})
  row=dict(path=label,start=p,end=q,connected_by_actual_filled_ground=ok,start_islands=ps,end_islands=qs)
  direct=[]
  for l,j in set(ps)&set(qs):
   pi=next(x for x in it if x['id'].split('@')[0]==p and x['layer']==l);qi=next(x for x in it if x['id'].split('@')[0]==q and x['layer']==l);ln=LineString([pi['geometry'].centroid,qi['geometry'].centroid])
   if gg[l][j].buffer(1e-7).covers(ln):direct.append(dict(layer=l,pad_center_line_mm=ln.length))
  row['unobstructed_ground_lines']=direct;rows.append(row)
 assert rows and all(r['connected_by_actual_filled_ground']for r in rows)
 out=dict(filled_PCB_sha256=hashlib.sha256(a.pcb.read_bytes()).hexdigest(),ground_net=gn,layer_islands={l:len(v)for l,v in gg.items()},physical_bridges=len(bridges),rows=rows,scope='Connectivity and direct copper visibility only; no zero impedance or AC return proof. Original pads/tracks plus actual native fill. Drill bores are handled by the separate resistance solver.')
 (a.out/'FILLED_GROUND_CONNECTIVITY.json').write_text(json.dumps(out,indent=2)+'\n')
 fig,axes=plt.subplots(1,2,figsize=(15,9),layout='constrained')
 for ax,layer in zip(axes,['B.Cu','In1.Cu']):
  for p in gg[layer]:ax.add_patch(patch(p,facecolor='#d5e2e8',edgecolor='#87a3b3',linewidth=.2))
  for name,xy in [('C157 added return',(38.6,21.6)),('Original return',(37.675,24)),('U201 return',(78.819766,21.275)),('C206 return',(85.12,-6.8))]:
   ax.plot(*xy,'o',ms=4,color='#b72e49');ax.annotate(name,xy,xytext=(5,8),textcoords='offset points',fontsize=8)
  ax.set(xlim=(10,89),ylim=(51,-10),aspect='equal',title=layer+' actual filled GND',xlabel='Board X (mm)',ylabel='Board Y (mm)');ax.grid(alpha=.15)
 fig.suptitle('I32 ground connectivity | '+out['filled_PCB_sha256'][:16]);fig.savefig(a.out/'Ground_returns.png',dpi=180)
 print(len(rows),'ground paths independently connected')
if __name__=='__main__':main()
