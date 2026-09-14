#!/usr/bin/env python3
"""Deterministic, exact-clearance local routing for the authored I32 changes.

Grid search proposes paths; continuous Shapely geometry validates every path.
Native KiCad refill, DRC and parity remain independent mandatory gates.
"""
from pathlib import Path
import sys,json,math,heapq,uuid,hashlib,argparse
import numpy as np
import shapely as sh
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
W=HERE.parents[1];P=W/'candidate/cad/GR86_CCA_RevB.kicad_pcb'
sys.path.insert(0,str(HERE.parent/'convergence_01/support'))
import check_combined_copper as c
S=c.sx.Symbol
key=lambda p:tuple(round(float(t),6)for t in p)
outline=Polygon(json.loads((W/'candidate/verification/I18/CURRENT_OUTLINE_GEOMETRY.json').read_text())['outline_mm'])
protected={'PROTECTED_12V','PROTECT_CTRL_VIN','INPUT_GATE','INPUT_GATE_DRIVE','INPUT_GATE_SLEW','BUCK_FEED','5V_VIN','5V_SW','5V_BST'}
raw={'RAW_12V','FUSED_12V','REV_BLOCKED_12V'}
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'GR86-I32-route:'+s))
def dump(t):return '('+str(t[0])+'\n'+'\n'.join(c.sx.dumps(v)for v in t[1:])+'\n)\n'
def read():
 global b,items,names,nets,holes,keepouts,pads
 b,items,u=c.collect(P);assert not u
 names={q[1]:q[2]for q in c.child(b,'net')};nets={v:k for k,v in names.items()}
 pads={i['id'].split('@')[0]:i for i in items if i['type']=='pad'}
 holes=unary_union([c.pad_shape(f,p)for f in c.child(b,'footprint')for p in c.child(f,'pad')if str(p[2])=='np_thru_hole'])
 keepouts={l:[]for l in c.L}
 for parent in [b]+c.child(b,'footprint'):
  for z in c.child(parent,'zone'):
   ko=c.child(z,'keepout')
   if not ko or str((c.get(ko[0],'tracks')or [''])[0])!='not_allowed':continue
   for poly in c.child(z,'polygon'):
    g=Polygon([q[1:]for q in c.child(c.child(poly,'pts')[0],'xy')])
    for l in c.get(z,'layers')or c.get(z,'layer')or []:
     if l in keepouts:keepouts[l].append(g)
 keepouts={l:unary_union(v)for l,v in keepouts.items()}
def point(p):
 return tuple(pads[p]['geometry'].centroid.coords[0])if isinstance(p,str)else tuple(p)
def obstacles(net,layer,width):
 name=names[net]
 groups={.15:[],.25:[],.6:[]}
 for i in items:
  if i['net']==net or i['layer']!=layer:continue
  nn=names.get(i['net'],'');gap=.6 if name in raw or nn in raw else .25 if name in protected or nn in protected else .15
  if i['id'].startswith('J201.'):gap=max(gap,.508)
  groups.setdefault(gap,[]).append(i['geometry'])
 return unary_union([unary_union(gs).buffer(width/2+gap+.0001)for gap,gs in groups.items()]+[holes.buffer(width/2+.3),keepouts[layer].buffer(width/2+.001)])

def route(a,z,ob,width):
 step=.1;xs=np.round(np.arange(0,89,step),5);ys=np.round(np.arange(-9.5,51.6,step),5);X,Y=np.meshgrid(xs,ys)
 allowed=outline.buffer(-(width/2+.25));sh.prepare(allowed);sh.prepare(ob);free=sh.contains_xy(allowed,X,Y)&~sh.intersects_xy(ob,X,Y)
 def xy(q):return(float(xs[q[0]]),float(ys[q[1]]))
 def near(p):
  i=round((p[0]-xs[0])/step);j=round((p[1]-ys[0])/step);qs=[]
  for dx in range(-4,5):
   for dy in range(-4,5):
    q=i+dx,j+dy
    if 0<=q[0]<len(xs)and 0<=q[1]<len(ys)and free[q[1],q[0]]:
     line=LineString([p,xy(q)])
     if not line.intersects(ob)and allowed.covers(line):qs.append(q)
  return qs
 starts=near(a);ends=set(near(z));blocked_edges=set()
 if not starts or not ends:return None,dict(start_access=len(starts),end_access=len(ends))
 for attempt in range(8):
  cost={q:math.dist(a,xy(q))for q in starts};prev={q:None for q in starts};pq=[(v+math.dist(xy(q),z),q)for q,v in cost.items()];heapq.heapify(pq);found=None
  while pq:
   f,q=heapq.heappop(pq)
   if f>cost[q]+math.dist(xy(q),z)+1e-8:continue
   if q in ends:found=q;break
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
    nq=q[0]+dx,q[1]+dy
    if not(0<=nq[0]<len(xs)and 0<=nq[1]<len(ys))or not free[nq[1],nq[0]]or(q,nq)in blocked_edges:continue
    if dx and dy and(not free[q[1],nq[0]]or not free[nq[1],q[0]]):continue
    nc=cost[q]+step*math.hypot(dx,dy)
    if nc>=cost.get(nq,1e99)-1e-12:continue
    cost[nq]=nc;prev[nq]=q;heapq.heappush(pq,(nc+math.dist(xy(nq),z),nq))
  if found is None:return None,dict(start_access=len(starts),end_access=len(ends),visited=len(cost))
  qs=[found]
  while prev[qs[-1]]is not None:qs.append(prev[qs[-1]])
  qs.reverse();bad=[]
  for qa,qz in zip(qs,qs[1:]):
   line=LineString([xy(qa),xy(qz)])
   if line.intersects(ob)or not allowed.covers(line):bad.append((qa,qz))
  if bad:
   for qa,qz in bad:blocked_edges.update([(qa,qz),(qz,qa)])
   continue
  pts=[a]+[xy(q)for q in qs]+[z];clean=[a]
  for pt in pts[1:]:
   if math.dist(clean[-1],pt)<1e-8:continue
   if len(clean)>=2:
    aa,zz=clean[-2:]
    if abs((zz[0]-aa[0])*(pt[1]-zz[1])-(zz[1]-aa[1])*(pt[0]-zz[0]))<1e-9:clean[-1]=pt;continue
   clean.append(pt)
  # Simplify grid staircases into exact-clearance 45-degree doglegs. Every
  # accepted replacement is checked as a complete continuous line geometry.
  smooth=[clean[0]];i=0
  while i<len(clean)-1:
   accepted=None
   for j in range(len(clean)-1,i,-1):
    aa,zz=clean[i],clean[j];dx=zz[0]-aa[0];dy=zz[1]-aa[1];sx0=1 if dx>=0 else -1;sy0=1 if dy>=0 else -1
    candidates=[]
    if abs(dx)>=abs(dy):
     candidates=[(aa[0]+sx0*(abs(dx)-abs(dy)),aa[1]),(aa[0]+sx0*abs(dy),zz[1])]
    else:
     candidates=[(aa[0],aa[1]+sy0*(abs(dy)-abs(dx))),(zz[0],aa[1]+sy0*abs(dx))]
    for bend in candidates:
     pp=[aa]+([bend]if math.dist(aa,bend)>1e-8 and math.dist(bend,zz)>1e-8 else [])+[zz]
     candidate=LineString(pp)
     if not candidate.intersects(ob)and allowed.covers(candidate):accepted=(j,pp);break
    if accepted:break
   if accepted is None:accepted=(i+1,[clean[i],clean[i+1]])
   i,pp=accepted;smooth.extend(pp[1:])
  clean=smooth
  line=LineString(clean);assert not line.intersects(ob)and allowed.covers(line)
  return [key(p)for p in clean],dict(start_access=len(starts),end_access=len(ends),visited=len(cost),exact_edges_checked=len(qs)-1)
 return None,dict(failure='Exact edge retry budget exhausted')

def execute(tasks):
 report=[];read()
 for k,t in enumerate(tasks):
  ident=t['id'];net=nets[t['net']]
  if t['kind']=='via':
   if any(c.get(v,'uuid')==[uid(ident)]for v in c.child(b,'via')):continue
   a=point(t['at']);size=t.get('size',.6);drill=t.get('drill',.3)
   ob=unary_union([obstacles(net,l,size)for l in c.L])
   if Point(a).intersects(ob):raise RuntimeError('Via blocked '+ident+' '+str(a))
   # Standard through-vias remain outside all component SMD lands.
   for i in items:
    if i['type']=='pad' and Point(a).buffer(drill/2+.1).intersects(i['geometry']):raise RuntimeError('Via intersects pad '+ident+' '+i['id'])
   if not any(c.get(v,'uuid')==[uid(ident)]for v in c.child(b,'via')):
    b.append(c.sx.loads(f'(via (at {a[0]} {a[1]}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (tenting front back) (net {net}) (uuid "{uid(ident)}"))'))
   row=dict(task=t,status='VIA_PREFLIGHT_PASS')
  else:
   if any(c.get(s,'uuid')==[uid(ident+':0')]for s in c.child(b,'segment')):continue
   a,z=point(t['a']),point(t['z']);width=t['width'];layer=t['layer'];ob=obstacles(net,layer,width)
   if math.dist(a,z)<1e-6:raise ValueError('Identical route endpoints '+ident)
   path,diag=route(a,z,ob,width)
   if not path:raise RuntimeError('Route blocked '+ident+' '+str(diag))
   if LineString(path).length>3*math.dist(a,z)+15:raise RuntimeError('Nonlocal route '+ident+' '+str(path))
   for j,(aa,zz)in enumerate(zip(path,path[1:])):
    b.append(c.sx.loads(f'(segment (start {aa[0]} {aa[1]}) (end {zz[0]} {zz[1]}) (width {width}) (layer "{layer}") (net {net}) (uuid "{uid(ident+":"+str(j))}"))'))
   row=dict(task=t,status='CONTINUOUS_CLEARANCE_PREFLIGHT_PASS',path_mm=path,length_mm=LineString(path).length,diagnostics=diag)
  P.write_text(dump(b));read();report.append(row)
  rp=HERE/'ROUTING_PROGRESS.json';prior=json.loads(rp.read_text())if rp.exists()else []
  prior=[x for x in prior if x['task']['id']!=ident];rp.write_text(json.dumps(prior+[row],indent=2)+'\n')
  print(ident,row['status'],row.get('length_mm',''),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('tasks',type=Path);a=ap.parse_args();execute(json.loads(a.tasks.read_text()))
