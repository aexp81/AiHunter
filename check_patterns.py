#!/usr/bin/env python3
"""Check whitebox and blackbox pattern YAML files against CLAUDE.md spec."""
import yaml
import sys
import json

REQUIRED_FIELDS = [
    'name', 'id',
    'trigger', 'access_required', 'prerequisite',
    'practical_notes', 'verify', 'vuln_root', 'transferable_to', 'cases'
]

# reasoning_chain or blackbox_reasoning required
REASONING_FIELDS = ['reasoning_chain', 'blackbox_reasoning']

issues = []

def check_yaml_syntax(path, label):
    """Check YAML syntax by loading the file."""
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        print(f"[PASS] {label}: YAML syntax OK")
        return data
    except yaml.YAMLError as e:
        msg = f"[FAIL] {label}: YAML syntax error: {e}"
        print(msg)
        issues.append(msg)
        return None

def check_schema(patterns, label, is_whitebox):
    """Check each pattern has required fields."""
    for i, p in enumerate(patterns):
        name = p.get('name', f'(unnamed pattern #{i+1})')
        pid = p.get('id', '(no id)')

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in p:
                msg = f"[SCHEMA] {label} / {pid} ({name}): missing required field '{field}'"
                issues.append(msg)
                print(msg)

        # Check applicable field
        if 'applicable' not in p:
            msg = f"[SCHEMA] {label} / {pid} ({name}): missing 'applicable' field"
            issues.append(msg)
            print(msg)

        # Check reasoning_chain presence
        has_reasoning = any(f in p for f in REASONING_FIELDS)
        if not has_reasoning:
            msg = f"[SCHEMA] {label} / {pid} ({name}): missing reasoning_chain or blackbox_reasoning"
            issues.append(msg)
            print(msg)

def check_reasoning_chain_format(patterns, label, is_whitebox):
    """Check reasoning_chain format rules."""
    for i, p in enumerate(patterns):
        pid = p.get('id', f'(unnamed #{i+1})')
        name = p.get('name', '')

        # Get the chain
        chain = p.get('reasoning_chain', p.get('blackbox_reasoning', []))
        if not chain:
            continue

        for j, step in enumerate(chain):
            step_str = str(step).strip()

            # Rule: no "步骤X：" prefix
            if step_str.startswith('步骤') and '：' in step_str[:6]:
                msg = f"[REASONING] {label} / {pid}: step {j+1} starts with '步骤X：' (forbidden): {step_str[:50]}"
                issues.append(msg)
                print(msg)

        # Whitebox specific: must have grep/Semgrep commands
        if is_whitebox and 'reasoning_chain' in p:
            chain = p['reasoning_chain']
            has_grep = any('grep' in str(s).lower() or 'semgrep' in str(s).lower() for s in chain)
            if not has_grep:
                msg = f"[REASONING-WHITEBOX] {label} / {pid} ({name}): reasoning_chain has no grep/Semgrep command (required for whitebox)"
                issues.append(msg)
                print(msg)

        # Blackbox specific: should not depend on source code
        if not is_whitebox and 'blackbox_reasoning' in p:
            chain = p['blackbox_reasoning']
            for j, step in enumerate(chain):
                step_str = str(step)
                if '白盒：' in step_str or '源码' in step_str or 'grep -rn' in step_str:
                    msg = f"[REASONING-BLACKBOX] {label} / {pid}: blackbox_reasoning step {j+1} references source code: {step_str[:60]}"
                    issues.append(msg)
                    print(msg)

def check_classification(wb_patterns, bb_patterns):
    """Check whitebox-only patterns not in blackbox, and vice versa."""
    # Whitebox-only patterns that should NOT be in blackbox
    whitebox_only_ids = set()
    for p in wb_patterns:
        applicable = p.get('applicable', '')
        if applicable == 'whitebox':
            whitebox_only_ids.add(p.get('id', ''))

    bb_ids = {p.get('id', '') for p in bb_patterns}

    for wid in whitebox_only_ids:
        if wid in bb_ids:
            msg = f"[CLASSIFICATION] Whitebox-only pattern '{wid}' found in blackbox.yaml (should not be there)"
            issues.append(msg)
            print(msg)

    # Check blackbox patterns with applicable='blackbox' in whitebox file
    blackbox_only_ids = set()
    for p in bb_patterns:
        applicable = p.get('applicable', '')
        if applicable == 'blackbox':
            blackbox_only_ids.add(p.get('id', ''))

    wb_ids = {p.get('id', '') for p in wb_patterns}

    for bid in blackbox_only_ids:
        if bid in wb_ids:
            msg = f"[CLASSIFICATION] Blackbox-only pattern '{bid}' found in whitebox.yaml (should not be there)"
            issues.append(msg)
            print(msg)

    # Check patterns without 'applicable' field
    for p in wb_patterns:
        if 'applicable' not in p:
            msg = f"[CLASSIFICATION] Whitebox pattern '{p.get('id', '?')}' missing 'applicable' field"
            issues.append(msg)
            print(msg)

    for p in bb_patterns:
        if 'applicable' not in p:
            msg = f"[CLASSIFICATION] Blackbox pattern '{p.get('id', '?')}' missing 'applicable' field"
            issues.append(msg)
            print(msg)

def check_other_issues(patterns, label, is_whitebox):
    """Check for miscellaneous issues."""
    ids_seen = set()
    for p in patterns:
        pid = p.get('id', '')
        name = p.get('name', '')

        # Duplicate IDs
        if pid in ids_seen:
            msg = f"[DUPLICATE] {label}: duplicate pattern ID '{pid}'"
            issues.append(msg)
            print(msg)
        ids_seen.add(pid)

        # Empty required lists
        for field in ['trigger', 'verify', 'transferable_to', 'cases']:
            val = p.get(field)
            if val is not None and isinstance(val, list) and len(val) == 0:
                msg = f"[EMPTY] {label} / {pid}: field '{field}' is an empty list"
                issues.append(msg)
                print(msg)

        # Check reasoning_chain steps for result descriptions (禁止结果描述)
        chain = p.get('reasoning_chain', p.get('blackbox_reasoning', []))
        if chain:
            for j, step in enumerate(chain):
                s = str(step).strip()
                # Result descriptions like "发现XXX", "存在XXX" at the start
                if s.startswith('发现') or s.startswith('存在'):
                    msg = f"[RESULT_DESC] {label} / {pid}: step {j+1} starts with result description: {s[:50]}"
                    issues.append(msg)
                    print(msg)

        # Check non-standard reasoning field names in whitebox
        if is_whitebox and 'blackbox_reasoning' in p:
            msg = f"[FIELD_NAME] {label} / {pid} ({name}): whitebox file uses 'blackbox_reasoning' instead of 'reasoning_chain'"
            issues.append(msg)
            print(msg)

        # Chinese key names (YAML keys should be English)
        for key in p.keys():
            if any('\u4e00' <= c <= '\u9fff' for c in key):
                msg = f"[KEY_NAME] {label} / {pid}: Chinese key name '{key}' (should use English)"
                issues.append(msg)
                print(msg)


# Main
print("=" * 70)
print("Pattern Library Check Report")
print("=" * 70)

wb_data = check_yaml_syntax('/meowai/workspace/AiHunter/openwebui-patterns-whitebox.yaml', 'whitebox')
bb_data = check_yaml_syntax('/meowai/workspace/AiHunter/openwebui-patterns-blackbox.yaml', 'blackbox')

if wb_data and bb_data:
    wb_patterns = wb_data.get('patterns', [])
    bb_patterns = bb_data.get('patterns', [])

    print(f"\nWhitebox patterns count: {len(wb_patterns)}")
    print(f"Blackbox patterns count: {len(bb_patterns)}")

    print("\n--- Schema Completeness ---")
    check_schema(wb_patterns, 'whitebox', True)
    check_schema(bb_patterns, 'blackbox', False)

    print("\n--- Reasoning Chain Format ---")
    check_reasoning_chain_format(wb_patterns, 'whitebox', True)
    check_reasoning_chain_format(bb_patterns, 'blackbox', False)

    print("\n--- Classification Check ---")
    check_classification(wb_patterns, bb_patterns)

    print("\n--- Other Issues ---")
    check_other_issues(wb_patterns, 'whitebox', True)
    check_other_issues(bb_patterns, 'blackbox', False)

print("\n" + "=" * 70)
print(f"TOTAL ISSUES FOUND: {len(issues)}")
print("=" * 70)

if issues:
    print("\nSummary of all issues:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
