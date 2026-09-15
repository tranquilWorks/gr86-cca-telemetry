#!/usr/bin/env python3
"""Build a source-bound Rev B PCBA quote/first-article handoff, without CI or writes to source."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

W = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(W / 'analyses/convergence_01/support'))
import sexpdata as sx
import check_combined_copper as cad

PCB_SHA = 'a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936'
NATIVE_ZIP_SHA = '3515bd44911e4504a110269bbef8f567118ab8ab9223e47f2931ad9c5a307731'
PREFIX = 'native_I06_hosted/'
MANUAL = {'F101', 'U401'}
DNP = {'C203', 'R301', 'R306'}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def refkey(ref: str):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', ref)]


def csv_bytes(fields, rows) -> bytes:
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def as_json(data) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def archive(entries: dict[str, bytes], path: Path) -> None:
    require(not path.exists(), f'Refusing to overwrite {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(entries.items()):
            require(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts,
                    f'Unsafe member {name}')
            item = zipfile.ZipInfo(name, date_time=(2026, 9, 12, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            z.writestr(item, data)


def build(native_zip: Path, output: Path) -> dict:
    require(digest(native_zip.read_bytes()) == NATIVE_ZIP_SHA, 'Wrong native archive: explicit rebind required')
    source = W / 'candidate'
    pcb = source / 'cad/GR86_CCA_RevB.kicad_pcb'
    require(digest(pcb.read_bytes()) == PCB_SHA, 'Current PCB differs from package effectivity')
    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(native_zip) as z:
        require(len(z.namelist()) == len(set(z.namelist())), 'Duplicate archive members')
        read = lambda name: z.read(PREFIX + name)
        inventory = json.loads(read('COPIED_SOURCE_INVENTORY.json'))
        verified_inputs = {}
        for section, folder in [('cad_before_native', 'cad'), ('firmware_before_compile', 'firmware')]:
            for name, expected in inventory[section].items():
                require('..' not in PurePosixPath(name).parts and not PurePosixPath(name).is_absolute(), 'Unsafe source path')
                data = (source / folder / name).read_bytes()
                require(digest(data) == expected, f'Native evidence does not match current source: {folder}/{name}')
                entries[f'editable_source/{folder}/{name}'] = data
            verified_inputs[folder] = len(inventory[section])
        require(verified_inputs == {'cad': 101, 'firmware': 32}, 'Unexpected source inventory')
        native_manifest = json.loads(read('OUTPUT_MANIFEST.json'))['files']
        for name, spec in native_manifest.items():
            data = read(name)
            require(digest(data) == spec['sha256'] and len(data) == spec['bytes'], f'Corrupt native output: {name}')
        result = json.loads(read('RESULT.json'))
        require(result['status'] == 'NATIVE_OUTPUTS_COMPLETE', 'Native product exports incomplete')
        require(result['native_report_finding_count'] == 0, 'Native electrical/geometry findings present')
        require(not result['nonzero_commands'] and not result['incomplete_outputs'], 'Native export failure')
        require(all(x['pass'] for x in result['output_postconditions'].values()), 'Native export postcondition failure')
        bom_rows = list(csv.DictReader(io.StringIO(read('REVIEW_BOM.csv').decode())))
        positions = list(csv.DictReader(io.StringIO(read('REVIEW_POSITIONS.csv').decode())))
        tree = sx.loads(pcb.read_text())
        footprints = {cad.prop(f)['Reference']: f for f in cad.child(tree, 'footprint')}
        props = {ref: cad.prop(f) for ref, f in footprints.items()}
        fitted = {ref for ref, p in props.items() if p.get('Assembly') in ('FACTORY', 'MANUAL_GPS')}
        require(len(fitted) == 153, 'Fitted product inventory changed')
        require({ref for ref, p in props.items() if p.get('Assembly') == 'DNP'} == DNP, 'DNP variant changed')
        by_ref = {r['Reference']: r for r in bom_rows}
        require(len(bom_rows) == 153 and set(by_ref) == fitted, 'BOM misses/duplicates fitted parts')
        require(len(positions) == 151 and len({r['Ref'] for r in positions}) == 151,
                'Duplicate or missing placement rows')
        require({r['Ref'] for r in positions} == fitted - MANUAL, 'Factory/manual split is wrong')
        for ref in fitted:
            require(by_ref[ref]['MPN'] == props[ref]['MPN'], f'MPN mismatch: {ref}')
            require(by_ref[ref]['LCSC'] == props[ref].get('LCSC', ''), f'Supplier identity mismatch: {ref}')
        require(by_ref['U121']['MPN'] == 'LM5164QDDARQ1' and by_ref['U121']['LCSC'] == 'C2072225', 'Wrong buck variant')
        require(props['F101']['Factory_Paste'] == 'NO' and props['F101']['Assembly_Process'] == 'FACTORY_LOCAL_AFTER_REFLOW', 'Fuse process changed')
        for row in positions:
            require(row['Side'] in ('top', 'bottom'), 'Invalid placement side')
            require(all(math.isfinite(float(row[k])) for k in ('PosX', 'PosY', 'Rot')), 'Nonfinite position')
        factory = [by_ref[ref] for ref in sorted(fitted - MANUAL, key=refkey)]
        entries['assembly/JLCPCB_BOM.csv'] = csv_bytes(
            ['Comment', 'Designator', 'Footprint', 'LCSC Part #'],
            [{'Comment': r['Value'], 'Designator': r['Reference'], 'Footprint': r['Footprint'], 'LCSC Part #': r['LCSC']} for r in factory])
        entries['assembly/JLCPCB_CPL.csv'] = csv_bytes(
            ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'],
            [{'Designator': r['Ref'], 'Mid X': r['PosX'] + 'mm', 'Mid Y': r['PosY'] + 'mm',
              'Layer': r['Side'].title(), 'Rotation': r['Rot']} for r in sorted(positions, key=lambda r: refkey(r['Ref']))])
        entries['assembly/COMPLETE_FITTED_BOM.csv'] = csv_bytes(list(bom_rows[0]), [by_ref[r] for r in sorted(fitted, key=refkey)])
        entries['assembly/LOCAL_ASSEMBLY_BOM.csv'] = csv_bytes(list(bom_rows[0]), [by_ref[r] for r in sorted(MANUAL)])
        entries['assembly/DO_NOT_POPULATE.json'] = as_json({ref: props[ref] for ref in sorted(DNP)})
        unassigned = [r for r in factory if not re.fullmatch(r'C\d+', r['LCSC'])]
        entries['assembly/SOURCING_REQUIRED.csv'] = csv_bytes(list(bom_rows[0]), unassigned)
        # Enumerate the exact 48 inherited heat-via identities on the current PCB.
        via_by_uuid = {str(cad.get(v, 'uuid')[0]): v for v in cad.child(tree, 'via')}
        source_vias = json.loads((source / 'verification/I13/SOURCE_CHANGE_CHECK.json').read_text())['new_vias']
        selected = []
        for row in source_vias:
            v = via_by_uuid[row['uuid']]
            require(list(cad.get(v, 'at')) == row['xy'], 'U201 heat via moved')
            selected.append(('U201 pad 41', row['uuid'], v))
        require(len(selected) == 48, 'Wrong U201 heat-via count')
        r153 = footprints['R153']
        at = cad.get(r153, 'at')
        require(len(at) == 2 or float(at[2]) == 0, 'R153 orientation changed')
        pad2 = next(p for p in cad.child(r153, 'pad') if str(p[1]) == '2')
        pa, ps = cad.get(pad2, 'at'), cad.get(pad2, 'size')
        center = [float(at[i]) + float(pa[i]) for i in (0, 1)]
        pad_vias = [(uid, v) for uid, v in via_by_uuid.items()
                    if all(abs(float(cad.get(v, 'at')[i]) - center[i]) <= float(ps[i])/2 for i in (0, 1))]
        require(len(pad_vias) == 1, 'R153 via-in-pad identity ambiguous')
        selected.append(('R153 pad 2', *pad_vias[0]))
        entries['fabrication/FILL_CAP_PLANARIZE_49_VIAS.csv'] = csv_bytes(
            ['Reference', 'UUID', 'PCB X mm', 'PCB Y mm', 'Drill mm', 'Land mm'],
            [{'Reference': ref, 'UUID': uid, 'PCB X mm': cad.get(v, 'at')[0], 'PCB Y mm': cad.get(v, 'at')[1],
              'Drill mm': cad.get(v, 'drill')[0], 'Land mm': cad.get(v, 'size')[0]} for ref, uid, v in selected])
        setup = cad.child(tree, 'setup')[0]
        entries['fabrication/AUTHORED_STACKUP.json'] = as_json(json.loads(json.dumps(cad.get(setup, 'stackup'), default=str)))
        fab = {Path(n).name: read(n) for n in native_manifest if n.startswith('review_gerbers/')}
        require(len(fab) == 14, 'Expected eleven Gerbers, two drill files and one Gerber job')
        for name, data in fab.items():
            entries['fabrication/gerbers/' + name] = data
        gerber_buffer = io.BytesIO()
        with zipfile.ZipFile(gerber_buffer, 'w', zipfile.ZIP_DEFLATED) as gz:
            for name, data in sorted(fab.items()):
                zi = zipfile.ZipInfo(name, date_time=(2026, 9, 12, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                gz.writestr(zi, data)
        entries['fabrication/JLCPCB_GERBERS.zip'] = gerber_buffer.getvalue()
        for name in ('REVIEW_SCHEMATIC.pdf', 'REVIEW_COMPONENTS.step', 'PCB_NETLIST.d356', 'SCHEMATIC_NETLIST.xml'):
            entries['review/' + name] = read(name)
        for name in ('RESULT.json', 'DRC.json', 'ERC.json', 'COPIED_SOURCE_INVENTORY.json', 'OUTPUT_MANIFEST.json'):
            entries['evidence/native/' + name] = read(name)
        for name in native_manifest:
            if name.startswith('firmware_images/') and name.endswith(('.bin', '.elf', '.map')):
                entries[name] = read(name)
        entries['review/REFILLED_NATIVE_BOARD.kicad_pcb'] = read('candidate_kicad/GR86_CCA_RevB.kicad_pcb')
        for path in (W / 'current/mechanics').iterdir():
            if path.is_file():
                entries['mechanics/current_C05_W02_T03/' + path.name] = path.read_bytes()
        for name in ('I25_THERMAL_MILESTONE.json', 'I25_THERMAL_MILESTONE.md', 'I27_FABRICATION_READINESS.json',
                     'analyses/i26/QUALIFICATION_GATES.json', 'analyses/i26/GND02_DESKTOP_CLOSURE.json',
                     'interfaces/HARNESS_INTERFACE_CONTRACT.md', 'interfaces/HARNESS_INTERFACE_CONTRACT.json'):
            entries['evidence/product/' + name] = (W / name).read_bytes()
        entries['reference/HISTORICAL_I22_MANUFACTURING.md'] = (W / 'current/MANUFACTURING_AND_ASSEMBLY.md').read_bytes()
        entries['START_HERE.md'] = (W / 'product/PRODUCT_HANDOFF.md').read_bytes()
        # Supplementary analyses are explicitly scope-qualified by their own report.
        for path in (W / 'product').rglob('*'):
            if path.is_file() and path.suffix in ('.cir', '.json', '.md', '.py') and '__pycache__' not in path.parts and path.name != 'PACKAGE_VERIFICATION.json':
                entries['product_notes/' + path.relative_to(W / 'product').as_posix()] = path.read_bytes()
        summary = {'status': 'SOURCE_BOUND_PCBA_QUOTE_AND_FIRST_ARTICLE_HANDOFF', 'source_PCB_sha256': PCB_SHA,
                   'native_archive_sha256': NATIVE_ZIP_SHA, 'native_export_commit': z.read('native_setup/commit.txt').decode().strip(),
                   'source_files_verified': verified_inputs, 'native_outputs_verified': len(native_manifest),
                   'fitted_parts': 153, 'factory_placement_rows': 151, 'local_assembly_parts': sorted(MANUAL),
                   'DNP': sorted(DNP), 'filled_capped_vias': len(selected), 'unassigned_factory_LCSC_references': [r['Reference'] for r in unassigned],
                   'supplier_acceptance': False, 'physical_tests_performed': 0, 'CI_completion_required_to_build_package': False,
                   'manufacturing_order_placed': False, 'automatic_turnkey_PCBA_order_ready': not unassigned,
                   'full_product_qualified': False}
        entries['PACKAGE_VERIFICATION.json'] = as_json(summary)
        entries['SHA256SUMS.json'] = as_json({n: digest(data) for n, data in sorted(entries.items())})
        archive(entries, output)
        return {**summary, 'package_file': output.name, 'package_sha256': digest(output.read_bytes()), 'package_members': len(entries)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-zip', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.native_zip, args.output), indent=2))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'Package not published: {exc}\n')
