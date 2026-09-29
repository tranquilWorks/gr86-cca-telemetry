#!/usr/bin/env python3
"""Shared domain-bound custody/configuration bridge. Engineering checks belong to pcb_assure."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

from types import SimpleNamespace

SCOPES = {
    'gr86-revb-jlcpcb': ('docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad', 'JLCPCB', 'GR86-REVB', '/ASSEMBLY_AND_ACCEPTANCE.md'),
}


def bind(config_dir, repo, project_id):
    if project_id not in SCOPES:
        raise ValueError('Unknown assurance domain')
    HERE, REPO, PROJECT_ID = Path(config_dir).resolve(), Path(repo).resolve(), project_id
    NATIVE_ROOT, PROCESS, PREFIX, PROFILE_SUFFIX = SCOPES[project_id]
    PROCESS_FIELDS = ('layers', 'material', 'thickness_mm', 'copper_oz') + (
        ('assembly_side',) if PROCESS == 'JLCPCB' else ('tool_id', 'registration_method'))
    PROFILE_NOTE = (
        'Source-bound I32 JLC manufacturing context; runtime criteria require controlled source/approval mapping. '
        'Never infer current stock, supplier acceptance or physical qualification from retained package records.'
        if PROCESS == 'JLCPCB' else
        'Selected Z1 process only. Existing process.json contains unmeasured candidates; no approved numeric limits are inferred.')
    ROLES = ('requirements', 'electrical', 'interfaces', 'layout', 'manufacturing', 'mechanical')

    def integration_identity(config_dir):
        entry = config_dir / 'bridge.py'
        return {'shared_sha256': digest(Path(__file__)),
                'entry_sha256': digest(entry) if entry.is_file() else None}


    def verify_run_identity(run):
        if load(inside(run, 'input-manifest.json')).get('project_id') != PROJECT_ID:
            raise Blocked('Foreign project assessment run')


    class Blocked(ValueError):
        pass


    def load(path):
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise Blocked('Duplicate JSON key: ' + key)
                result[key] = value
            return result
        return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                          parse_constant=lambda x: (_ for _ in ()).throw(Blocked('Nonfinite JSON: ' + x)))


    def digest(path):
        h = hashlib.sha256()
        with Path(path).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()


    def write(path, value):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')


    def relative(name):
        if not isinstance(name, str):
            raise Blocked('Expected a relative path string')
        p = PurePosixPath(name)
        if (not name or name == '.' or p.is_absolute() or PureWindowsPath(name).drive
                or '\\' in name or '..' in p.parts or p.as_posix() != name):
            raise Blocked('Unsafe relative path: ' + name)
        return p


    def inside(root, name):
        p = root
        for part in relative(name).parts:
            p = p / part
            if p.is_symlink():
                raise Blocked('Symlink input: ' + name)
        if not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
            raise Blocked('Missing/nonregular input: ' + name)
        return p


    def disjoint(path, *protected):
        original = Path(path).absolute()
        for parent in (original, *original.parents):
            if parent.is_symlink():
                raise Blocked('Symlink output/workspace path')
        target = original.resolve()
        for root in protected:
            root = Path(root).resolve()
            if target.is_relative_to(root) or root.is_relative_to(target):
                raise Blocked('Output/workspace and protected inputs must be disjoint')
        return target


    def new_dir(path, *protected):
        path = disjoint(path, *protected)
        if path.exists():
            raise Blocked('Destination already exists; use a new append-only run')
        path.mkdir(parents=True)
        return path


    def git(repo, *args):
        result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                                text=True, timeout=15, check=False)
        if result.returncode:
            raise Blocked('Git context unavailable: ' + result.stderr.strip())
        return result.stdout.strip()


    def catalog(config_dir=HERE):
        cfg = load(config_dir / 'input-catalog.json')
        if (cfg.get('schema_version') != 1 or cfg.get('project_id') != PROJECT_ID
                or cfg.get('repository') != 'tranquilWorks/gr86-cca-telemetry'
                or cfg.get('native_root') != NATIVE_ROOT
                or cfg.get('board_id') != PREFIX):
            raise Blocked('Unexpected board domain scope')
        sources = cfg.get('sources', [])
        if not sources:
            raise Blocked('Empty source inventory')
        for key in ('id', 'path', 'destination'):
            if len({s[key] for s in sources}) != len(sources):
                raise Blocked('Duplicate source ' + key)
        for s in sources:
            relative(s['path']); relative(s['destination'])
            if s['kind'] not in ('native', 'context') or s['role'] not in (
                    'design', 'firmware', 'requirement', 'source', 'profile', 'interface',
                    'model', 'analysis_input', 'manufacturing'):
                raise Blocked('Unknown source role/kind')
            if s['kind'] == 'native' and not s['path'].startswith(NATIVE_ROOT + '/'):
                raise Blocked('Foreign board source')
            expected = s['path'][len(NATIVE_ROOT + '/'):] if s['kind'] == 'native' else 'sources/' + s['path']
            if s['destination'] != expected or type(s['review_visible']) is not bool:
                raise Blocked('Source destination/visibility contract changed')
            # Context contains baseline history and designer claims. Curate it separately.
            if s['review_visible'] and (s['kind'] != 'native' or s['role'] != 'design'):
                raise Blocked('Uncurated context cannot enter a blind packet')
            if not isinstance(s['discovery_sha256'], str) or len(s['discovery_sha256']) != 64:
                raise Blocked('Missing discovery hash')
        for path in cfg['ecad'].values():
            if path not in {s['destination'] for s in sources}:
                raise Blocked('ECAD entry is not allowlisted')
        return cfg


    def source_state(repo, cfg):
        repo = Path(repo).resolve()
        if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
            raise Blocked('Expected the repository root')
        remote = git(repo, 'remote', 'get-url', 'origin')
        if remote not in ('https://github.com/tranquilWorks/gr86-cca-telemetry.git',
                          'https://github.com/tranquilWorks/gr86-cca-telemetry',
                          'git@github.com:tranquilWorks/gr86-cca-telemetry.git'):
            raise Blocked('Canonical repository identity is not configured on origin')
        observed = {s['path']: digest(inside(repo, s['path'])) for s in cfg['sources']}
        native = repo / cfg['native_root']
        current = set()
        for p in native.rglob('*'):
            if p.is_symlink():
                raise Blocked('Symlink in native inventory')
            if p.is_file():
                # KiCad editor/session files are not design inputs and may change independently.
                if p.name.endswith(('.kicad_prl', '.lck')) or p.name == 'fp-info-cache':
                    continue
                current.add(p.relative_to(repo).as_posix())
        expected = {s['path'] for s in cfg['sources'] if s['kind'] == 'native'}
        if current != expected:
            raise Blocked('Native inventory changed; reconcile the explicit catalog: ' +
                          json.dumps({'new': sorted(current - expected), 'missing': sorted(expected - current)}))
        return {'repository': cfg['repository'], 'root': str(repo),
                'head': git(repo, 'rev-parse', 'HEAD'),
                'branch': git(repo, 'branch', '--show-current'),
                'git_status': git(repo, 'status', '--porcelain'), 'source_hashes': observed,
                'drift': [s['path'] for s in cfg['sources'] if observed[s['path']] != s['discovery_sha256']]}


    def framework(python, config_dir=HERE):
        python = str(Path(python).absolute())
        lock = load(config_dir / 'framework.lock.json')
        probe = "import hashlib,importlib.metadata as m,json,pathlib,sys\nlock=json.load(sys.stdin); d=m.distribution(lock['distribution'])\nassert d.version==lock['version'],'Framework version differs from pin'\nroot=pathlib.Path(d.locate_file('pcb_assure'))\nassert root.is_dir(),'Use the pinned installed wheel, not an editable package'\nactual={p.relative_to(root.parent).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}\nassert actual==set(lock['files']),'Installed framework inventory differs from pin'\nfor name,expected in lock['files'].items():\n p=pathlib.Path(d.locate_file(name)); assert not p.is_symlink(),name\n assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,'Framework bytes differ: '+name\nprint(json.dumps({'version':d.version,'package_root':str(root.resolve()),'files_verified':len(actual)}))\n"
        p = subprocess.run([python, '-I', '-c', probe], input=json.dumps(lock),
                           capture_output=True, text=True, timeout=30, check=False)
        if p.returncode:
            raise Blocked('Pinned framework unavailable or changed: ' + p.stderr.strip()[-1500:])
        return json.loads(p.stdout)


    def projection(cfg, config_dir):
        bypath = {s['path']: s['id'] for s in cfg['sources']}
        obligations = load(config_dir / 'obligations.json')['obligations']
        if not obligations or len({r['id'] for r in obligations}) != len(obligations):
            raise Blocked('Empty/duplicate review obligations')
        records = []
        for item in obligations:
            if not item['source_paths'] or item['role'] not in ROLES:
                raise Blocked('Obligation has no sources or unknown reviewer role')
            records.append({'id': item['id'], 'statement': item['statement'],
                            'approval': 'CANDIDATE', 'approval_record': None,
                            'source_refs': [bypath[p] for p in item['source_paths']],
                            'required_methods': item['required_methods'],
                            'check': {'kind': 'manual', 'observation_key': None, 'unit': None,
                                      'operator': None, 'limit': None, 'expected_mapping': None}})
        return {'schema_version': '1.0', 'requirements': records}


    def hashes(root):
        result = {}
        for p in sorted(Path(root).rglob('*')):
            if p.is_symlink():
                raise Blocked('Symlink in capsule')
            if p.is_file() and p.relative_to(root).as_posix() != 'capsule-seal.json':
                result[p.relative_to(root).as_posix()] = digest(p)
        return result


    def verify_capsule(workspace):
        seal = load(inside(workspace, 'capsule-seal.json'))
        if seal.get('files') != hashes(workspace):
            raise Blocked('Capsule bytes/inventory changed; prepare a new capsule')
        manifest = load(inside(workspace, 'assurance.json'))
        if manifest['project_id'] != PROJECT_ID:
            raise Blocked('Foreign project capsule')
        return load(inside(workspace, 'capture.json'))


    def prepare(repo, out, accept_drift=False, config_dir=HERE):
        cfg = catalog(config_dir)
        before = source_state(repo, cfg)
        if before['drift'] and not accept_drift:
            raise Blocked('Source drift: inspect current local changes, then explicitly use --accept-source-drift; never reset to the discovery commit')
        # All validation precedes output creation. Failures never overwrite a prior run.
        reqs = projection(cfg, config_dir)
        out = new_dir(out, repo)
        artifacts = []
        for s in cfg['sources']:
            source = inside(repo, s['path']); dest = out / s['destination']
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as stream:
                stream.write(source.read_bytes())
            if digest(dest) != before['source_hashes'][s['path']]:
                raise Blocked('Source changed during copy')
            artifacts.append({'id': s['id'], 'path': s['destination'], 'role': s['role'],
                              'review_visible': s['review_visible'], 'sha256': digest(dest)})
        profile = {'schema_version': '1.0', 'process': PROCESS, 'approval': 'CANDIDATE',
                   'source_refs': [s['id'] for s in cfg['sources'] if s['path'].endswith(PROFILE_SUFFIX)],
                   'settings': {}, 'limits': {}, 'design_targets': {},
                   'vendor_stages': {k: 'NOT_RUN' for k in ('profile_conformance', 'package_consistency', 'vendor_preview', 'production_approval')},
                   'notes': PROFILE_NOTE}
        candidate = lambda name: {'id': name, 'approval': 'CANDIDATE', 'approval_record': None, 'source_refs': []}
        runtime = {'schema_version': '1.0', 'sources': [], 'parts': [], 'cases': [], 'rules': [],
                   'assembly': {**candidate(PREFIX + '-ASSEMBLY'), 'variant': cfg['variant'], 'components': []},
                   'bom_file': 'bom.pending.json', 'cpl_file': 'cpl.pending.json',
                   'process_profile': {**candidate(PREFIX + '-PROCESS'), 'process': PROCESS,
                        'settings': {k: None for k in PROCESS_FIELDS}, 'limits': []},
                   'z1': {**candidate(PREFIX + '-Z1'), 'bridges': [], 'envelope': {k: None for k in ('tip_mm', 'angle_deg', 'depth_mm', 'runout_mm', 'registration_mm', 'available_clearance_mm')}},
                   'coverage': []}
        generated = {
            'requirements.json': (reqs, 'requirement'),
            'observations.json': ({'schema_version': '1.0', 'observations': {}}, 'analysis_input'),
            'manufacturing.json': (profile, 'profile'), 'runtime.json': (runtime, 'analysis_input'),
            'bom.pending.json': ({'schema_version': '1.0', 'variant': cfg['variant'], 'components': []}, 'analysis_input'),
            'cpl.pending.json': ({'schema_version': '1.0', 'variant': cfg['variant'], 'units': 'mm', 'rotation_convention': 'UNQUALIFIED', 'origin': 'UNQUALIFIED', 'components': []}, 'analysis_input')}
        for name, (data, role) in generated.items():
            write(out / name, data)
            artifacts.append({'id': name, 'path': name, 'role': role,
                              'review_visible': False, 'sha256': digest(out / name)})
        capture = {'schema_version': 1, 'captured_at': datetime.now(timezone.utc).isoformat(),
                   'source': before, 'discovery_commit': cfg['discovery_commit'],
                   'accepted_drift_for_snapshot_only': accept_drift,
                   'mapping': {s['destination']: s['path'] for s in cfg['sources']},
                   'integration_code': integration_identity(config_dir),
                   'configuration_hashes': {n: digest(config_dir / n) for n in ('input-catalog.json', 'framework.lock.json', 'obligations.json')},
                   'engineering_approval': False, 'independence': 'NOT_ESTABLISHED',
                   'curated_requirement_sources': 'BLOCKED', 'scope_completeness': 'BLOCKED'}
        write(out / 'capture.json', capture)
        artifacts.append({'id': 'capture', 'path': 'capture.json', 'role': 'analysis_input', 'review_visible': False, 'sha256': digest(out / 'capture.json')})
        write(out / 'assurance.json', {'schema_version': '1.0', 'project_id': cfg['project_id'],
              'board_id': cfg['board_id'], 'variant': cfg['variant'], 'lifecycle': 'ONBOARDED',
              'framework_version': '0.2.0', 'artifacts': artifacts, 'ecad': cfg['ecad'],
              'requirements_file': 'requirements.json', 'observations_file': 'observations.json',
              'manufacturing_profile': 'manufacturing.json', 'runtime_file': 'runtime.json',
              'policy': {'findings_only': True, 'canonical_writes': False, 'supplier_uploads': False, 'hardware_execution': False}})
        after = source_state(repo, cfg)
        if before['source_hashes'] != after['source_hashes'] or before['head'] != after['head']:
            raise Blocked('Repository changed during capture; discard this incomplete capsule')
        write(out / 'capsule-seal.json', {'schema_version': 1, 'files': hashes(out)})
        return {'capsule': str(out), 'source_files': len(cfg['sources']), 'canonical_inputs_unchanged': True,
                'engineering_result': 'BLOCKED', 'meaning': 'ONBOARDED identifies this explicit local scope only; no criteria, review or board approval.'}


    def command(python, args, *, timeout=300):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.run([str(Path(python).absolute()), '-I', '-m', 'pcb_assure', *args],
                           capture_output=True, text=True, timeout=timeout, env=env, check=False)
        return {'argv': [str(Path(python).absolute()), '-I', '-m', 'pcb_assure', *args],
                'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


    def assess(repo, workspace, out, python, config_dir=HERE):
        workspace = disjoint(workspace, repo)
        capture = verify_capsule(workspace)
        cfg = catalog(config_dir); before = source_state(repo, cfg)
        if capture['configuration_hashes'] != {n: digest(config_dir / n) for n in ('input-catalog.json', 'framework.lock.json', 'obligations.json')}:
            raise Blocked('Integration configuration changed since capture; use a new capsule')
        if capture.get('integration_code') != integration_identity(config_dir):
            raise Blocked('Integration code changed or was not bound; use a new capsule')
        if before['source_hashes'] != capture['source']['source_hashes']:
            raise Blocked('Canonical inputs changed since capture; use a new capsule')
        pin = framework(python, config_dir)
        out = disjoint(out, repo, workspace, Path(pin['package_root']))
        if out.exists() or out.with_name(out.name + '.bridge.json').exists():
            raise Blocked('Run destination already exists')
        validation = command(python, ['validate', '--project', str(workspace)])
        if validation['exit']:
            raise Blocked('Shared project validation failed: ' + validation['stderr'])
        run = command(python, ['audit', '--project', str(workspace), '--out', str(out)])
        after = source_state(repo, cfg)
        if before['source_hashes'] != after['source_hashes'] or before['head'] != after['head']:
            raise Blocked('Canonical inputs changed during assessment')
        verify_capsule(workspace)
        evidence = command(python, ['verify-evidence', '--run', str(out)]) if run['exit'] in (0, 1, 3) else None
        receipt = {'schema_version': 1, 'framework': pin, 'validation': validation, 'audit': run,
                   'evidence_verification': evidence, 'canonical_inputs_unchanged': True,
                   'review_sessions_executed': 0, 'engineering_approval': False}
        # Never modify the sealed framework run; custody receipt is a separate sibling.
        write(out.with_name(out.name + '.bridge.json'), receipt)
        if run['exit'] not in (0, 1, 3) or not evidence or evidence['exit']:
            return receipt, 2
        return receipt, 1 if run['exit'] == 1 else 3


    def mcp_config(repo, workspace, run_root, out):
        workspace = disjoint(workspace, repo); verify_capsule(workspace)
        run_root = disjoint(run_root, repo, workspace)
        out = disjoint(out, repo, workspace, run_root)
        write(out, {'schema_version': '1.0', 'projects': {PROJECT_ID: str(workspace)}, 'run_root': str(run_root)})
        return {'config': str(out), 'projects': [PROJECT_ID], 'global_configuration_changed': False}


    def main(argv=None):
        parser = argparse.ArgumentParser(description=__doc__)
        sub = parser.add_subparsers(dest='command', required=True)
        for name in ('doctor', 'prepare', 'audit', 'packet', 'mcp-config'):
            p = sub.add_parser(name)
            p.add_argument('--repo', type=Path, default=REPO)
            p.add_argument('--framework-python', default=sys.executable)
            if name in ('prepare', 'audit', 'packet', 'mcp-config'):
                p.add_argument('--out', type=Path, required=True)
            if name in ('audit', 'mcp-config'):
                p.add_argument('--workspace', type=Path, required=True)
            if name == 'prepare':
                p.add_argument('--accept-source-drift', action='store_true')
            if name == 'packet':
                p.add_argument('--run', type=Path, required=True); p.add_argument('--role', choices=ROLES, required=True)
            if name == 'mcp-config':
                p.add_argument('--run-root', type=Path, required=True)
        args = parser.parse_args(argv)
        repo = args.repo.resolve()
        try:
            if args.command == 'prepare':
                value = prepare(repo, args.out, args.accept_source_drift); code = 0
            elif args.command == 'audit':
                value, code = assess(repo, args.workspace, args.out, args.framework_python)
            elif args.command == 'packet':
                pin = framework(args.framework_python)
                run = disjoint(args.run, repo); out = disjoint(args.out, repo, run, Path(pin['package_root']))
                verify_run_identity(run)
                value = command(args.framework_python, ['prepare-review', '--run', str(run), '--role', args.role, '--out', str(out)])
                code = value['exit']
                value.update(session_status='NOT_RUN', independence='NOT_ESTABLISHED', requirements_curation='BLOCKED')
            elif args.command == 'mcp-config':
                value = mcp_config(repo, args.workspace, args.run_root, args.out); code = 0
            else:
                cfg = catalog(); state = source_state(repo, cfg); pin = framework(args.framework_python)
                value = {'integration_checks': 'PASS', 'framework': pin, 'source': state,
                         'engineering_readiness': 'BLOCKED', 'independent_review': 'BLOCKED',
                         'held_out_qualification': 'BLOCKED', 'criterion_mapping': 'CANDIDATE'}; code = 3
            print(json.dumps(value, indent=2, allow_nan=False)); return code
        except (Blocked, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            print(json.dumps({'execution': 'BLOCKED', 'engineering_result': 'BLOCKED', 'error': str(exc),
                              'engineering_approval': False}), file=sys.stderr)
            return 2

    return SimpleNamespace(**{k: v for k, v in locals().items() if callable(v) or k in ('HERE', 'REPO', 'PROJECT_ID', 'ROLES')})
