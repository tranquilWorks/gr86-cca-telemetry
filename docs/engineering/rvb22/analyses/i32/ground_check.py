"""Conservative subset of actual In1 ground: full square cells only, no cell bridges.

DC resistance of a restricted copper subset, single contact cell per actual via.
The grid is eroded by its half diagonal, retaining only cells wholly in copper.
Omitted copper and parallel layers cannot reduce this calculated DC resistance.
Finite-volume cell-centre spreading is still a numerical approximation; two
meshes and an explicit inflation are reported, not a manufactured measurement.
"""
from pathlib import Path
import sys,json,math,hashlib,argparse
D=Path(__file__).resolve().parent;W=D.parents[1]
sys.path[:0]=[str(W/'analyses/convergence_01/support'),str(W/'analyses/convergence_01'),str(W/'control')]
from native_binding import canonicalize
import numpy as np,shapely as sh,sexpdata as sx,pyamg
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import cg
import check_combined_copper as c
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--native-dir',type=Path,required=True)
ap.add_argument('--expected-hash',required=True)
ap.add_argument('--expected-source-hash',required=True)
ap.add_argument('--baseline-pcb',type=Path,required=True)
ap.add_argument('--baseline-hash',required=True)
ap.add_argument('--output-dir',type=Path,default=D)
args=ap.parse_args();D=args.output_dir.resolve();D.mkdir(parents=True,exist_ok=True)
P=args.native_dir.resolve()/'candidate_kicad/GR86_CCA_RevB.kicad_pcb'
assert hashlib.sha256(P.read_bytes()).hexdigest()==args.expected_hash,'Filled PCB hash mismatch'
native=json.loads((args.native_dir/'RESULT.json').read_text())
assert native['inputs']['cad']['GR86_CCA_RevB.kicad_pcb']==args.expected_source_hash,'Native candidate source mismatch'
required={'refilled_copper','erc_report','drc_report','schematic_netlist','pcb_netlist','requested_gerbers','separate_drills','schematic_bom','component_positions','schematic_pdf','component_step_file','component_model_log','fitted_component_step_inventory'}
assert set(native['output_postconditions'])==required and all(x['pass']for x in native['output_postconditions'].values()) and native['native_report_finding_count']==0
baseline=args.baseline_pcb
assert hashlib.sha256(baseline.read_bytes()).hexdigest()==args.baseline_hash
b,it,u=c.collect(P);assert not u
def polygon_parts(g):
 if g.geom_type=='Polygon':return [g]
 return [q for a in getattr(g,'geoms',[])for q in polygon_parts(a)]
geoms=[]
for z in c.child(b,'zone'):
 if c.get(z,'net')!=[30] or c.child(z,'keepout'):continue
 for f in c.child(z,'filled_polygon'):
  if c.get(f,'layer')!=['In1.Cu']:continue
  raw=Polygon([p[1:]for p in c.child(c.child(f,'pts')[0],'xy')]);fixed=unary_union(polygon_parts(sh.make_valid(raw)))
  assert abs(raw.area-fixed.area)<1e-5
  geoms.append(fixed)
geoms.extend(x['geometry']for x in it if x['layer']=='In1.Cu' and x['net']==30)
holes=[]
for v in c.child(b,'via'):holes.append(Point(*c.get(v,'at')[:2]).buffer(c.get(v,'drill')[0]/2,quad_segs=32))
# PTH lands are solid in the independent pad parser. Remove every real
# footprint drill too; five GND PTH bores were omitted by the inherited I23
# solver. NPTH and foreign-net PTH exclusions are explicit rather than assumed.
footprint_holes=0
for f in c.child(b,'footprint'):
 for p in c.child(f,'pad'):
  dd=c.get(p,'drill')
  if not dd:continue
  assert len(dd)==1 and isinstance(dd[0],(int,float)),'Unsupported non-round or offset bore'
  assert str(p[2])in ['thru_hole','np_thru_hole']
  center=c.pad_shape(f,p).centroid
  holes.append(center.buffer(dd[0]/2,quad_segs=32));footprint_holes+=1
raw_ground=unary_union(geoms)
g=raw_ground.difference(unary_union(holes))
ports={'source_via':(38.6,21.6,.3),'source_old_via':(37.675,24.,.3),'load_EP_via':(78.819766,21.275,.2),'C206_ground_via':(85.12,-6.8,.3)}
# Retained scalar trace/barrel terms require unchanged physical terminals.
bb,_,bu=c.collect(baseline);assert not bu
terminal_tracks={'4c8ad6a2-9b32-4016-9596-d0b0bce231a3','6e1eba61-9b5e-5732-91ec-2bb8003465c9'}
terminal_pads={('C157','2'),('U201','41'),('C206','2')}
def terminal_geometry(board):
 answer={'tracks':{},'pads':{},'vias':{},'stackup':c.child(c.child(board,'setup')[0],'stackup')}
 for seg in c.child(board,'segment'):
  uid=c.get(seg,'uuid')[0]
  if uid in terminal_tracks:answer['tracks'][uid]=seg
 for f in c.child(board,'footprint'):
  ref=c.prop(f)['Reference']
  for pad in c.child(f,'pad'):
   if (ref,str(pad[1]))in terminal_pads:answer['pads'][ref+'.'+str(pad[1])]=[c.get(f,'at'),pad]
 for name,(x,y,dr)in {**ports,'source_via':(37.675,24.,.3)}.items():
  matching=[v for v in c.child(board,'via')if math.dist(c.get(v,'at')[:2],(x,y))<1e-7]
  assert len(matching)==1,(name,len(matching))
  via=matching[0];assert c.get(via,'net')==[30]and c.get(via,'drill')==[dr]
  answer['vias'][name]=via
 assert len(answer['tracks'])==2 and len(answer['pads'])==3
 return tuple(json.dumps(canonicalize(q),sort_keys=True)for q in [answer['stackup'],sorted(answer['tracks'].items()),sorted(answer['pads'].items()),list(answer['vias'].items())])
assert terminal_geometry(b)==terminal_geometry(bb),'Terminal or stack geometry changed; regenerate trace/barrel contract'
import uuid
from shapely.geometry import LineString
new_trace=[]
for seg in c.child(b,'segment'):
 for j in range(10):
  ident=str(uuid.uuid5(uuid.NAMESPACE_URL,'GR86-I32-route:source_return_close_trace:'+str(j)))
  if c.get(seg,'uuid')==[ident]:new_trace.append(seg)
assert new_trace and all(c.get(seg,'net')==[30]and c.get(seg,'layer')==['B.Cu']and c.get(seg,'width')==[.6]for seg in new_trace)
new_lines=[LineString([c.get(seg,'start'),c.get(seg,'end')])for seg in new_trace]
connection=unary_union(new_lines).buffer(1e-6)
assert connection.covers(Point(37.675,22))and connection.covers(Point(38.6,21.6))and connection.geom_type=='Polygon'
new_length_mm=sum(line.length for line in new_lines)
trace_R_per_mm=1.724e-8*(1+.00393*130)*.001/(.54e-3*50e-6)
source_trace_delta_R=(new_length_mm-2)*trace_R_per_mm
assert source_trace_delta_R<0
terminal_signature=hashlib.sha256('\n'.join(terminal_geometry(b)).encode()).hexdigest()
rho=1.724e-8*(1+.00393*130);sheet=rho/24e-6;rows=[]
for h in [.1,.075]:
 core=g.buffer(-math.sqrt(2)*h/2-1e-6);xmin,ymin,xmax,ymax=g.bounds
 xs=np.arange(math.floor(xmin/h)*h+h/2,xmax,h);ys=np.arange(math.floor(ymin/h)*h+h/2,ymax,h)
 X,Y=np.meshgrid(xs,ys);sh.prepare(core);valid=sh.contains_xy(core,X,Y);ij=np.full(valid.shape,-1,dtype=np.int32);ij[valid]=np.arange(valid.sum());n=int(valid.sum())
 aa=[];bb=[]
 for a,z in [(ij[:,:-1],ij[:,1:]),(ij[:-1,:],ij[1:,:])]:
  ok=(a>=0)&(z>=0);aa.append(a[ok]);bb.append(z[ok])
 a=np.concatenate(aa);z=np.concatenate(bb);one=np.ones(len(a))/sheet
 A=coo_matrix((np.r_[one,one,-one,-one],(np.r_[a,z,a,z],np.r_[a,z,z,a])),shape=(n,n)).tocsr()
 nc,lab=connected_components(A);xx=X[valid];yy=Y[valid];pi={}
 for name,(x,y,dr) in ports.items():
  d=np.hypot(xx-x,yy-y);eligible=np.flatnonzero((d>dr/2)&(d<.3))
  if not len(eligible):
   print('No wholly retained land cell',h,name,flush=True);pi={};break
  # Closest retained cell centre on actual via land, favour largest component.
  biggest=max(eligible,key=lambda i:np.count_nonzero(lab==lab[i]));same=eligible[lab[eligible]==lab[biggest]];k=int(same[np.argmin(d[same])]);pi[name]=k
 if not pi:
  rows.append({'mesh_mm':h,'status':'NO_FULL_LAND_CELL','nodes':n});continue
 assert len({lab[i]for i in pi.values()})==1
 keep=np.flatnonzero(lab==lab[next(iter(pi.values()))]);remap=np.full(n,-1);remap[keep]=np.arange(len(keep));B=A[keep][:,keep];pi={k:int(remap[v])for k,v in pi.items()}
 ground=pi['load_EP_via'];free=np.flatnonzero(np.arange(len(keep))!=ground);C=B[free][:,free];ml=pyamg.smoothed_aggregation_solver(C,max_coarse=500);M=ml.aspreconditioner(cycle='V');measures=[]
 for name in ['source_via','source_old_via','C206_ground_via']:
  rhs=np.zeros(len(keep));rhs[pi[name]]=1;rhs[ground]=-1
  v,info=cg(C,rhs[free],M=M,rtol=1e-10,atol=1e-12,maxiter=2500);assert info==0,info
  vv=np.zeros(len(keep));vv[free]=v;r=float(vv[pi[name]]);res=float(np.max(abs(B@vv-rhs)))
  assert res<1e-7
  measures.append({'from':name,'to':'load_EP_via','restricted_plane_R_ohm':r,'max_KCL_residual_A':res,'source_port_potentials_V_per_A':{key:float(vv[pi[key]])for key in ['source_via','source_old_via']}})
 out={'mesh_mm':h,'status':'SOLVED_RESTRICTED_GROUND_SUBSET','nodes':len(keep),'retained_area_mm2':len(keep)*h*h,'ports':pi,'measurements':measures};rows.append(out);print(json.dumps(out),flush=True)
(D/'GROUND_PLANE_REFINED.json').write_text(json.dumps({'source_filled_pcb_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'source_PCB_sha256':args.expected_source_hash,'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'terminal_geometry_signature_sha256':terminal_signature,'explicit_footprint_bores_removed':footprint_holes,'total_bores_removed':len(holes),'removed_drill_copper_area_mm2':raw_ground.area-g.area,'layer':'In1.Cu','temperature_C':150,'copper_um':24,'sheet_R_ohm':sheet,'rows':rows,'limits':['Includes only actual In1 ground subset. No removed copper, layer parallel paths or extra contacts are credited.','No disconnected pieces are joined within a cell. All cells fit entirely in source copper by half-diagonal erosion.','Point current injection represents one retained cell of the actual via land. Via barrels and source/terminal tracks are added separately.','Numerical centre-to-centre finite volume is not a strict continuum upper-bound theorem; use two-mesh result and explicit numerical margin.']},indent=2)+'\n')

# Retain the original finite-power model's non-plane terms exactly. For the
# plane term use the larger of the two freshly solved meshes plus the original
# 10% inflation. No manufactured contact or exact continuum theorem is claimed.
original=json.loads((W/'analyses/power_i24/GROUND_RETURN_CONTRACT.json').read_text())
assert len(rows)==2 and all(r['status']=='SOLVED_RESTRICTED_GROUND_SUBSET'for r in rows)
contract={k:v for k,v in original.items()}
# Both real vias join the same C157 pad through explicit B copper. Account
# for shared In1 spreading using its FULL two-port impedance matrix, not two
# falsely independent plane resistors. Retain original barrel/copper bounds.
load_barrel=original['terms'][1]['retained_nonplane_ohm']
old_source_branch=original['terms'][0]['retained_nonplane_ohm']-load_barrel
new_source_branch=old_source_branch+source_trace_delta_R
pad_spreading=0.001 # extra 1mohm for common pad current crowding/branch overlap
source_values=[];cap_values=[];network_rows=[]
for row in rows:
 by={x['from']:x for x in row['measurements']}
 order=['source_via','source_old_via']
 Z=np.array([[by[col]['source_port_potentials_V_per_A'][dest]for col in order]for dest in order])
 assert np.max(abs(Z-Z.T))<1e-8 and np.linalg.eigvalsh(Z).min()>0
 Z=(Z+Z.T)/2
 A=1.1*Z+np.diag([new_source_branch,old_source_branch])
 fractions=np.linalg.solve(A,np.ones(2));equiv=1/fractions.sum();fractions*=equiv
 assert min(fractions)>0 and abs(sum(fractions)-1)<1e-10
 total=float(equiv+load_barrel+pad_spreading);source_values.append(total)
 cap_values.append(load_barrel+1.1*by['C206_ground_via']['restricted_plane_R_ohm'])
 network_rows.append(dict(mesh_mm=row['mesh_mm'],plane_impedance_matrix_ohm=Z.tolist(),source_branch_R_ohm=[new_source_branch,old_source_branch],source_current_fractions=fractions.tolist(),numerical_plane_multiplier=1.1,load_barrel_ohm=load_barrel,additional_common_pad_spreading_ohm=pad_spreading,total_return_ohm=total))
terms=[]
for key,lim,values in [('source_to_load_ground_upper_ohm','shared_return_allocation_ohm',source_values),('C206_to_load_plane_plus_load_barrel_upper_ohm','C206_ground_spreading_allocation_ohm',cap_values)]:
 contract[key]=max(values);terms.append(dict(contract_key=key,mesh_total_values_ohm=values,margin_ohm=contract[lim]-contract[key],pass_allocation=contract[key]<contract[lim]))
contract['source_two_port_network']=network_rows
contract.update(status='PASS_RETAINED_POWER_RETURN_ALLOCATIONS'if all(t['pass_allocation']for t in terms)else'FINDINGS_POWER_RETURN_ALLOCATION',
 original_contract=original,terminal_baseline_PCB_sha256=args.baseline_hash,new_source_return_trace_mm=new_length_mm,source_return_nonplane_delta_ohm=source_trace_delta_R,source_return_ports_mm=[[38.6,21.6],[37.675,24]],filled_PCB_sha256=args.expected_hash,source_PCB_sha256=args.expected_source_hash,
 method='Recompute actual In1 restricted copper including all via/PTH/NPTH bores at 0.1 and 0.075 mm; verify original terminal/stack identity; solve the coupled two-port source return using actual old/new 0.6mm B traces, equal 0.3mm drill/15um barrels, 1mohm added common-pad spreading and 10% plane inflation; use larger mesh resistance and original 10% inflation.',
 terminal_geometry_signature_sha256=terminal_signature,terms=terms,physical_tests_claimed=0)
(D/'GROUND_RETURN_CONTRACT.json').write_text(json.dumps(contract,indent=2)+'\n')
print(json.dumps(contract,indent=2),flush=True)
if not all(t['pass_allocation']for t in terms):raise SystemExit(1)
