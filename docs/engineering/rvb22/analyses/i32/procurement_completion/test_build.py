"""Regression checks for wrong parts and silent manufacturing-file drift."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build


class ProcurementTests(unittest.TestCase):
    def changed_sources_rejected(self, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            data = copy.deepcopy(build.read(build.D/'SOURCES.json'))
            mutate(data['parts'])
            build.put(target/'SOURCES.json', data)
            (target/'catalog').symlink_to(build.D/'catalog', target_is_directory=True)
            with patch.object(build, 'D', target), self.assertRaises(AssertionError):
                build.validate_sources()

    def test_catalog_code_cannot_select_another_value(self):
        self.changed_sources_rejected(lambda p: p['GCM188R71C105KA64D'].update(LCSC='C85864'))

    def test_alias_url_cannot_approve_unrelated_part(self):
        self.changed_sources_rejected(lambda p: p['GCM188R71C105KA64D'].update(
            LCSC='C85864', supplier_mpn='GCM188R71H104KA57D',
            identity='DOCUMENTED_FORMAT_ALIAS', alias_evidence='https://www.murata.com/'))

    def test_frozen_part_cannot_be_downgraded_to_unassigned(self):
        self.changed_sources_rejected(lambda p: p['PLT1206Z5051LBTS'].update(
            LCSC='', route='GLOBAL_SOURCE_REQUEST', status='SUPPLIER_QUOTE_REQUIRED'))

    def test_unknown_part_cannot_enter_registry(self):
        self.changed_sources_rejected(lambda p: p.update(UNQUALIFIED=dict(p['GCM188R71C105KA64D'])))

    def test_factory_part_cannot_bypass_catalog_through_local_route(self):
        self.changed_sources_rejected(lambda p: p['GCM188R71C105KA64D'].update(
            LCSC='', route='LOCAL_INSTALL', status='SUPPLIER_QUOTE_REQUIRED'))

    def test_only_generation_headers_ignored_in_fabrication(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'test.gtl'
            p.write_text('%TF.CreationDate,old*%\nX001Y002D01*\n')
            initial = build.fabrication_content(p)
            p.write_text('%TF.CreationDate,new*%\nX001Y002D01*\n')
            self.assertEqual(initial, build.fabrication_content(p))
            p.write_text('%TF.CreationDate,new*%\nX001Y003D01*\n')
            self.assertNotEqual(initial, build.fabrication_content(p))

    def test_job_stackup_not_erased_with_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'test.gbrjob'
            data = {'Header': {'CreationDate':'old', 'GenerationSoftware':{'Version':'9.0.9'}},
                    'GeneralSpecs': {'LayerNumber':4}}
            build.put(p, data)
            initial = build.fabrication_content(p)
            data['GeneralSpecs']['LayerNumber'] = 2
            build.put(p, data)
            self.assertNotEqual(initial, build.fabrication_content(p))


if __name__ == '__main__':
    unittest.main()
