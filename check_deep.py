#!/usr/bin/env python3
"""Deep check on reasoning_chain step format compliance."""
import yaml

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

wb = load_yaml('/meowai/workspace/AiHunter/openwebui-patterns-whitebox.yaml')
bb = load_yaml('/meowai/workspace/AiHunter/openwebui-patterns-blackbox.yaml')

issues = []

def check_step_format(step, pid, label, step_num):
    """Each step must start with 问：/ 如果 / 白盒：/ 黑盒：/ or be a sub-item (indented with -)."""
    s = str(step).strip()

    # Sub-items starting with "-" or "  -" are acceptable
    if s.startswith('- ') or s.startswith('  '):
        return

    # Acceptable prefixes
    ok_prefixes = ['问：', '如果', '白盒：', '黑盒：', '验证', '构造']
    if any(s.startswith(p) for p in ok_prefixes):
        return

    # Result descriptions (forbidden)
    result_words = ['发现', '存在', '确认', '成功', '失败']
    for w in result_words:
        if s.startswith(w):
            issues.append(f"[STEP_RESULT_DESC] {label}/{pid} step {step_num}: starts with result description '{w}': {s[:60]}")
            return

    # Not a question or condition - potential issue
    # Check if it's an action statement without question format
    if not s.endswith('？') and '→' not in s and '如果' not in s:
        # Likely not compliant
        issues.append(f"[STEP_FORMAT] {label}/{pid} step {step_num}: not a question/condition: {s[:80]}")

# Check whitebox
for p in wb.get('patterns', []):
    pid = p.get('id', '?')
    chain = p.get('reasoning_chain', [])
    for i, step in enumerate(chain, 1):
        check_step_format(step, pid, 'WB', i)

# Check blackbox
for p in bb.get('patterns', []):
    pid = p.get('id', '?')
    chain = p.get('blackbox_reasoning', p.get('reasoning_chain', []))
    for i, step in enumerate(chain, 1):
        check_step_format(step, pid, 'BB', i)

# Also check: blackbox patterns using 'reasoning_chain' field instead of 'blackbox_reasoning'
for p in bb.get('patterns', []):
    pid = p.get('id', '?')
    if 'reasoning_chain' in p and 'blackbox_reasoning' not in p:
        issues.append(f"[FIELD_NAME] BB/{pid}: uses 'reasoning_chain' instead of 'blackbox_reasoning' in blackbox file")

# Check: whitebox patterns with verify using string instead of list
for p in wb.get('patterns', []):
    pid = p.get('id', '?')
    v = p.get('verify')
    if v and not isinstance(v, list):
        issues.append(f"[TYPE] WB/{pid}: 'verify' should be a list, got {type(v).__name__}")

    pn = p.get('practical_notes')
    if pn and not isinstance(pn, (list, dict)):
        issues.append(f"[TYPE] WB/{pid}: 'practical_notes' should be list/dict, got {type(pn).__name__}")

# Check: blackbox file using alternative field names (verification_methods vs verify, etc.)
alt_fields = {
    'verification_methods': 'verify',
    'practical_payloads': 'practical_notes (or separate field)',
    'common_frameworks_behavior': '(extra field, OK but not standard)',
}
for p in bb.get('patterns', []):
    pid = p.get('id', '?')
    for alt, standard in alt_fields.items():
        if alt in p and standard.split(' ')[0] not in p:
            issues.append(f"[ALT_FIELD] BB/{pid}: uses '{alt}' instead of standard '{standard}'")

# Print
print("=== Deep Reasoning Chain Format Check ===\n")
if issues:
    for i, iss in enumerate(issues, 1):
        print(f"  {i}. {iss}")
    print(f"\nTotal deep-check issues: {len(issues)}")
else:
    print("  All steps compliant!")
