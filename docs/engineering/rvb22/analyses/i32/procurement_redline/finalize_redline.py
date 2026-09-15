#!/usr/bin/env python3
"""Verify and aggregate the completed I32 procurement redline; never run hardware."""
from pathlib import Path
import hashlib, json, sys
import numpy as np

D = Path(__file__).resolve().parent
W = D.parents[2]
sys.path.insert(0, str(D))
import apply_redline as a
from restore_waveforms import verify_parts

def read(p):
    return json.loads(p.read_text())

def put(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def bind_unchanged_physics():
    """Compare full native trees, including all models and filled polygons."""
    boards = []
    for name in ('native', 'native_final'):
        b = a.sx.loads((D / name / 'candidate_kicad/GR86_CCA_RevB.kicad_pcb').read_text())
        for f in a.children(b, 'footprint'):
            # Only the documented descriptive clean-up and already-authorized
            # R151 catalogue-field reconciliation may differ after the replay.
            for q in a.children(f, 'descr') + a.children(f, 'tags'):
                f.remove(q)
            for q in list(a.children(f, 'property')):
                if a.props(f)['Reference'] == 'R151' and q[1] == 'LCSC':
                    f.remove(q)
                    continue
                # KiCad regenerates property UUIDs; pad/route UUIDs are retained.
                for z in a.children(q, 'uuid'):
                    q.remove(z)
        boards.append(b)
    assert boards[0] == boards[1], 'Post-replay physical or model mutation'
    rebind = read(D / 'METADATA_ONLY_REBIND.json')
    assert rebind['filled_polygon_geometry_exactly_unchanged']
    return rebind

def main():
    binding = read(D / 'SOURCE_BINDING.json')
    for name, digest in binding['cad_files'].items():
        assert sha(W / 'candidate/cad' / name) == digest, name
    source = binding['source_PCB_sha256']
    rebind = bind_unchanged_physics()
    assert rebind['final_source_PCB_sha256'] == source
    n = read(D / 'native_final/RESULT.json')
    m = read(D / 'manufacturing_audit_final/RESULTS.json')
    bom = read(D / 'MANUFACTURING_RECONCILIATION.json')
    package = read(D / 'PACKAGE_QUALIFICATION.json')
    audit = read(D / 'SOURCE_AUDIT.json')
    mech = read(D / 'mechanics_final/MECHANICAL.json')
    ground = read(D / 'ground_final/GROUND_RETURN_CONTRACT.json')
    returns = read(D / 'filled_returns_final/FILLED_GROUND_CONNECTIVITY.json')
    live = read(D / 'LIVE_JLC_SOURCEABILITY.json')
    for v in (m, bom, package, audit, mech, ground):
        assert v['source_PCB_sha256'] == source
    assert n['status'] == 'NATIVE_OUTPUTS_COMPLETE' and n['inputs_unchanged']
    assert len(n['output_postconditions']) == 13
    assert all(v['pass'] for v in n['output_postconditions'].values())
    assert m['independent_manufacturing_status'] == 'PASS_INTENDED_COPPER_AND_EXPORTS'
    assert all(m[k] == 0 for k in ('native_DRC', 'native_ERC', 'native_parity', 'native_unconnected'))
    assert not m['continuity']['disconnected_pad_nets']
    assert not m['continuity']['padless_components']
    assert not m['netlist']['pad_net_mismatches']
    assert bom['fitted'] == 177 and bom['factory_CPL_rows'] == 175
    assert bom['local_install'] == ['F101', 'U401'] and bom['DNP'] == ['C203', 'R301', 'R306']
    assert bom['frozen_MPN_Cnumber_binding'] and bom['old_frozen_MPNs_in_active_BOM'] == 0
    assert package['changed_refs'] == 13 and package['native_DRC_findings'] == 0
    assert audit['firmware_unchanged_from_base'] and audit['stackup_and_native_rules_unchanged']
    assert len(audit['filled_capped_planarized_vias']) == 49
    assert not mech['interferences']
    assert all(v['pass_allocation'] for v in ground['terms'])
    assert len(returns['rows']) == 23 and all(v['connected_by_actual_filled_ground'] for v in returns['rows'])
    assert live['unique_parts'] == 9 and all(v['isBuyComponent'] == '1' and v['allowPostFlag'] and not v['noBuyReason'] for v in live['rows'])
    s = read(D / 'spice/QUALIFICATION_SUMMARY.json')
    swaps = read(D / 'spice/SWAP_RESULTS.json')
    controls = read(D / 'spice/CONTROL_RESULTS.json')
    assert s['source_PCB_sha256'] == rebind['qualified_source_PCB_sha256']
    assert s['pass'] and len(swaps) == 32 and len(controls) == 6
    assert all(v['completed'] and v['returncode'] == 0 for v in swaps + controls)
    assert s['normal_case_count'] == 17 and s['normal_sequence_ok']
    assert s['reset_margin_V'] >= .01181633 and s['overshoot_margin_V'] >= .02339022
    assert s['VIN_minus_source_min_V'] > -.3 and s['L121_peak_A'] < 2.5
    assert s['superstress_30p08uH_PASS'] and abs(s['high_side_1us_confirmation_V'] - 3.5766084) < 1e-7
    raw = read(D / 'spice/RAW_RECORD_MANIFEST.json')
    assert len(raw['records']) == 38
    for r in raw['records']:
        verify_parts(r)
        assert read(D / 'spice' / r['result_path'])['waveform_sha256'] == r['uncompressed_sha256']
    coarse = read(D / 'thermal/0.5/RESULTS.json')
    fine = read(D / 'thermal/0.25/RESULTS.json')
    for j in (coarse, fine):
        assert j['source']['source_PCB_sha256'] == rebind['qualified_source_PCB_sha256']
        assert j['source']['native_PCB_sha256'] == rebind['qualified_filled_PCB_sha256']
        assert j['release_budget_W'] == 2.940859375
        assert all(abs(v['energy_balance_residual_W']) < 1e-7 for v in j['results'])
    thermal = dict(release_heat_W=fine['release_budget_W'], stacked_80pct_heat_W=fine['stacked_total_W'],
        required_U121_efficiency_at_U151_80pct=fine['required_U121_efficiency_if_U151_exactly_80pct_and_max_leakage'], cases=[])
    for c, f in zip(coarse['results'], fine['results']):
        delta = max(0, f['max_board_C'] - c['max_board_C'])
        thermal['cases'].append(dict(case=f['case'], coarse_board_max_C=c['max_board_C'], fine_board_max_C=f['max_board_C'],
            one_step_allowance_C=delta, board_screen_with_one_step_C=f['max_board_C'] + delta, source_heat_W=f['heat_vector_total_W']))
    screen = max(v['board_screen_with_one_step_C'] for v in thermal['cases'])
    thermal['stacked_board_screen_C'] = screen
    thermal['local_package_screen'] = {}
    for ref, (x, y) in {'U152': (43.6, 4.8), 'U153': (79.1, -3.5)}.items():
        by_case = []
        # Use the worse of both current heat allocations for each local package.
        for name in ('I32_measured_loss_allocation', 'I32_stacked_80pct_sensitivity'):
            vals = []
            for mesh in (.5, .25):
                z = np.load(D / f'thermal/{mesh}/{name}.npz')
                select = (abs(z['x'] - x) <= 1 + mesh / 2) & (abs(z['y'] - y) <= 1.5 + mesh / 2)
                vals.append(float(z['T'][3, select].max()))
            by_case.append(dict(case=name, coarse_C=vals[0], fine_C=vals[1], one_step_C=vals[1] + max(0, vals[1] - vals[0])))
        local = max(v['one_step_C'] for v in by_case)
        peak = max(v[ref]['peak_W'] for v in swaps)
        tj = local + 51 * peak
        assert tj < 130
        thermal['local_package_screen'][ref] = dict(cases=by_case, RthetaJB_allocation_K_W=51,
            peak_dissipation_W=peak, conditional_Tj_screen_C=tj, minimum_TSD_C=130, margin_C=130-tj)
    # Conservative peak-as-RMS allocation, calibrated to the manufacturer's
    # typical 40 C rise at 2.5 A, with copper resistance temperature feedback.
    # This is a conditional screen, not a guaranteed vendor thermal model.
    rise25 = 40 * (s['L121_peak_A'] / 2.5) ** 2
    coil = (screen + rise25 * (1 - .00393 * 25)) / (1 - rise25 * .00393)
    assert coil < 125 and screen < 125
    thermal['L121_conditional_screen'] = dict(peak_as_RMS_A=s['L121_peak_A'], rated_current_A=2.5,
        typical_rise_at_rated_current_C=40, global_board_one_step_C=screen, copper_TC_per_K=.00393,
        allocated_winding_C=coil, rated_max_including_self_rise_C=125, margin_C=125-coil,
        basis='Manufacturer BPCI M00 rated-current definition; typical thermal scaling, not guaranteed measurement or validation.')
    thermal['R156_R169_global_board_to_125C_margin_C'] = 125-screen
    thermal.update(old_board_correlation_trigger_C=112.8829809018675, correlation_trigger_unchanged=True,
        mesh_convergence_proven=False, junction_temperature_proven=False, immediate_air_proven=False,
        physical_tests=0, source_rebind='METADATA_ONLY_REBIND.json')
    put(D / 'THERMAL_RESULTS.json', thermal)
    electrical = {k:v for k,v in s.items() if k not in ('native_CAD_sha256', 'thermal_rating_screen')}
    electrical['component_stress'] = {ref:dict(peak_W=max(v[ref]['peak_W'] for v in swaps),
        whole_record_energy_J=max(v[ref]['energy_J'] for v in swaps)) for ref in ('U152', 'U153', 'R165')}
    electrical.update(control_cases=6, raw_waveforms_preserved=38,
        model_class='Transparent current-mode derivative; not final-source vendor-macromodel or hardware validation',
        final_source_binding='METADATA_ONLY_REBIND.json')
    gates = {
        'native_schematic_ERC': True, 'native_PCB_DRC': True, 'unconnected_pad_net_checks': True,
        'schematic_PCB_reference_value_net_parity': True, 'all_frozen_footprint_package_identities': True,
        'BOM_exact_frozen_MPN_Cnumber_source_binding': True, 'fitted_DNP_local_count_reconciliation': True,
        'CPL_reference_side_XY_rotation_reconciliation': True, 'native_manufacturing_hash_consistency': True,
        'stackup_and_49_special_vias': True, 'I32_native_source_audits': True,
        'fresh_final_procurement_ngspice': True, 'affected_thermal_and_package_desktop_screens': True,
        'live_exact_frozen_JLC_public_purchase_preorder_paths': True}
    final = dict(status='COMPLETE_FROZEN_PROCUREMENT_REDLINE_DESKTOP_VERIFIED', starting_remote_SHA='1c934f9ddd7a1b823e5136484f525485472528f6',
        immutable_pre_redline_CAD_commit='e5ef8425dbe59c99e99eabb75c04342a47b27561', source_PCB_sha256=source,
        filled_PCB_sha256=binding['filled_PCB_sha256'], native_schematic_XML_sha256=binding['native_schematic_XML_sha256'],
        gates=gates, desktop_gates_passed=len(gates), native=dict(ERC=0, DRC=0, unconnected=0, parity=0,
        postconditions=13, CAD_files=157, fitted_models=177, electrical_nets=145, net_bearing_pads=571),
        substitutions=a.SPEC, assembly=bom, electrical=electrical, thermal=thermal,
        mechanics={k:mech[k] for k in ('status','fitted_count','populated_checks','mated_checks','interferences','extra_height_mm','nearest')},
        filled_ground_paths=23, return_allocations={k:ground[k] for k in ('source_to_load_ground_upper_ohm','shared_return_allocation_ohm','C206_to_load_plane_plus_load_barrel_upper_ohm','C206_ground_spreading_allocation_ohm')},
        sourceability=live, metadata_rebind=rebind,
        remaining_supplier_gates=['29 unchanged factory references still need exact LCSC/customer-supplied sourcing assignment; no unrelated substitutes authorized.',
            'L121 catalog manual/wave process and assembly orientation must be accepted by JLC; no authenticated order or capacity reservation performed.',
            'Supplier stackup, minimum finished plating, special-via fill/cap/planarization, stencil and assembly DFM acceptance.'],
        remaining_physical_gates=['First-article populated/mated fit, probe access, C166 edge tolerance and cooling hardware/material acceptance.',
            'Thermal correlation under retained I25 workload and 2.940859375 W budget; unchanged 112.8829809018675 C trigger; U201 immediate air <=85 C and Adafruit 851 local <=60 C at 65 C cabin.',
            'Measure converter losses and package temperatures, particularly L121 self-rise and 125 C parts; verify contact performance and long-term material/fatigue behavior.',
            'Bench startup/brownout/reset/reverse protection, EMC/transient testing, installed vehicle and unit acceptance.'],
        U101_pedigree='Owner accepted #W controlled-manufacturing option downgrade to functional H-grade #PBF; pedigree is not equivalent.',
        firmware='32 adopted source files unchanged; retained genuine 160 MHz recovery build passed 28/28 binary release checks.',
        physical_tests=0, supplier_approval=False, manufacturing_order=False, full_product_qualified=False)
    put(D / 'FINAL_REDLINE_VERIFICATION.json', final)
    print(json.dumps(dict(status=final['status'], gates=len(gates), thermal=thermal), indent=2))

if __name__ == '__main__':
    main()
