#!/usr/bin/env python3
"""Deterministic I32 silkscreen finishing; native DRC is an independent gate."""
from pathlib import Path
import hashlib,json,math,sys
import pcbnew as p
from shapely.geometry import box,Polygon,LineString,Point
from shapely.ops import unary_union
import author_candidate as a
import controlled_reservoir as cr
import route_candidate as r
c=r.c

def main():
    assert p.GetBuildVersion().startswith('9.0.9')
    tree=c.sx.loads(r.P.read_text());refs=set(cr.PARTS)|{'R151','R155','R156','R158'}
    # Retain the exact brand geometry, moved clear of input capacitors.
    polys=c.child(tree,'gr_poly')
    xs=[q[1]for v in polys for q in c.child(c.child(v,'pts')[0],'xy')]
    if min(xs)>29:
        for v in polys:
            for q in c.child(c.child(v,'pts')[0],'xy'):q[1]=round(q[1]-16,6);q[2]=round(q[2]+53.355079,6)
    else:assert abs(min(xs)-14)<1e-6
    # Small generic library body strokes conflict with dense placement. Fab
    # outlines remain complete; clear reference labels and polarity marks follow.
    for f in c.child(tree,'footprint'):
        if c.prop(f).get('Reference')not in refs or c.prop(f).get('Reference')=='D105':continue
        for q in list(f):
            if c.tag(q).startswith('fp_')and(c.get(q,'layer')or[''])[0].endswith('SilkS'):f.remove(q)
    for ref,xx in [('C162',44.5)]:
        ident=a.uid(ref+'-polarity')
        for q in list(c.child(tree,'gr_text')):
            if c.get(q,'uuid')==[ident]:tree.remove(q)
        tree.append(c.sx.loads(f'(gr_text "+" (at {xx} -7.4 0) (layer "F.SilkS") (uuid "{ident}") (effects (font (size 1 1) (thickness 0.15))))'))
    for ref,x,y,layer in [('U152',41.7,5.8,'B.SilkS'),('U153',77.7,-1.7,'B.SilkS'),('Q152',44,43.05,'F.SilkS'),('Q153',48,43.05,'F.SilkS')]:
        ident=a.uid(ref+'-pin1-mark')
        if not any(c.get(q,'uuid')==[ident]for q in c.child(tree,'gr_circle')):
            tree.append(c.sx.loads(f'(gr_circle (center {x} {y}) (end {x+.1} {y}) (stroke (width .15) (type default)) (fill solid) (layer "{layer}") (uuid "{ident}"))'))
    r.P.write_text(r.dump(tree));r.read()
    b=p.LoadBoard(str(r.P));assert b
    sides={'F.Cu':p.F_SilkS,'B.Cu':p.B_SilkS};obstacles={k:[]for k in sides}
    # Unplated holes also open the solder mask. The copper collector omits
    # these non-electrical items, so include them explicitly on both faces.
    for f0 in c.child(r.b,'footprint'):
        for pad in c.child(f0,'pad'):
            if str(pad[2])=='np_thru_hole':
                g=c.pad_shape(f0,pad).buffer(.2)
                for side in sides:obstacles[side].append(g)
    for it in r.items:
        if it['layer']in sides and it['type']in ['pad','via']:obstacles[it['layer']].append(it['geometry'].buffer(.2))
    for f in c.child(r.b,'footprint'):
        side=c.get(f,'layer')[0]
        if side not in sides:continue
        x,y,*aa=c.get(f,'at');ang=math.radians(aa[0]if aa else 0);points=[]
        for q in c.child(f,'fp_rect')+c.child(f,'fp_line'):
            if not (c.get(q,'layer')or [''])[0].endswith('CrtYd'):continue
            lo,hi=c.get(q,'start'),c.get(q,'end')
            pp=[lo,hi]if c.tag(q)=='fp_line'else[(lo[0],lo[1]),(lo[0],hi[1]),(hi[0],lo[1]),(hi[0],hi[1])]
            points += [(x+u*math.cos(ang)+v*math.sin(ang),y-u*math.sin(ang)+v*math.cos(ang))for u,v in pp]
        if points:obstacles[side].append(box(min(q[0]for q in points),min(q[1]for q in points),max(q[0]for q in points),max(q[1]for q in points)).buffer(.1))
    def bbox(obj):
        q=obj.GetBoundingBox();return box(p.ToMM(q.GetX()),p.ToMM(q.GetY()),p.ToMM(q.GetRight()),p.ToMM(q.GetBottom()))
    legends=[]
    for obj in b.GetDrawings():
        if str(obj.m_Uuid.AsString())in ['07c69d64-98cb-4813-9eb5-50beb172a101','7bf1e246-fdc4-4858-8f2e-7faf4a525528']:
            legends.append(obj);continue
        layer=b.GetLayerName(obj.GetLayer())
        if layer in ['F.Silkscreen','B.Silkscreen']:
            side='F.Cu'if layer.startswith('F.')else'B.Cu'
            if obj.GetClass()=='PCB_SHAPE'and obj.GetShape()==p.SHAPE_T_POLY:
                ps=obj.GetPolyShape()
                for i in range(ps.OutlineCount()):
                    poly=ps.Outline(i);obstacles[side].append(Polygon([(p.ToMM(poly.CPoint(j).x),p.ToMM(poly.CPoint(j).y))for j in range(poly.PointCount())]).buffer(.15))
            else:obstacles[side].append(bbox(obj).buffer(.15))
    for f in b.GetFootprints():
        side='F.Cu'if f.GetLayer()==p.F_Cu else'B.Cu'
        for obj in f.GraphicalItems():
            if obj.GetLayer()==sides[side]:obstacles[side].append(bbox(obj).buffer(.15))
        for obj in [f.Reference(),f.Value()]:
            if obj.IsVisible()and obj.GetLayer()==sides[side]and f.GetReference()not in refs:obstacles[side].append(bbox(obj).buffer(.15))
    out=[]
    for t in legends:
        side='B.Cu';x=80 if t.GetText()=='201'else 83;y=4
        t.SetTextSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)));t.SetTextThickness(p.FromMM(.15))
        ob=unary_union(obstacles[side]);candidates=[]
        for ix in range(-40,41):
            for iy in range(-40,41):
                for angle in [0,90]:candidates.append((math.hypot(ix*.2,iy*.2)+(.2 if angle else 0),x+ix*.2,y+iy*.2,angle))
        for _,xx,yy,angle in sorted(candidates):
            t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));t.SetPosition(p.VECTOR2I(p.FromMM(xx),p.FromMM(yy)));g=bbox(t)
            if r.outline.buffer(-.25).covers(g)and not g.intersects(ob):break
        else:raise RuntimeError('No clear probe legend '+t.GetText())
        obstacles[side].append(g.buffer(.15));out.append(dict(ref='TP'+t.GetText()+' legend',side=side,xy_mm=[xx,yy],bounds_mm=list(g.bounds)))
    for f in sorted(b.GetFootprints(),key=lambda f:(0 if f.GetReference()in ['TP154','R151','U152']else 1,f.GetReference())):
        ref=f.GetReference()
        if ref not in refs:continue
        side='F.Cu'if f.GetLayer()==p.F_Cu else'B.Cu';t=f.Reference();t.SetVisible(True);t.SetLayer(sides[side]);t.SetTextSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)));t.SetTextThickness(p.FromMM(.15));t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));t.SetKeepUpright(False);t.SetMirrored(side=='B.Cu')
        x,y=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y);ob=unary_union(obstacles[side]);candidates=[]
        for iy in range(-60,61):
            for ix in range(-60,61):
                dx,dy=ix*.2,iy*.2
                if abs(dx)<.3 and abs(dy)<.8:continue
                if side=='B.Cu'and x<55 and y+dy<.6:continue
                for angle in [0,90]:candidates.append((math.hypot(dx,dy)+.1*abs(dx)+(.2 if angle else 0),x+dx,y+dy,angle))
        for _,xx,yy,angle in sorted(candidates):
            t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
            t.SetPosition(p.VECTOR2I(p.FromMM(xx),p.FromMM(yy)));g=bbox(t)
            if r.outline.buffer(-.25).covers(g)and not g.intersects(ob):break
        else:raise RuntimeError('No clear reference position for '+ref)
        obstacles[side].append(g.buffer(.15));out.append(dict(ref=ref,side=side,xy_mm=[xx,yy],bounds_mm=list(g.bounds)))
    # Controlled local variants preserve the tailored silkscreen in the library.
    # Electrical pads and Fab/courtyard geometry are unchanged. Never waive a
    # footprint mismatch to permit an unrecorded on-board modification.
    variants={}
    for f in b.GetFootprints():
        ref=f.GetReference()
        if ref not in refs or ref=='D105':continue
        name='I32_FINISHED_'+ref
        f.SetFPID(p.LIB_ID('RevB',name));variants[ref]='RevB:'+name
        clone=p.FOOTPRINT(f)
        if clone.GetLayer()!=p.F_Cu:clone.Flip(clone.GetPosition(),False)
        clone.SetOrientation(p.EDA_ANGLE(0,p.DEGREES_T));clone.SetPosition(p.VECTOR2I(0,0))
        p.FootprintSave(str(a.CAD/'libraries/RevB.pretty'),clone)
        assert (a.CAD/'libraries/RevB.pretty'/(name+'.kicad_mod')).exists()
    p.SaveBoard(str(r.P),b)
    for path in a.CAD.glob('*.kicad_sch'):
        sch=c.sx.loads(path.read_text());changed=False
        for sym in c.child(sch,'symbol'):
            ref=c.prop(sym).get('Reference')
            if ref in variants:a.prop(sym,'Footprint',variants[ref]);changed=True
        if changed:path.write_text(a.dump(sch))
    (a.HERE/'SILK_FINISH.json').write_text(json.dumps(dict(reference_placements=out,logo_translation_mm=[-16,53.355079],logo_preserved_without_scaling=True,scope='Conservative bounding-box preflight; final native DRC still required.'),indent=2)+'\n')
    print('Placed',len(out),'references and preserved translated logo')

if __name__=='__main__':main()
