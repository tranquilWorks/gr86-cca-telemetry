#!/usr/bin/env python3
"""Build the sourced I32 ECAD/assembly package without changing qualified physics.

prepare -> run_native_candidate.py -> package -> verify
SOURCES.json owns procurement decisions; candidate/cad owns circuit and geometry.
"""
from pathlib import Path
import argparse
import csv
import gzip
import hashlib
import json
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

D = Path(__file__).resolve().parent
W = D.parents[2]
OLD = W / 'analyses/i32/procurement_redline'
BASE = W / 'candidate/cad'
OUT = W / 'current/i32_sourced_manufacturing'
CAD = OUT / 'editable_source/cad'
ARCHIVE = W / 'product/GR86_I32_SOURCED_MANUFACTURING.zip'
sys.path.insert(0, str(OLD))
import apply_redline as a
from sourcing_evidence import records, walk

FIELDS = ('LCSC', 'ProcurementRoute', 'ProcurementURL', 'SupplierMPN')
LOCAL = {'F101', 'U401'}
DNP = {'C203', 'R301', 'R306'}
ALIASES = {
    ('0430451200', '430451200'): 'https://www.molex.com/en-us/products/part-detail/43045-1200',
    ('ERA3AEB1472V', 'ERA-3AEB1472V'): 'https://industrial.panasonic.com/ww/products/pt/high-precision-chip-resistors/models/ERA3AEB1472V',
    ('CGA4J2X7R2A104K125AA', 'CGA4J2X7R2A104KT0Y0U'): 'https://www.newark.com/tdk/cga4j2x7r2a104k125aa/cap-0-1uf-100v-mlcc-0805/dp/40Y2282',
    ('CGA6N3X7R2A225K230AB', 'CGA6N3X7R2A225KT0Y0U'): 'https://www.digikey.com/en/products/detail/tdk-corporation/CGA6N3X7R2A225K230AB/2443344',
    ('CGA3E2C0G1H101J080AA', 'CGA3E2C0G1H101JT0Y0N'): 'https://www.digikey.com/en/products/detail/tdk/CGA3E2C0G1H101J080AA/2443118',
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def put(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n')


def csvrows(p):
    with p.open(newline='') as f:
        return list(csv.DictReader(f))


def writecsv(p, fields, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def inventory(folder):
    return {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}


def fitted():
    return set(read(BASE / 'FITTED_REFERENCES.json')['fitted_references'])


def footprints(board):
    return {a.props(f)['Reference']: f for f in a.children(board, 'footprint')}


def procurement(ref, mpn, sources):
    s = sources[mpn]
    return {'LCSC': s['LCSC'], 'ProcurementRoute': 'LOCAL_INSTALL' if ref in LOCAL else s['route'],
            'ProcurementURL': s['url'], 'SupplierMPN': s['supplier_mpn']}


def validate_sources():
    sources = read(D / 'SOURCES.json')['parts']
    bom = csvrows(OLD / 'native_final/REVIEW_BOM.csv')
    assert set(sources) == {r['MPN'] for r in bom}
    for mpn, s in sources.items():
        assert s['url'].startswith('https://') and s['supplier_mpn']
        assert s['route'] in {'JLC_CATALOG', 'LOCAL_INSTALL'}
        if s['LCSC']:
            capture = D / 'catalog' / (s['LCSC'] + '.json')
            record = read(capture)
            assert record['componentCode'] == s['LCSC']
            assert record['componentModelEn'] == s['supplier_mpn']
            assert record['isBuyComponent'] == '1' and record['allowPostFlag'] and not record.get('noBuyReason')
            assert s['status'] == ('CATALOG_STOCK' if record['overseasStockCount'] > 0 else 'CATALOG_PREORDER')
            if s['supplier_mpn'] != mpn:
                assert s.get('alias_evidence') == ALIASES.get((mpn, s['supplier_mpn']))
                assert (mpn, s['supplier_mpn']) in ALIASES
                assert s['identity'] in {'DOCUMENTED_FORMAT_ALIAS', 'DOCUMENTED_CATALOG_ALIAS'}
            else:
                assert s['identity'] == 'EXACT_MPN'
            raw = gzip.decompress((capture.with_suffix('.html.gz')).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == record['response_sha256']
            data = [v for root in records(raw.decode()).values() for v in walk(root)]
            for key in ('componentModelEn', 'assemblyMode', 'overseasStockCount', 'isBuyComponent', 'allowPostFlag'):
                assert any(v.get('componentCode') == s['LCSC'] and key in v and v[key] == record.get(key) for v in data), (mpn, key)
        else:
            assert s['route'] == 'LOCAL_INSTALL'
            assert s['supplier_mpn'] == mpn
            assert s['status'] == 'SUPPLIER_QUOTE_REQUIRED'
    for row in bom:
        if row['Reference'] not in LOCAL:
            source = sources[row['MPN']]
            assert source['LCSC'] and source['route'] == 'JLC_CATALOG', row['Reference']
    for ref, spec in a.SPEC.items():
        assert sources[spec['MPN']]['LCSC'] == spec['LCSC'], ref
        assert sources[spec['MPN']]['supplier_mpn'] == spec['MPN'], ref
    return sources


def transform(path, sources):
    """Replace only whitelisted top-level component properties, preserving other bytes."""
    text = path.read_text()
    kind = 'footprint' if path.suffix == '.kicad_pcb' else 'symbol'
    changes = []
    for start, end in a.spans(text):
        part = text[start:end]
        if not part.startswith('(' + kind + ' '):
            continue
        node = a.sx.loads(part)
        p = a.props(node)
        ref = p.get('Reference')
        if ref not in fitted():
            continue
        for key, value in procurement(ref, p['MPN'], sources).items():
            a.prop(node, key, value)
        changes.append((start, end, a.sx.dumps(node)))
    for start, end, part in reversed(changes):
        text = text[:start] + part + text[end:]
    return text


def prepare():
    sources = validate_sources()
    binding = read(OLD / 'SOURCE_BINDING.json')
    assert inventory(BASE) == binding['cad_files'], 'Qualified baseline changed'
    for name in binding['cad_files']:
        src, dst = BASE / name, CAD / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in {'.kicad_pcb', '.kicad_sch'}:
            dst.write_text(transform(src, sources))
        else:
            shutil.copyfile(src, dst)
    verify_cad(sources)
    print('Prepared sourced native CAD; physics and all 177 references verified.')


def verify_cad(sources):
    baseline = read(OLD / 'SOURCE_BINDING.json')['cad_files']
    assert inventory(BASE) == baseline
    assert set(inventory(CAD)) == set(baseline)
    counts = {'schematic': set(), 'PCB': set()}
    changes = []
    for name in baseline:
        src, dst = BASE / name, CAD / name
        if src.suffix not in {'.kicad_pcb', '.kicad_sch'}:
            assert src.read_bytes() == dst.read_bytes(), name
            continue
        assert dst.read_text() == transform(src, sources), 'Generated CAD drift: ' + name
        trees = [a.sx.loads(p.read_text()) for p in (src, dst)]
        kind = 'footprint' if src.suffix == '.kicad_pcb' else 'symbol'
        oldnodes = {a.props(x).get('Reference'): x for x in a.children(trees[0], kind)}
        for node in a.children(trees[1], kind):
            props = a.props(node)
            ref = props.get('Reference')
            if ref not in fitted():
                continue
            counts['PCB' if kind == 'footprint' else 'schematic'].add(ref)
            assert all(props.get(k) == v for k, v in procurement(ref, props['MPN'], sources).items()), ref
            original = a.props(oldnodes[ref])
            changes.append(dict(file=name, reference=ref, MPN=props['MPN'],
                                before={k: original.get(k, '') for k in FIELDS},
                                after={k: props.get(k, '') for k in FIELDS}))
        for tree in trees:
            for node in a.children(tree, kind):
                if a.props(node).get('Reference') in fitted():
                    for p in list(a.children(node, 'property')):
                        if p[1] in FIELDS:
                            node.remove(p)
        assert trees[0] == trees[1], 'Non-procurement mutation: ' + name
    assert counts['PCB'] == counts['schematic'] == fitted()
    return changes


def deterministic_zip(path, folder):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():
                info = zipfile.ZipInfo(str(p.relative_to(folder)), (2026, 9, 15, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, p.read_bytes())


def check_native(native):
    n = read(native / 'RESULT.json')
    assert n['status'] == 'NATIVE_OUTPUTS_COMPLETE' and n['inputs_unchanged']
    assert n['native_report_finding_count'] == 0
    assert all(v['pass'] for v in n['output_postconditions'].values())
    assert n['inputs']['cad'] == inventory(CAD)
    for name, spec in read(native / 'OUTPUT_MANIFEST.json')['files'].items():
        assert sha(native / name) == spec['sha256'], name
    drc = read(native/'DRC.json')
    assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
    # Reuse the independent copper audit only after exact filled-tree and export
    # equivalence. No geometry, aperture, net attribute or drilling code is erased.
    trees = []
    for directory in (OLD/'native_final', native):
        tree = a.sx.loads((directory/'candidate_kicad/GR86_CCA_RevB.kicad_pcb').read_text())
        for f in a.children(tree, 'footprint'):
            for prop in list(a.children(f, 'property')):
                if prop[1] in FIELDS:
                    f.remove(prop)
                else:
                    for uid in a.children(prop, 'uuid'):
                        prop.remove(uid)
        trees.append(tree)
    assert trees[0] == trees[1], 'Native filled physics changed'
    oldgerbers = OLD/'native_final/review_gerbers'
    newgerbers = native/'review_gerbers'
    assert {p.name for p in oldgerbers.iterdir()} == {p.name for p in newgerbers.iterdir()}
    assert len(list(newgerbers.iterdir())) == 14
    for p in newgerbers.iterdir():
        assert fabrication_content(p) == fabrication_content(oldgerbers/p.name), p.name
    assert csvrows(native/'REVIEW_POSITIONS.csv') == csvrows(OLD/'native_final/REVIEW_POSITIONS.csv')
    oldxml = ET.parse(OLD/'native_final/SCHEMATIC_NETLIST.xml')
    newxml = ET.parse(native/'SCHEMATIC_NETLIST.xml')
    assert ET.tostring(oldxml.find('nets')) == ET.tostring(newxml.find('nets'))
    return n


def fabrication_content(path):
    if path.suffix == '.gbrjob':
        value = read(path)
        del value['Header']['CreationDate']
        del value['Header']['GenerationSoftware']['Version']
        return value
    prefixes = ('%TF.GenerationSoftware,', '%TF.CreationDate,',
                'G04 Created by KiCad (PCBNEW ', '; DRILL file {KiCad ',
                '; #@! TF.CreationDate,', '; #@! TF.GenerationSoftware,')
    return [line for line in path.read_text().splitlines() if not line.startswith(prefixes)]


def package(native):
    sources = validate_sources()
    changes = verify_cad(sources)
    n = check_native(native)
    board = a.sx.loads((CAD / 'GR86_CCA_RevB.kicad_pcb').read_text())
    fps = footprints(board)
    rows = csvrows(native / 'REVIEW_BOM.csv')
    by = {r['Reference']: r for r in rows}
    assert len(rows) == len(by) == 177 and set(by) == fitted()
    factory = fitted() - LOCAL
    assert {ref for ref, f in fps.items() if a.props(f).get('Assembly') == 'DNP'} == DNP
    positions = csvrows(native / 'REVIEW_POSITIONS.csv')
    pos = {r['Ref']: r for r in positions}
    assert len(positions) == len(pos) == 175 and set(pos) == factory
    origin = a.get(a.children(board, 'setup')[0], 'aux_axis_origin', [0, 0])
    procurement_rows = []
    for ref, row in by.items():
        props = a.props(fps[ref])
        assert all(row[k] == props.get(k, '') for k in ('Value', 'Manufacturer', 'MPN', 'LCSC'))
        assert row['Footprint'] == str(fps[ref][1]) and row['Quantity'] == '1'
        s = sources[row['MPN']]
        catalog = read(D / 'catalog' / (s['LCSC'] + '.json')) if s['LCSC'] else {}
        procurement_rows.append(dict(**row, Assembly='LOCAL' if ref in LOCAL else 'FACTORY',
            Route='LOCAL_INSTALL' if ref in LOCAL else s['route'], SupplierMPN=s['supplier_mpn'],
            SourceURL=s['url'], Status=s['status'], Identity=s['identity'],
            CatalogAssembly=catalog.get('assemblyMode', ''), StockSnapshot=catalog.get('overseasStockCount', ''),
            PreorderMinimum=catalog.get('preMinPurchaseNum', ''),
            SupplierAcceptance='REQUIRED', Substitutions='NOT_ALLOWED'))
        if ref in factory:
            p = pos[ref]
            x, y, *angle = a.get(fps[ref], 'at')
            angle = angle[0] if angle else 0
            side = 'top' if a.get(fps[ref], 'layer') == ['F.Cu'] else 'bottom'
            assert p['Side'] == side and p['Val'] == row['Value']
            assert p['Package'] == row['Footprint'].split(':', 1)[1]
            assert abs(float(p['PosX']) - (x-origin[0])) < 0.0000011
            assert abs(float(p['PosY']) - (origin[1]-y)) < 0.0000011
            assert abs((float(p['Rot']) - angle + 180) % 360 - 180) < 0.000001
    A = OUT / 'assembly'
    writecsv(A/'COMPLETE_FITTED_BOM.csv', list(rows[0]), rows)
    writecsv(A/'LOCAL_ASSEMBLY_BOM.csv', list(rows[0]), [r for r in rows if r['Reference'] in LOCAL])
    writecsv(A/'PROCUREMENT_BOM.csv', list(procurement_rows[0]), procurement_rows)
    baseline_bom = {r['Reference']: r for r in csvrows(OLD/'native_final/REVIEW_BOM.csv')}
    redline = []
    for row in rows:
        previous = baseline_bom[row['Reference']]
        s = sources[row['MPN']]
        if previous['LCSC'] != row['LCSC'] or s['supplier_mpn'] != row['MPN']:
            reason = ('EXACT_CATALOG_ASSIGNMENT_ADDED' if row['LCSC'] and not previous['LCSC'] else
                      'AMBIGUOUS_CATALOG_ASSIGNMENT_WITHHELD' if not row['LCSC'] else s['identity'])
            redline.append(dict(Reference=row['Reference'], MPN=row['MPN'],
                                PreviousLCSC=previous['LCSC'], CurrentLCSC=row['LCSC'],
                                SupplierMPN=s['supplier_mpn'], Reason=reason, SourceURL=s['url']))
    writecsv(A/'PROCUREMENT_REDLINE.csv', list(redline[0]), redline)
    requests = [r for r in procurement_rows if r['Reference'] in factory and not r['LCSC']]
    assert not requests, 'Every factory reference must be in JLC catalog'
    # Remove the obsolete generated request from the exploratory package.
    (A/'GLOBAL_SOURCING_REQUEST.csv').unlink(missing_ok=True)
    writecsv(A/'PREORDER_REQUIREMENTS.csv', list(procurement_rows[0]),
             [r for r in procurement_rows if r['Reference'] in factory and r['Status'] == 'CATALOG_PREORDER'])
    writecsv(A/'JLCPCB_BOM.csv', ['Comment','Designator','Footprint','LCSC Part #','MPN','Manufacturer'],
        [dict(Comment=r['Value'], Designator=r['Reference'], Footprint=r['Footprint'],
              **{'LCSC Part #': r['LCSC']}, MPN=sources[r['MPN']]['supplier_mpn'], Manufacturer=r['Manufacturer'])
         for r in rows if r['Reference'] in factory])
    writecsv(A/'JLCPCB_CPL.csv', ['Designator','Mid X','Mid Y','Layer','Rotation'],
        [{'Designator':p['Ref'], 'Mid X':p['PosX']+'mm', 'Mid Y':p['PosY']+'mm',
          'Layer':p['Side'].title(), 'Rotation':p['Rot']} for p in positions])
    put(A/'DO_NOT_POPULATE.json', sorted(DNP))
    shutil.copytree(native/'review_gerbers', OUT/'fabrication/gerbers', dirs_exist_ok=True)
    deterministic_zip(OUT/'fabrication/JLCPCB_GERBERS.zip', OUT/'fabrication/gerbers')
    for name in ('FILL_CAP_PLANARIZE_49_VIAS.csv', 'STACKUP_AND_PROCESS.json'):
        shutil.copyfile(W/'current/i32_manufacturing/fabrication'/name, OUT/'fabrication'/name)
    (OUT/'documentation').mkdir(exist_ok=True)
    for src, dst in [('PCB_NETLIST.d356','fabrication/PCB_NETLIST.d356'),
                     ('SCHEMATIC_NETLIST.xml','documentation/SCHEMATIC_NETLIST.xml'),
                     ('REVIEW_SCHEMATIC.pdf','documentation/SCHEMATIC.pdf')]:
        shutil.copyfile(native/src, OUT/dst)
    # The populated STEP is retained only after exact source-tree equivalence.
    shutil.copyfile(OLD/'native_final/REVIEW_COMPONENTS.step', OUT/'documentation/POPULATED_COMPONENTS.step')
    (OUT/'documentation/QUALIFIED_ASSEMBLY_REQUIREMENTS.md').write_text(
        '> Retained physical/process requirements. This package\'s README and procurement BOM '
        'supersede the sourcing counts and source paths in this baseline document.\n\n' +
        (W/'current/i32_manufacturing/ASSEMBLY_AND_ACCEPTANCE.md').read_text())
    shutil.copyfile(W/'current/i32_manufacturing/FIRMWARE_EFFECTIVITY.json', OUT/'FIRMWARE_EFFECTIVITY.json')
    for name in ('README.md', 'ASSEMBLY_AND_ACCEPTANCE.md', 'IDENTITY_ALIASES.md'):
        shutil.copyfile(D/name, OUT/name)
    put(OUT/'PROCUREMENT_SOURCES.json', read(D/'SOURCES.json'))
    shutil.copytree(D/'catalog', OUT/'sourcing_evidence/catalog', dirs_exist_ok=True)
    summary = dict(status='ALL_FACTORY_PARTS_JLC_CATALOG_NATIVE_PACKAGE_COHERENT',
        source_PCB_sha256=sha(CAD/'GR86_CCA_RevB.kicad_pcb'),
        qualified_baseline_PCB_sha256=sha(BASE/'GR86_CCA_RevB.kicad_pcb'),
        metadata_only_fields=list(FIELDS), exact_non_procurement_tree_equivalence=True,
        CAD_files=len(inventory(CAD)), fitted=177, factory=175, local_install=sorted(LOCAL), DNP=sorted(DNP),
        catalog_factory_references=len(factory)-len(requests),
        newly_assigned_original_factory_references=[r['Reference'] for r in redline if r['Reason'] == 'EXACT_CATALOG_ASSIGNMENT_ADDED'],
        withheld_ambiguous_catalog_references=[r['Reference'] for r in redline if r['Reason'] == 'AMBIGUOUS_CATALOG_ASSIGNMENT_WITHHELD'],
        global_sourcing_factory_references=[r['Reference'] for r in requests],
        all_factory_parts_in_JLC_catalog=True, factory_unique_catalog_parts=len({r['LCSC'] for r in rows if r['Reference'] in factory}),
        frozen_exact_bindings=13, native_findings=0, special_vias=49,
        native_filled_physics_exact=True, fabrication_files_equivalent_except_generation_headers=14,
        complete_native_positions_unchanged=True, schematic_nets_unchanged=True,
        simulation_execution='REUSED_QUALIFIED_PHYSICS_NO_NEW_SOLVER_RUN',
        simulation_source_binding='docs/engineering/rvb22/analyses/i32/procurement_redline/METADATA_ONLY_REBIND.json',
        simulation_source_binding_path_base='repository_root',
        populated_STEP='REUSED_EXACT_GEOMETRY_AND_MODELS_FROM_QUALIFIED_BASELINE',
        supplier_acceptance=False, order_ready=False, order_placed=False, physical_tests=0)
    put(OUT/'COHERENCE.json', summary)
    put(D/'CAD_PROPERTY_REDLINE.json', changes)
    files = {str(p.relative_to(OUT)):dict(sha256=sha(p), bytes=p.stat().st_size)
             for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'SOURCE_MANIFEST.json'}
    put(OUT/'SOURCE_MANIFEST.json', dict(schema_version=1, source_PCB_sha256=summary['source_PCB_sha256'], files=files))
    deterministic_zip(ARCHIVE, OUT)
    verify(native)


def verify(native):
    sources = validate_sources()
    verify_cad(sources)
    check_native(native)
    manifest = read(OUT/'SOURCE_MANIFEST.json')
    actual = {str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()}
    assert actual == set(manifest['files']) | {'SOURCE_MANIFEST.json'}
    for name, spec in manifest['files'].items():
        assert sha(OUT/name) == spec['sha256'] and (OUT/name).stat().st_size == spec['bytes'], name
    with zipfile.ZipFile(ARCHIVE) as z:
        assert len(z.namelist()) == len(set(z.namelist())) and set(z.namelist()) == actual
        for name in z.namelist():
            assert z.read(name) == (OUT/name).read_bytes(), name
    bom = csvrows(OUT/'assembly/JLCPCB_BOM.csv')
    cpl = csvrows(OUT/'assembly/JLCPCB_CPL.csv')
    assert len(bom) == len(cpl) == 175
    assert {r['Designator'] for r in bom} == {r['Designator'] for r in cpl} == fitted()-LOCAL
    complete = csvrows(OUT/'assembly/COMPLETE_FITTED_BOM.csv')
    assert complete == csvrows(native/'REVIEW_BOM.csv')
    for row in complete:
        assert row['LCSC'] == sources[row['MPN']]['LCSC']
    for row in bom:
        ref = row['Designator']
        native_row = next(r for r in complete if r['Reference'] == ref)
        assert row['MPN'] == sources[native_row['MPN']]['supplier_mpn']
        assert row['LCSC Part #'] == native_row['LCSC']
    expected_cpl = [{'Designator':p['Ref'], 'Mid X':p['PosX']+'mm', 'Mid Y':p['PosY']+'mm',
                     'Layer':p['Side'].title(), 'Rotation':p['Rot']}
                    for p in csvrows(native/'REVIEW_POSITIONS.csv')]
    assert cpl == expected_cpl, 'CPL coordinate/rotation/side drift'
    assert set(read(OUT/'assembly/DO_NOT_POPULATE.json')) == DNP
    assert csvrows(OUT/'assembly/LOCAL_ASSEMBLY_BOM.csv') == [r for r in complete if r['Reference'] in LOCAL]
    assert read(OUT/'PROCUREMENT_SOURCES.json') == read(D/'SOURCES.json')
    report = dict(status='PASS_SOURCED_NATIVE_PACKAGE', package_sha256=sha(ARCHIVE),
                  package_members=len(actual), **{k:v for k,v in read(OUT/'COHERENCE.json').items() if k != 'status'})
    put(D/'VERIFICATION.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['prepare', 'package', 'verify'])
    ap.add_argument('--native-dir', type=Path, default=D/'native')
    args = ap.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'package':
        package(args.native_dir)
    else:
        verify(args.native_dir)
