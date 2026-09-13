"""Pin source-authored electrical/manufacturing content across native KiCad refill."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "support"))
import sexpdata as sx

SOURCE_HASH = "a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936"
SOURCE_PCB = Path(__file__).resolve().parents[2] / "candidate" / "cad" / "GR86_CCA_RevB.kicad_pcb"
NON_ELECTRICAL_FP_LAYERS = {"F.Fab", "B.Fab", "F.CrtYd", "B.CrtYd", "F.SilkS", "B.SilkS"}
NON_ELECTRICAL_FP_GRAPHICS = {"fp_line", "fp_rect", "fp_arc", "fp_circle", "fp_poly", "fp_text", "fp_text_box"}
DERIVED_OR_SERIALIZER_TAGS = {"filled_polygon", "generator", "generator_version"}

def _stable_key(value):
    return json.dumps(value,separators=(",",":"),ensure_ascii=False,sort_keys=True)

def _layer(node):
    return next((str(x[1]) for x in node[1:] if isinstance(x,list) and len(x)>1 and str(x[0])=="layer"),None)

def canonicalize(node):
    """Bind authored electrical/manufacturing intent, not KiCad's save representation.

    The exact controlled source is independently raw-SHA pinned. A native KiCad save
    may regenerate zone ``filled_polygon`` records, update serializer metadata,
    reorder top-level records, and mirror local coordinates of footprint annotation
    graphics on back-side footprints. The latter are ignored only on Fab/Courtyard/
    Silkscreen layers. Copper footprint graphics, pads, tracks, vias, Edge.Cuts,
    authored zone outlines/rules, nets and stackup remain semantically bound.
    """
    if not isinstance(node,list):
        return str(node) if isinstance(node,sx.Symbol) else node
    tag=str(node[0]) if node else ""
    if tag in DERIVED_OR_SERIALIZER_TAGS:
        return None
    layer=_layer(node)
    if tag in NON_ELECTRICAL_FP_GRAPHICS and layer in NON_ELECTRICAL_FP_LAYERS:
        return None
    omit_id = tag == "property"
    out=[]
    for x in node:
        if omit_id and isinstance(x,list) and x and str(x[0])=="uuid":
            continue
        value=canonicalize(x)
        if value is not None:
            out.append(value)
    if tag=="kicad_pcb" and out:
        return [out[0]]+sorted(out[1:],key=_stable_key)
    return out

def content_hash(node):
    data=json.dumps(canonicalize(node),separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()

def first_difference(a,b,path=()):
    if type(a) is not type(b):return path,a,b
    if isinstance(a,list):
        if len(a)!=len(b):
            for i,(x,y) in enumerate(zip(a,b)):
                d=first_difference(x,y,path+(i,))
                if d is not None:return d
            return path+("len",),len(a),len(b)
        for i,(x,y) in enumerate(zip(a,b)):
            d=first_difference(x,y,path+(i,))
            if d is not None:return d
        return None
    if a!=b:return path,a,b
    return None

def describe_path(root,path):
    node=root;parts=[]
    for p in path:
        if p=="len":parts.append("len");break
        if not isinstance(node,list) or not isinstance(p,int) or p>=len(node):parts.append(str(p));break
        tag=str(node[0]) if node else "[]";parts.append(f"{tag}[{p}]");node=node[p]
    return "/".join(parts)

def verify_filled(path):
    source_data=SOURCE_PCB.read_bytes();source_raw=hashlib.sha256(source_data).hexdigest()
    if source_raw!=SOURCE_HASH:raise ValueError("Controlled PCB source advanced: explicit engineering rebind required")
    source_tree=sx.loads(source_data.decode());source_canon=canonicalize(source_tree);reference_content=content_hash(source_tree)
    data=Path(path).read_bytes();raw=hashlib.sha256(data).hexdigest();native_tree=sx.loads(data.decode());native_canon=canonicalize(native_tree);stable=content_hash(native_tree)
    if stable!=reference_content:
        d=first_difference(source_canon,native_canon)
        detail="hash differs without structural diff" if d is None else f"first_difference={d[0]} semantic_path={describe_path(source_canon,d[0])} controlled={repr(d[1])[:240]} native={repr(d[2])[:240]}"
        raise ValueError("Native board authored content differs from controlled source: explicit engineering rebind required; "+detail)
    return {"raw_sha256":raw,"content_sha256":stable,"controlled_source_raw_sha256":source_raw,"controlled_source_content_sha256":reference_content,"content_equal_to_controlled_source":True,"top_level_record_order_ignored":True,"excluded_native_generated_tags":sorted(DERIVED_OR_SERIALIZER_TAGS),"excluded_non_electrical_footprint_graphics_layers":sorted(NON_ELECTRICAL_FP_LAYERS),"native_refill_electrical_validation":"DRC/export/copper checks remain required"}

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("pcb",type=Path);parser.add_argument("--out",type=Path);args=parser.parse_args();result=verify_filled(args.pcb);text=json.dumps(result,indent=2)+"\n"
    if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(text)
    print(text)
