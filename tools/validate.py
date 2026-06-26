#!/usr/bin/env python3
"""知识库格式铁律校验 —— 把 CLAUDE.md 里的"自动化检查"落成真 lint。

校验范围：
  insights  knowledge/insights/<phase>/*.yaml
  spa       knowledge/security/spa/<domain>/*.yaml

ERROR（退出码 1，硬规则，当前全库应为 0）：
  - YAML 可解析、为 mapping
  - 必填字段齐全（按各自 schema）
  - id == 文件名
  - id 唯一（insights 全局唯一；spa 全局唯一）
  - insights: reasoning_chain 为非空列表，且无"步骤X"命令式写法
  - spa: observe/infer/question/verify 必须存在
  - whitebox spa: verify.whitebox 必须含 grep 命令

WARN（默认不计入退出码，--strict 时升级为失败）：
  - insights: reasoning_chain 行首不是检查式开头

用法：  python3 tools/validate.py            # 跑全库
       python3 tools/validate.py --strict   # 警告也算失败（CI 严格模式）
"""
import os, sys, re, yaml

INS_ROOT = "knowledge/insights"
SPA_ROOT = "knowledge/security/spa"
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


def check_id(p, d):
    """检查 id 字段存在且等于文件名"""
    if d is None or not isinstance(d, dict):
        err(p, "非 mapping / 空文件")
        return None
    i = d.get("id")
    if not i:
        err(p, "缺必填字段: id")
        return None
    base = os.path.splitext(os.path.basename(p))[0]
    if i != base:
        err(p, f"id({i}) ≠ 文件名({base})")
    return i


def check_reasoning_chain(p, rc):
    """insights 专用：校验 reasoning_chain"""
    if not isinstance(rc, list) or not rc:
        err(p, "reasoning_chain 缺失或非列表")
        return
    for line in rc:
        s = str(line).strip()
        if re.match(r"^步骤\s*\d", s) or s.startswith("步骤"):
            err(p, f'reasoning_chain 含"步骤X"命令式写法: {s[:30]}')
        elif not s.startswith(ALLOWED_PREFIX) and not s.startswith("-"):
            warn(p, f"reasoning_chain 行首非检查式: {s[:30]}")


def validate_insights():
    REQ = ("id", "name", "phase", "applicable", "approach", "observation",
           "hypothesis", "why_here_first", "action_result", "reasoning_chain", "vuln_root")
    seen = {}
    for p in yfiles(INS_ROOT, INS_SKIP):
        d, e = load(p)
        if e:
            err(p, f"YAML 解析失败: {e}"); continue
        if d is None or not isinstance(d, dict):
            err(p, "非 mapping / 空文件"); continue
        for f in REQ:
            if not d.get(f):
                err(p, f"缺必填字段: {f}")
        i = check_id(p, d)
        if i:
            if i in seen: err(p, f"id 重复，另见 {seen[i]}")
            else: seen[i] = p
        check_reasoning_chain(p, d.get("reasoning_chain"))


def validate_spa():
    REQ = ("id", "name", "applicable", "domain", "severity", "priority",
           "accessRequired", "observe", "infer", "question", "verify", "vulnRoot")
    seen = {}
    for p in yfiles(SPA_ROOT):
        d, e = load(p)
        if e:
            err(p, f"YAML 解析失败: {e}"); continue
        if d is None or not isinstance(d, dict):
            err(p, "非 mapping / 空文件"); continue
        for f in REQ:
            if not d.get(f):
                err(p, f"缺必填字段: {f}")
        i = check_id(p, d)
        if i:
            if i in seen: err(p, f"spa 内 id 重复，另见 {seen[i]}")
            else: seen[i] = p
        # 校验 verify 结构
        verify = d.get("verify")
        if isinstance(verify, dict):
            has_bb = bool(verify.get("blackbox"))
            has_wb = bool(verify.get("whitebox"))
            if not has_bb and not has_wb:
                err(p, "verify 中 blackbox 和 whitebox 至少需要一个")
            # 白盒必须含 grep
            applicable = d.get("applicable", "")
            if applicable in ("whitebox", "both") and has_wb:
                wb = verify.get("whitebox", [])
                txt = str(wb)
                if not re.search(r"grep|semgrep|ripgrep|\brg\b", txt, re.I):
                    err(p, "whitebox verify 缺 grep/semgrep 命令")
        # 校验 observe.signals 存在
        observe = d.get("observe")
        if isinstance(observe, dict):
            signals = observe.get("signals")
            if not signals or not isinstance(signals, list):
                warn(p, "observe.signals 为空或非列表")


def main():
    if os.path.isdir(INS_ROOT):
        validate_insights()
    if os.path.isdir(SPA_ROOT):
        validate_spa()
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
