#!/usr/bin/env python3
"""知识库格式铁律校验（T-002）—— 把 CLAUDE.md 里的"自动化检查"落成真 lint。

校验范围：
  insights  knowledge/insights/<phase>/*.yaml
  patterns  knowledge/security/patterns/{blackbox,whitebox}/<cat>/*.yaml

ERROR（退出码 1，硬规则，当前全库应为 0）：
  - YAML 可解析、为 mapping
  - 必填字段齐全（按各自 schema 的实际通用字段）
  - id == 文件名
  - id 唯一：insights 全局唯一；patterns 在各自 mode(blackbox/whitebox) 内唯一
  - reasoning_chain 为非空列表，且无"步骤X"命令式写法（CLAUDE §2 明令禁止）
  - whitebox 的 reasoning_chain 必须含 grep/semgrep 命令（CLAUDE §6）

WARN（默认不计入退出码，--strict 时升级为失败）：
  - reasoning_chain 行首不是 问/如果/白盒/验证/对比/扩展 等检查式开头

用法：  python3 tools/validate.py            # 跑全库
       python3 tools/validate.py --strict   # 警告也算失败（CI 严格模式）
"""
import os, sys, re, yaml

INS_ROOT = "knowledge/insights"
PAT_ROOT = "knowledge/security/patterns"
INS_SKIP = {"articles.yaml", "INDEX.yaml"}
ALLOWED_PREFIX = ("问", "如果", "白盒", "黑盒", "验证", "对比", "扩展", "执行", "补充", "注意", "构造")

errors, warns = [], []
def err(p, m): errors.append((p, m))
def warn(p, m): warns.append((p, m))


def yfiles(root, skip=()):
    for r, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".yaml") and f not in skip:
                yield os.path.join(r, f)


def load(p):
    try:
        return yaml.safe_load(open(p, encoding="utf-8")), None
    except Exception as e:
        return None, str(e)


def check_reasoning_chain(p, rc):
    if not isinstance(rc, list) or not rc:
        err(p, "reasoning_chain 缺失或非列表")
        return
    for line in rc:
        s = str(line).strip()
        if re.match(r"^步骤\s*\d", s) or s.startswith("步骤"):
            err(p, f'reasoning_chain 含"步骤X"命令式写法: {s[:30]}')
        elif not s.startswith(ALLOWED_PREFIX) and not s.startswith("-"):
            warn(p, f"reasoning_chain 行首非检查式: {s[:30]}")


def check_common(p, d, required):
    if d is None or not isinstance(d, dict):
        err(p, "非 mapping / 空文件")
        return None
    for f in required:
        if not d.get(f):
            err(p, f"缺必填字段: {f}")
    i = d.get("id")
    base = os.path.splitext(os.path.basename(p))[0]
    if i and i != base:
        err(p, f"id({i}) ≠ 文件名({base})")
    check_reasoning_chain(p, d.get("reasoning_chain"))
    return i


def validate_insights():
    REQ = ("id", "name", "phase", "applicable", "approach", "observation",
           "hypothesis", "why_here_first", "action_result", "reasoning_chain", "vuln_root")
    seen = {}
    for p in yfiles(INS_ROOT, INS_SKIP):
        d, e = load(p)
        if e:
            err(p, f"YAML 解析失败: {e}"); continue
        i = check_common(p, d, REQ)
        if i:
            if i in seen: err(p, f"id 重复，另见 {seen[i]}")
            else: seen[i] = p


def validate_patterns():
    REQ = ("id", "name", "applicable", "trigger", "reasoning_chain")
    seen = {"blackbox": {}, "whitebox": {}}
    for p in yfiles(PAT_ROOT):
        d, e = load(p)
        if e:
            err(p, f"YAML 解析失败: {e}"); continue
        i = check_common(p, d, REQ)
        mode = "whitebox" if "/whitebox/" in p.replace(os.sep, "/") else "blackbox"
        if i:
            if i in seen[mode]: err(p, f"{mode} 内 id 重复，另见 {seen[mode][i]}")
            else: seen[mode][i] = p
        if mode == "whitebox" and isinstance(d, dict):
            txt = " ".join(str(x) for x in (d.get("reasoning_chain") or []))
            if not re.search(r"grep|semgrep|ripgrep|\brg\b", txt, re.I):
                err(p, "whitebox reasoning_chain 缺 grep/semgrep 命令")


def main():
    validate_insights()
    validate_patterns()
    for p, m in warns:
        print(f"WARN  {p}: {m}")
    for p, m in errors:
        print(f"ERROR {p}: {m}")
    strict = "--strict" in sys.argv
    print(f"\n{len(errors)} errors, {len(warns)} warnings"
          + ("  (--strict: 警告计入失败)" if strict else ""))
    if errors or (strict and warns):
        sys.exit(1)
    print("✓ 校验通过")


if __name__ == "__main__":
    main()
