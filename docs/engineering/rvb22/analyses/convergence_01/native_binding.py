"""Pin electrical/manufacturing content while tolerating native-generated drawing UUIDs."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "support"))
import sexpdata as sx

SOURCE_HASH = "a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936"
SOURCE_PCB = Path(__file__).resolve().parents[2] / "candidate" / "cad" / "GR86_CCA_RevB.kicad_pcb"
NON_ELECTRICAL_LAYERS = {"F.Fab", "B.Fab", "F.CrtYd", "B.CrtYd"}

def canonicalize(node):
    """Preserve all values, geometry, order, copper and pad UUIDs; omit only drawing IDs."""
    if not isinstance(node, list):
        return str(node) if isinstance(node, sx.Symbol) else node
    tag = str(node[0]) if node else ""
    layer = next((str(x[1]) for x in node[1:] if isinstance(x, list)
                  and len(x) > 1 and str(x[0]) == "layer"), None)
    omit_id = tag == "property" or (tag.startswith("fp_") and layer in NON_ELECTRICAL_LAYERS)
    return [canonicalize(x) for x in node if not (
        omit_id and isinstance(x, list) and x and str(x[0]) == "uuid")]

def content_hash(node):
    data = json.dumps(canonicalize(node), separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()

def verify_filled(path):
    source_data = SOURCE_PCB.read_bytes()
    source_raw = hashlib.sha256(source_data).hexdigest()
    if source_raw != SOURCE_HASH:
        raise ValueError("Controlled PCB source advanced: explicit engineering rebind required")
    reference_content = content_hash(sx.loads(source_data.decode()))

    data = Path(path).read_bytes()
    raw = hashlib.sha256(data).hexdigest()
    stable = content_hash(sx.loads(data.decode()))
    if stable != reference_content:
        raise ValueError("Native board content differs from controlled source: explicit engineering rebind required")
    return {"raw_sha256": raw, "content_sha256": stable,
            "controlled_source_raw_sha256": source_raw,
            "controlled_source_content_sha256": reference_content,
            "content_equal_to_controlled_source": True,
            "only_generated_non_electrical_ids_may_differ": True}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcb", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = verify_filled(args.pcb)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text)
