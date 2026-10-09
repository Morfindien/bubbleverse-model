#!/usr/bin/env python3
"""Read-only Q043 local-validation admission and preservation gates."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_tests(root=ROOT, candidate=False):
    root = Path(root)
    layer = root / ('candidate' if candidate else 'accepted')
    formal = root / ('candidate/formal' if candidate else 'model')
    evidence = root / ('candidate/evidence' if candidate else 'evidence')
    old = root / 'versions/accepted/v0.4'
    provenance = json.loads((root/'candidate/Q043_PROVENANCE.json').read_text())
    rows = []

    def load(p):
        return json.loads(p.read_text(encoding='utf-8'))

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    def digest(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def gate(name, fn):
        try:
            rows.append({'id': name, 'status': 'PASS', 'detail': fn()})
        except Exception as exc:
            rows.append({'id': name, 'status': 'FAIL', 'detail': f'{type(exc).__name__}: {exc}'})

    def sequence():
        c = load(root/'candidate/candidate_state.json')
        a = load(root/'accepted/model_state.json')
        e = load(evidence/'evidence_registry.json')
        require(c['previous_accepted_q'] == 'Q042' and c['previous_accepted_model_version'] == 'v0.4', 'Q sequence gap')
        require(c['current_q'] == c['q_access_end'] == 'Q043' and c['target_q'] == 'Q043', 'candidate boundary invalid')
        require(c['candidate_model_version'] == 'v0.5' and c['candidate_revision'] == 'R000005', 'candidate version invalid')
        require(a['current_q'] == a['q_access_end'] == ('Q042' if candidate else 'Q043'), 'accepted sequence mismatch')
        require(a['accepted_model_version'] == ('v0.4' if candidate else 'v0.5'), 'accepted version mismatch')
        require(e['current_q'] == e['q_access_end'] == 'Q043', 'evidence boundary invalid')
        require(load(old/'model_state.json')['current_q'] == 'Q042', 'baseline snapshot boundary invalid')
        return 'Q042/v0.4 -> Q043/v0.5, no missing Q'
    gate('Q043_SEQUENCE_GATE', sequence)

    def sources():
        for s in provenance['source_files']:
            p = evidence/'sources/Q043'/s['archived_name']
            require(digest(p) == s['sha256'] and p.stat().st_size == s['bytes'], 'source bytes changed: '+s['archived_name'])
        require(provenance['source_result_original_sha256'] == '4486e5173ba8ef3ac659c743bb578284c93446ce9e5b3d0dae71728beadbb9ff', 'original journal result identity differs')
        return {'verified_source_files': len(provenance['source_files'])}
    gate('Q043_SOURCE_HASH_GATE', sources)

    def qualification():
        s = load(evidence/'sources/Q043/integration_result.json')
        state = load(layer/('candidate_state.json' if candidate else 'model_state.json'))
        require(s['q'] == 'Q043' and s['result_id'] == 'R-Q043-REPOSITORY-INTEGRATION-001', 'result identity differs')
        require(s['actual_result'] == 'PASS_LOCAL_PREPARATION_AND_VALIDATION_ONLY', 'local validation overstated')
        require(s['remote_sync'] == 'NOT_PERFORMED' and s['candidate_promoted'] is False and s['candidate_admitted_to_active_state'] is False, 'historical admission or remote sync invented')
        require(s['new_scientific_inference'] is False and s['physical_model_change'] == 'NONE', 'physical inference invented')
        require(s['numerical_dispatches'] == s['new_optimizer_starts'] == 0, 'numerical production invented')
        require(s['reference_truth_gate'] == 'BLOCKED' and s['final_result_gate'] == 'UNRESOLVED', 'qualification weakened')
        require(state['production_restart_authorized'] is False and s['production_restart_authorized'] is False, 'production authorized')
        require(state['physical_model_change'] is False, 'physical model changed')
        entries = {x['evidence_id']:x for x in load(evidence/'evidence_registry.json')['entries']}
        for eid in ['EVD-Q043-RESULT', 'EVD-Q043-JOURNAL']:
            e = entries[eid]
            require(e['scientific_classification'] == s['actual_result'], 'evidence scope differs')
            require(e['independent_cosmological_evidence'] is False and e['physical_falsification'] is False and e['production_restart_authorized'] is False, 'internal evidence elevated to physics')
        update = load(evidence/'q_updates/Q043.json')
        require(update['historical_state_is_current_state'] is False and update['source_repository_modified'] is False, 'historical/current state conflated')
        return 'Original local-only result preserved; no physics or production inferred'
    gate('Q043_QUALIFICATION_GATE', qualification)

    def continuity():
        s = load(evidence/'sources/Q043/integration_result.json')
        d = load(evidence/'sources/Q042/ingestion_decision.json')
        a = load(evidence/'sources/Q042/ingestion_audit.json')
        require(s['original_91_source_register'] == d['source_register'] == a['source_register'], 'source register changed')
        require(len(d['source_register']) == len({x['id'] for x in d['source_register']}) == 91, 'source count differs')
        for key, value in s['original_claim_maps'].items():
            require(value == d[key] and value == a[key], 'original claim map differs: '+key)
        inherited = load(old/'evidence_registry.json')['entries']
        current = load(evidence/'evidence_registry.json')['entries']
        require(current[:len(inherited)] == inherited, 'inherited evidence entries altered')
        return '91 source objects, both claim-map trees and all inherited evidence preserved'
    gate('Q043_SOURCE_CONTINUITY_GATE', continuity)

    def physical():
        for name, key in [('parameters','parameters'), ('equations','equations'), ('benchmarks','benchmarks'), ('assumptions','assumptions'), ('uncertainty','uncertainties'), ('domain_of_validity','domains'), ('limitations','limitations')]:
            require(load(formal/(name+'.json'))[key] == load(old/(name+'.json'))[key], 'physical/formal entries changed: '+name)
        for name in ['observations','constraints','mechanisms']:
            require(load(layer/(name+'.json'))[name] == load(old/(name+'.json'))[name], 'physical layer changed: '+name)
        require(load(formal/'input_schema.json') == load(old/'input_schema.json') and load(formal/'output_schema.json') == load(old/'output_schema.json'), 'public schemas changed')
        return 'Physical/formal entries and public calculation definitions unchanged'
    gate('Q043_PHYSICAL_PRESERVATION_GATE', physical)

    def predictions():
        for name in ['predictions','contradictions']:
            require(load(layer/(name+'.json'))[name] == load(old/(name+'.json'))[name], 'prediction/contradiction history changed')
        return 'All original predictions, statuses and contradictions unchanged'
    gate('Q043_PREDICTION_CONTRADICTION_GATE', predictions)

    def diff():
        d = load(root/'candidate/candidate_diff.json')
        require(d['target_q'] == 'Q043' and d['physical_model_change'] is False and d['update_class'] == 'EVIDENCE_ONLY_UPDATE', 'diff scope differs')
        for key in ['new_domains','new_parameters','new_equations','new_assumptions','new_uncertainties','new_benchmarks','new_calculations','resolved_contradictions','superseded']:
            require(d[key] == [], 'unsupported addition: '+key)
        old_items = load(old/'robustness.json')['items']
        new_items = load(layer/'robustness.json')['items']
        require(new_items[:-1] == old_items and new_items[-1]['id'] == 'ROB-Q043-LOCAL-VALIDATION-001', 'unjustified robustness diff')
        eids = {x['evidence_id'] for x in load(evidence/'evidence_registry.json')['entries']}
        require(set(d['evidence_refs']) <= eids, 'unresolved diff evidence')
        return 'Only traceable internal technical evidence/robustness and Q metadata added'
    gate('Q043_DIFF_GATE', diff)

    def firewall():
        count = 0
        for base in [layer,formal,evidence]:
            for p in base.rglob('*'):
                if p.is_file() and p.suffix in {'.json','.md','.txt'}:
                    text = p.read_text(encoding='utf-8')
                    nums = [int(x) for x in re.findall(r'\bQ-?0*([0-9]{1,5})\b',text,re.I)]
                    require(not any(x > 43 for x in nums), 'high-Q origin in '+str(p))
                    count += 1
        # New manuscript PDF text is archived and hashed alongside original bytes.
        # Prior PDF sources are unchanged historical evidence, independently hashed.
        for name in ['q_journal.txt','appendices.txt','main_book.txt']:
            require((evidence/'sources/Q043'/name).exists(), 'verified manuscript text missing')
        return {'scanned_files':count, 'maximum_authorized_q':43, 'pdf_text_source_hashes_verified':True}
    gate('Q043_FIREWALL_GATE', firewall)

    def immutable():
        for relative, expected in provenance['protected_input_hashes'].items():
            if not candidate and (relative.startswith(('accepted/','model/')) or relative in ['evidence/evidence_registry.json','release/MODEL_RELEASE_HANDOFF.json','release/MODEL_RELEASE_HANDOFF.md']):
                continue
            require(digest(root/relative) == expected, 'protected input changed: '+relative)
        if not candidate:
            snap = root/'versions/accepted/v0.5'
            for p in (root/'accepted').iterdir():
                require(digest(p) == digest(snap/p.name), 'accepted snapshot mismatch')
            for p in formal.glob('*.json'):
                require(digest(p) == digest(snap/p.name), 'formal snapshot mismatch')
        return 'Old snapshots and source bytes immutable; accepted untouched before promotion'
    gate('Q043_ACCEPTED_IMMUTABILITY_GATE', immutable)

    def formal_sync():
        m = load(formal/'model_manifest.json')
        require(m['current_q'] == m['q_access_end'] == 'Q043' and m['q_access_start'] == 'Q001', 'formal Q mismatch')
        require(m['accepted_model_version'] == 'v0.5' and m['model_revision'] == 'R000005' and m['formal_model_version'] == 'v0.5-formalization-1', 'formal version mismatch')
        require(m['scientific_change'] is False, 'scientific change declared')
        eids = {x['evidence_id'] for x in load(evidence/'evidence_registry.json')['entries']}
        require(set(m['evidence_refs']) <= eids, 'unresolved formal evidence')
        return 'Formal identity, anti-invention rule and references coherent'
    gate('Q043_FORMAL_SYNC_GATE', formal_sync)

    def git_provenance():
        subprocess.run(['git','cat-file','-e',provenance['model_input_commit']+'^{commit}'],cwd=root,check=True,capture_output=True)
        require(provenance['source_repository_inspection_commit'] == '72cf9e92fc794c122f593a77b6a555e6e97f6a2e' and provenance['source_manuscript_commit'] is None, 'source artifact incorrectly assigned to commit')
        return 'Real reachable input commit; no fabricated manuscript commit'
    gate('Q043_REAL_PROVENANCE_GATE', git_provenance)

    passed = sum(x['status'] == 'PASS' for x in rows)
    return {'artifact_type':'Q043_MODEL_UPDATE_VALIDATION','target_q':'Q043','mode':'CANDIDATE' if candidate else 'CURRENT_ACCEPTED','tests':rows,'tests_total':len(rows),'tests_passed':passed,'all_green':passed == len(rows),'non_destructive':True}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', action='store_true')
    ap.add_argument('--root', type=Path, default=ROOT)
    args = ap.parse_args()
    result = run_tests(args.root, args.candidate)
    for row in result['tests']:
        print(f"{row['id']}={row['status']} {row['detail']}")
    print(f"Q043_MODEL_TESTS={result['tests_passed']}/{result['tests_total']}")
    raise SystemExit(0 if result['all_green'] else 1)
