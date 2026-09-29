"""Optional installed CLI + real MCP smoke. Findings-only; all outputs external."""
import argparse
import importlib.util
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def main(repo, entry, project_id):
    ROOT, BRIDGE = Path(repo).resolve(), Path(entry).resolve()
    spec = importlib.util.spec_from_file_location('domain_smoke_bridge', BRIDGE)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    Blocked, framework = bridge.Blocked, bridge.framework
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--accept-source-drift', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() or out.is_relative_to(ROOT) or ROOT.is_relative_to(out):
        raise SystemExit('Smoke output must be a new external directory')
    out.mkdir(parents=True)
    commands = []
    packet_exits = {}
    # Prove the installed-package guard rejects altered expected bytes without
    # modifying either the installed framework or the canonical lock file.
    negative = out / 'pin-negative'; negative.mkdir()
    lock = json.loads((BRIDGE.parent / 'framework.lock.json').read_text())
    lock['files'][next(iter(lock['files']))] = '0' * 64
    (negative / 'framework.lock.json').write_text(json.dumps(lock) + '\n')
    try:
        framework(sys.executable, negative)
    except Blocked as exc:
        assert 'Framework bytes differ:' in str(exc)
        (negative / 'result.json').write_text(json.dumps({'rejection': str(exc), 'status': 'PASS'}) + '\n')
    else:
        raise AssertionError('Altered framework lock was accepted')

    def cli(name, *extra, exits=(0,)):
        argv = [sys.executable, str(BRIDGE), name, '--framework-python', sys.executable, *map(str, extra)]
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=300, check=False)
        record = {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
        commands.append(record)
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if p.returncode not in exits:
            raise RuntimeError(str(record))
        return json.loads(p.stdout or p.stderr)

    cli('doctor', exits=(3,))
    more = ['--accept-source-drift'] if args.accept_source_drift else []
    cli('prepare', '--out', out / 'inputs', *more)
    receipt = cli('audit', '--workspace', out / 'inputs', '--out', out / 'cli-run', exits=(1, 3))
    assert receipt['canonical_inputs_unchanged']
    for role in ('requirements', 'electrical', 'interfaces', 'layout', 'manufacturing', 'mechanical'):
        packet = cli('packet', '--run', out / 'cli-run', '--role', role, '--out', out / ('packet-' + role), exits=(0, 2))
        packet_exits[role] = commands[-1]['exit']
        assert packet['session_status'] == 'NOT_RUN'
    cli('mcp-config', '--workspace', out / 'inputs', '--run-root', out / 'mcp-runs', '--out', out / 'mcp.json')
    # Rejected canonical output and duplicate capture must not create/replace inputs.
    cli('prepare', '--out', ROOT / 'forbidden-assurance-run', exits=(2,))
    cli('prepare', '--out', out / 'inputs', exits=(2,))

    transcript = []
    async def exercise():
        params = StdioServerParameters(command=str(Path(sys.executable).with_name('pcb-assure-mcp')),
              args=[], env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PCB_ASSURE_MCP_CONFIG': str(out / 'mcp.json')})
        async with (
            stdio_client(params) as (reader, writer),
            ClientSession(reader, writer) as session,
        ):
            init = await session.initialize()
            assert init.serverInfo.name == 'pcb-design-assurance'
            names = {t.name for t in (await session.list_tools()).tools}
            assert names == {'capabilities', 'doctor', 'validate_project', 'run_assessment',
                             'get_report', 'get_findings', 'get_sources', 'get_requirements', 'get_supported_checks'}
            async def call(name, arguments, error=False):
                result = await session.call_tool(name, arguments)
                transcript.append({'name': name, 'arguments': arguments, 'result': result.model_dump(mode='json')})
                (out / 'mcp-transcript.json').write_text(json.dumps(transcript, indent=2) + '\n')
                assert bool(result.isError) is error
                return json.loads(result.content[0].text) if not error else None
            capabilities = await call('capabilities', {})
            assert capabilities['registered_projects'] == [project_id]
            assert not capabilities['design_write_tools'] and not capabilities['approval_tools']
            await call('doctor', {})
            await call('get_supported_checks', {})
            await call('validate_project', {'project_id': project_id})
            await call('get_sources', {'project_id': project_id})
            await call('get_requirements', {'project_id': project_id})
            audit = await call('run_assessment', {'project_id': project_id})
            report = await call('get_report', {'run_id': audit['run_id']})
            await call('get_findings', {'run_id': audit['run_id']})
            for foreign in ('act-adapter-z1', 'act-effects-jlcpcb', 'gr86'):
                if foreign == project_id:
                    continue
                await call('validate_project', {'project_id': foreign}, error=True)
            await call('get_report', {'run_id': '../escape'}, error=True)
            await call('repair_design', {}, error=True)
            assert report['canonical_inputs_unchanged'] and not report['release_authorized']
            assert report['review_sessions_executed'] == 0
            return {'tools': sorted(names), 'mcp_run_id': audit['run_id'],
                    'snapshot_id': report['snapshot_id'], 'engineering_result': report['overall']}
    result = asyncio.run(exercise())
    native = json.loads((out / 'cli-run/runtime/native/result.json').read_text())
    assert native['status'] == 'BLOCKED', 'Do not silently qualify a new native backend'
    assert all(c['argv'][-1] == '--version' for c in native['commands']), 'Unexpected native design tool execution'
    result.update(native_compatibility='BLOCKED', native_blocker=native.get('blocker'), fresh_native_erc_drc='NOT_RUN')
    # Native session files have appeared after an initially successful seal check
    # on this host. Recheck at the end; never remove the file or reseal the run.
    verifications = []
    for run in (out / 'cli-run', out / 'mcp-runs' / result['mcp_run_id']):
        argv = [sys.executable, '-I', '-m', 'pcb_assure', 'verify-evidence', '--run', str(run)]
        p = subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)
        verifications.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    (out / 'final-integrity.json').write_text(json.dumps(verifications, indent=2) + '\n')
    custody_ok = all(v['exit'] == 0 for v in verifications) and all(v == 0 for v in packet_exits.values())
    result.update(project_id=project_id, integration_smoke='PASS' if custody_ok else 'BLOCKED',
                  transport_checks='PASS', final_custody='PASS' if custody_ok else 'BLOCKED',
                  packet_exits=packet_exits, cli_commands=len(commands), mcp_calls=len(transcript),
                  altered_framework_pin_rejected=True,
                  independent_sessions=0, release_authorized=False,
                  note='Transport/custody success only; retain actual engineering FAIL/BLOCKED gates.')
    (out / 'smoke.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if custody_ok else 3
