#!/usr/bin/env python3
"""Independently verify every release ZIP member against its source manifest."""
from pathlib import Path
from zipfile import ZipFile
import csv, hashlib, io, json

D = Path(__file__).resolve().parent
W = D.parents[2]
OUT = W / 'current/i32_manufacturing'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    archive = W / 'product/GR86_I32_PROCUREMENT_REDLINE.zip'
    checks = {}
    with ZipFile(archive) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        m = json.loads(z.read('SOURCE_MANIFEST.json'))
        assert set(names) == set(m['files']) | {'SOURCE_MANIFEST.json'}
        for name, item in m['files'].items():
            data = z.read(name)
            assert digest(data) == item['sha256'] and len(data) == item['bytes'], name
            assert data == (OUT / name).read_bytes(), name
        assert z.read('SOURCE_MANIFEST.json') == (OUT / 'SOURCE_MANIFEST.json').read_bytes()
        checks['every_unique_member_manifested_and_hash_matched'] = True
        cad = {str(p.relative_to(W / 'candidate/cad')):digest(p.read_bytes()) for p in (W / 'candidate/cad').rglob('*') if p.is_file()}
        assert len(cad) == 157
        for name, sha in cad.items():
            assert digest(z.read('editable_source/cad/' + name)) == sha
        checks['all_157_current_CAD_inputs_exact'] = True
        def rows(name):
            return list(csv.DictReader(io.StringIO(z.read('assembly/' + name).decode())))
        fitted, bom, cpl, local = [rows(name) for name in ('COMPLETE_FITTED_BOM.csv','JLCPCB_BOM.csv','JLCPCB_CPL.csv','LOCAL_ASSEMBLY_BOM.csv')]
        assert len(fitted) == 177 and len(bom) == len(cpl) == 175 and len(local) == 2
        assert {r['Designator'] for r in bom} == {r['Designator'] for r in cpl}
        assert {r['Reference'] for r in local} == {'F101','U401'}
        assert {r['Reference'] for r in fitted} == {r['Designator'] for r in bom} | {'F101','U401'}
        dnp = set(json.loads(z.read('assembly/DO_NOT_POPULATE.json')))
        assert dnp == {'C203','R301','R306'} and not dnp & {r['Reference'] for r in fitted}
        checks['177_fitted_175_factory_two_local_three_DNP'] = True
        assert len(rows('SOURCING_REQUIRED.csv')) == 29
        checks['29_unchanged_unassigned_sources_explicit'] = True
        with ZipFile(io.BytesIO(z.read('fabrication/JLCPCB_GERBERS.zip'))) as g:
            assert len(g.namelist()) == len(set(g.namelist())) == 14
            for name in g.namelist():
                assert g.read(name) == z.read('fabrication/gerbers/' + name)
        checks['standalone_Gerbers_14_exact_members'] = True
    result = dict(status='PASS_CURRENT_I32_PACKAGE_HASH_AND_POPULATION_BINDING', source_PCB_sha256=m['source_PCB_sha256'],
        filled_PCB_sha256=m['filled_PCB_sha256'], package_file=archive.name, package_sha256=digest(archive.read_bytes()),
        package_members=len(names), current_source_files=157, fitted_parts=177, factory_placement_rows=175,
        local_assembly_parts=['F101','U401'], DNP=sorted(dnp), filled_capped_vias=49,
        unassigned_factory_LCSC_references=m['unchanged_unassigned_refs'], checks=checks,
        full_engineering_verification='../analyses/i32/procurement_redline/FINAL_REDLINE_VERIFICATION.json',
        supplier_acceptance=False, physical_tests_performed=0, manufacturing_order_placed=False,
        automatic_turnkey_PCBA_order_ready=False, full_product_qualified=False,
        older_verification_preserved='../analyses/i32/procurement_redline/history/pre_redline/product/PACKAGE_VERIFICATION.json')
    (W / 'product/PACKAGE_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','package_sha256','package_members','checks')},indent=2))

if __name__ == '__main__':
    main()
