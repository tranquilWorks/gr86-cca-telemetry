"""Custody/security boundaries exercised with synthetic temporary Git repositories."""
import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('gr86_assurance_bridge', ROOT / 'assurance/bridge.py')
BRIDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BRIDGE)


class AssuranceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repository'; self.repo.mkdir()
        self.config = self.base / 'config'; self.config.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'remote', 'add', 'origin',
                        'https://github.com/tranquilWorks/gr86-cca-telemetry.git'], check=True)
        sources = []
        for i, name in enumerate(('board.kicad_pro', 'board.kicad_sch', 'board.kicad_pcb')):
            path = self.repo / 'docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('SYNTHETIC CUSTODY TEST ONLY: ' + name)
            sources.append({'id': f'source-{i}', 'path': 'docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad/' + name,
                            'destination': name, 'role': 'design', 'kind': 'native',
                            'review_visible': True, 'discovery_sha256': BRIDGE.digest(path)})
        self.cfg = {'schema_version': 1, 'project_id': 'gr86-revb-jlcpcb', 'board_id': 'GR86-REVB',
                    'variant': 'SYNTHETIC_TEST', 'repository': 'tranquilWorks/gr86-cca-telemetry',
                    'discovery_commit': 'synthetic', 'native_root': 'docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad',
                    'ecad': dict(zip(('project', 'schematic', 'pcb'), [s['destination'] for s in sources])),
                    'sources': sources}
        self.save_config()
        self.write(self.config / 'framework.lock.json', {'fixture': 'not an installed framework'})
        self.write(self.config / 'obligations.json', {'obligations': [{'id': 'TEST', 'role': 'requirements',
                  'statement': 'Synthetic routing obligation only', 'source_paths': [sources[0]['path']],
                  'required_methods': ['inspection']}]})
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Test', '-c',
                        'user.email=test@example.invalid', 'commit', '-qm', 'synthetic fixture'], check=True)

    def write(self, path, value):
        path.write_text(json.dumps(value))

    def save_config(self):
        self.write(self.config / 'input-catalog.json', self.cfg)

    def prepare(self, **kw):
        return BRIDGE.prepare(self.repo, self.base / 'capsule', config_dir=self.config, **kw)

    def test_capture_is_byte_exact_and_no_approval(self):
        before = BRIDGE.source_state(self.repo, self.cfg)
        value = self.prepare()
        capture = BRIDGE.verify_capsule(self.base / 'capsule')
        self.assertEqual(before['source_hashes'], capture['source']['source_hashes'])
        self.assertEqual(before, BRIDGE.source_state(self.repo, self.cfg))
        self.assertTrue(value['canonical_inputs_unchanged'])
        manifest = BRIDGE.load(self.base / 'capsule/assurance.json')
        self.assertFalse(manifest['policy']['canonical_writes'])
        self.assertEqual(value['engineering_result'], 'BLOCKED')
        reqs = BRIDGE.load(self.base / 'capsule/requirements.json')['requirements']
        self.assertEqual(reqs[0]['approval'], 'CANDIDATE')
        self.assertIsNone(reqs[0]['approval_record'])

    def test_existing_destination_never_overwritten(self):
        self.prepare()
        seal = BRIDGE.digest(self.base / 'capsule/capsule-seal.json')
        with self.assertRaisesRegex(BRIDGE.Blocked, 'already exists'): self.prepare()
        self.assertEqual(seal, BRIDGE.digest(self.base / 'capsule/capsule-seal.json'))

    def test_source_drift_requires_explicit_capture_and_is_not_approval(self):
        source = self.repo / self.cfg['sources'][0]['path']; source.write_text('OWNER NEWER CONTENT')
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Source drift'): self.prepare()
        self.assertFalse((self.base / 'capsule').exists())
        self.prepare(accept_drift=True)
        capture = BRIDGE.verify_capsule(self.base / 'capsule')
        self.assertEqual(capture['source']['drift'], [self.cfg['sources'][0]['path']])
        self.assertFalse(capture['engineering_approval'])
        self.assertEqual(source.read_text(), 'OWNER NEWER CONTENT')

    def test_new_native_input_not_silently_excluded(self):
        (self.repo / 'docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad/child.kicad_sch').write_text('new hierarchical sheet')
        with self.assertRaisesRegex(BRIDGE.Blocked, 'inventory changed'): self.prepare(accept_drift=True)

    def test_known_editor_cache_not_a_design_input(self):
        (self.repo / 'docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad/board.kicad_prl').write_text('local editor state')
        self.prepare()
        self.assertNotIn('board.kicad_prl', BRIDGE.hashes(self.base / 'capsule'))

    def test_missing_input_fails_before_output(self):
        (self.repo / self.cfg['sources'][0]['path']).unlink()
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Missing'): self.prepare()
        self.assertFalse((self.base / 'capsule').exists())

    def test_input_symlink_refused(self):
        source = self.repo / self.cfg['sources'][0]['path']; raw = source.read_bytes()
        source.unlink(); target = self.base / 'outside'; target.write_bytes(raw); source.symlink_to(target)
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Symlink'): self.prepare()

    def test_output_inside_or_above_repository_refused(self):
        for out in (self.repo / 'audit', self.repo, self.base):
            with self.subTest(out=out), self.assertRaisesRegex(BRIDGE.Blocked, 'disjoint'):
                BRIDGE.prepare(self.repo, out, config_dir=self.config)

    def test_output_symlink_parent_refused(self):
        target = self.base / 'real'; target.mkdir(); alias = self.base / 'alias'; alias.symlink_to(target)
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Symlink'):
            BRIDGE.prepare(self.repo, alias / 'new', config_dir=self.config)

    def test_tampered_capsule_refused(self):
        self.prepare(); (self.base / 'capsule/board.kicad_pcb').write_text('tampered')
        with self.assertRaisesRegex(BRIDGE.Blocked, 'bytes/inventory changed'):
            BRIDGE.verify_capsule(self.base / 'capsule')

    def test_extra_file_named_like_nested_seal_refused(self):
        self.prepare(); p = self.base / 'capsule/foreign'; p.mkdir()
        (p / 'capsule-seal.json').write_text('must not bypass inventory')
        with self.assertRaises(BRIDGE.Blocked): BRIDGE.verify_capsule(self.base / 'capsule')

    def test_duplicate_json_and_nonfinite_refused(self):
        path = self.base / 'bad.json'
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            path.write_text(value)
            with self.subTest(value=value), self.assertRaises(BRIDGE.Blocked): BRIDGE.load(path)

    def test_traversal_absolute_and_duplicate_catalog_refused(self):
        original = copy.deepcopy(self.cfg)
        for name in ('../outside', '/absolute', 'C:\\outside', 'x/../y'):
            self.cfg = copy.deepcopy(original); self.cfg['sources'][0]['path'] = name; self.save_config()
            with self.subTest(name=name), self.assertRaises(BRIDGE.Blocked): BRIDGE.catalog(self.config)
        self.cfg = copy.deepcopy(original); self.cfg['sources'].append(self.cfg['sources'][0]); self.save_config()
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Duplicate'): BRIDGE.catalog(self.config)

    def test_uncurated_context_cannot_enter_blind_packet(self):
        source = self.cfg['sources'][0]; source.update(kind='context', destination='sources/' + source['path'])
        self.save_config()
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Uncurated'): BRIDGE.catalog(self.config)

    def test_foreign_repository_identity_rejected(self):
        subprocess.run(['git', '-C', str(self.repo), 'remote', 'set-url', 'origin',
                        'https://github.com/example/unrelated.git'], check=True)
        with self.assertRaisesRegex(BRIDGE.Blocked, 'identity'): self.prepare()

    def test_mcp_config_has_only_gr86_and_external_paths(self):
        self.prepare(); path = self.base / 'mcp.json'
        BRIDGE.mcp_config(self.repo, self.base / 'capsule', self.base / 'runs', path)
        value = BRIDGE.load(path)
        self.assertEqual(set(value['projects']), {'gr86-revb-jlcpcb'})
        self.assertEqual(value['projects']['gr86-revb-jlcpcb'], str(self.base / 'capsule'))
        with self.assertRaisesRegex(BRIDGE.Blocked, 'disjoint'):
            BRIDGE.mcp_config(self.repo, self.base / 'capsule', self.repo / 'runs', self.base / 'other.json')

    def test_changed_configuration_blocks_assessment_before_tool_execution(self):
        self.prepare()
        self.write(self.config / 'framework.lock.json', {'changed': 'after capture'})
        with self.assertRaisesRegex(BRIDGE.Blocked, 'configuration changed'):
            BRIDGE.assess(self.repo, self.base / 'capsule', self.base / 'run',
                          '/no/interpreter/should/run', config_dir=self.config)
        self.assertFalse((self.base / 'run').exists())

    def test_changed_source_blocks_assessment_before_tool_execution(self):
        self.prepare()
        (self.repo / self.cfg['sources'][0]['path']).write_text('newer source after capture')
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Canonical inputs changed'):
            BRIDGE.assess(self.repo, self.base / 'capsule', self.base / 'run',
                          '/no/interpreter/should/run', config_dir=self.config)
        self.assertFalse((self.base / 'run').exists())


    def test_foreign_board_and_project_scope_rejected(self):
        for key, value in (('board_id', 'ACT-EFFECTS'), ('project_id', 'act-effects-jlcpcb'),
                           ('native_root', 'adapter/ecad')):
            with self.subTest(key=key):
                original = self.cfg[key]; self.cfg[key] = value; self.save_config()
                with self.assertRaisesRegex(BRIDGE.Blocked, 'scope'): self.prepare()
                self.cfg[key] = original; self.save_config()

    def test_changed_entry_identity_blocks_before_execution(self):
        self.prepare()
        (self.config / 'bridge.py').write_text('changed integration code')
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Integration code changed'):
            BRIDGE.assess(self.repo, self.base / 'capsule', self.base / 'run', '/missing/python', self.config)
        self.assertFalse((self.base / 'run').exists())

    def test_foreign_packet_run_rejected(self):
        run = self.base / 'run'; run.mkdir()
        (run / 'input-manifest.json').write_text('{"project_id":"act-adapter-z1"}')
        with self.assertRaisesRegex(BRIDGE.Blocked, 'Foreign project'): BRIDGE.verify_run_identity(run)

    def test_jlc_candidates_do_not_import_z1_or_numeric_limits(self):
        self.prepare(); capsule = self.base / 'capsule'
        profile = BRIDGE.load(capsule / 'manufacturing.json')
        runtime = BRIDGE.load(capsule / 'runtime.json')
        self.assertEqual(profile['process'], 'JLCPCB')
        self.assertEqual(profile['approval'], 'CANDIDATE')
        self.assertEqual(profile['limits'], {})
        self.assertEqual(runtime['process_profile']['settings'], dict.fromkeys(
            ('layers', 'material', 'thickness_mm', 'copper_oz', 'assembly_side')))
        self.assertEqual(runtime['sources'], [])
        self.assertEqual(runtime['z1']['approval'], 'CANDIDATE')
        self.assertEqual(runtime['z1']['bridges'], [])

    def test_models_and_designer_metadata_require_packet_curation(self):
        for role in ('model', 'analysis_input'):
            self.cfg['sources'][0]['role'] = role; self.save_config()
            with self.assertRaisesRegex(BRIDGE.Blocked, 'Uncurated'): self.prepare()

    def test_current_catalog_retains_entire_native_and_bound_firmware_scope(self):
        cfg = BRIDGE.catalog()
        state = BRIDGE.source_state(ROOT, cfg)
        self.assertEqual(state['drift'], [])
        self.assertEqual(len([s for s in cfg['sources'] if s['kind'] == 'native']), 156)
        self.assertEqual(len([s for s in cfg['sources'] if s['role'] == 'firmware']), 32)
        self.assertFalse(any(s['review_visible'] for s in cfg['sources'] if s['role'] != 'design'))
        pcb = ROOT / cfg['native_root'] / cfg['ecad']['pcb']
        self.assertIn('(version 20241229)', pcb.read_text()[:80])
        self.assertTrue(all(s['path'].startswith(cfg['native_root'] + '/')
                            for s in cfg['sources'] if s['kind'] == 'native'))


if __name__ == '__main__':
    unittest.main()
