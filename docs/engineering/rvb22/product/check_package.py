#!/usr/bin/env python3
"""Check the delivered package itself; no CI, network, source changes or hardware."""
import argparse
import csv
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch
import build_package as b


def verify(path: Path, native: Path) -> dict:
    checks = {}
    with zipfile.ZipFile(path) as z:
        manifest = json.loads(z.read('SHA256SUMS.json'))
        checks['every_member_manifested'] = set(z.namelist()) == set(manifest) | {'SHA256SUMS.json'}
        checks['every_member_hash_matches'] = all(hashlib.sha256(z.read(n)).hexdigest() == sha for n, sha in manifest.items())
        read_csv = lambda n: list(csv.DictReader(io.StringIO(z.read(n).decode())))
        full = read_csv('assembly/COMPLETE_FITTED_BOM.csv')
        factory = read_csv('assembly/JLCPCB_BOM.csv')
        cpl = read_csv('assembly/JLCPCB_CPL.csv')
        manual = read_csv('assembly/LOCAL_ASSEMBLY_BOM.csv')
        refs = lambda rows, key: {r[key] for r in rows}
        checks['complete_population_153'] = len(full) == len(refs(full, 'Reference')) == 153
        checks['factory_BOM_CPL_one_to_one_151'] = len(factory) == len(cpl) == 151 and refs(factory, 'Designator') == refs(cpl, 'Designator')
        checks['manual_parts_retained_not_machine_placed'] = refs(manual, 'Reference') == b.MANUAL and not (b.MANUAL & refs(factory, 'Designator'))
        checks['DNP_excluded'] = set(json.loads(z.read('assembly/DO_NOT_POPULATE.json'))) == b.DNP and not (b.DNP & refs(full, 'Reference'))
        by_ref = {r['Reference']: r for r in full}
        checks['critical_MPNs_match'] = all(by_ref[ref]['MPN'] == mpn for ref, mpn in {
            'U121': 'LM5164QDDARQ1', 'R155': 'TNPU060311K8HWEA00',
            'R156': 'TNPU06034K99HWEA00', 'R158': 'WSLP0603R0820FEA', 'C206': 'T598X477M006ATE025'}.items())
        vias = read_csv('fabrication/FILL_CAP_PLANARIZE_49_VIAS.csv')
        checks['via_fill_unique_49'] = len(vias) == len(refs(vias, 'UUID')) == 49
        sourcing = read_csv('assembly/SOURCING_REQUIRED.csv')
        checks['sourcing_gaps_exposed_14'] = len(sourcing) == 14 and refs(sourcing, 'Reference') == {r['Designator'] for r in factory if not r['LCSC Part #']}
        with zipfile.ZipFile(io.BytesIO(z.read('fabrication/JLCPCB_GERBERS.zip'))) as fab:
            checks['standalone_fab_archive_14_exact_files'] = len(fab.namelist()) == 14 and all(fab.read(n) == z.read('fabrication/gerbers/' + n) for n in fab.namelist())
        state = json.loads(z.read('PACKAGE_VERIFICATION.json'))
        checks['qualification_not_faked'] = state['physical_tests_performed'] == 0 and state['full_product_qualified'] is False and state['automatic_turnkey_PCBA_order_ready'] is False
        checks['current_PCB_identity'] = b.digest(z.read('editable_source/cad/GR86_CCA_RevB.kicad_pcb')) == b.PCB_SHA
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bad = root / 'wrong.zip'; bad.write_bytes(b'not the controlled native artifact')
        try:
            b.build(bad, root / 'must-not-exist.zip')
        except ValueError:
            checks['wrong_native_archive_rejected'] = not (root / 'must-not-exist.zip').exists()
        else:
            checks['wrong_native_archive_rejected'] = False
        altered = root / 'candidate/cad/GR86_CCA_RevB.kicad_pcb'
        altered.parent.mkdir(parents=True); altered.write_text('(kicad_pcb)')
        try:
            with patch.object(b, 'W', root):
                b.build(native, root / 'bad-source.zip')
        except ValueError:
            checks['changed_PCB_rejected'] = not (root / 'bad-source.zip').exists()
        else:
            checks['changed_PCB_rejected'] = False
        existing = root / 'existing.zip'; existing.write_bytes(b'keep')
        try:
            b.archive({'test': b'new'}, existing)
        except ValueError:
            checks['existing_output_preserved'] = existing.read_bytes() == b'keep'
        else:
            checks['existing_output_preserved'] = False
    if not all(checks.values()):
        raise ValueError('Failed package checks: ' + str([k for k, v in checks.items() if not v]))
    return {'passed': len(checks), 'checks': checks, 'physical_testing': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--native-zip', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(verify(a.package, a.native_zip), indent=2))
