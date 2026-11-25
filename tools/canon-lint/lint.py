#!/usr/bin/env python3
"""canon-lint: 检查 Markdown 是否违反《柳德米拉》十条硬设定。

规则:
  - 超光速（否定语境不算，如“没有超光速”“不许写超光速”）
  - 地表 1 g
  - 三星系距离数值
  - 自转 24 小时
  - 大气 21% 氧 / 101 kPa
  - 废弃概念（账本）
  - 主线人物被写死

跳过: 围栏代码块、行内含 `canon-lint:ignore` 的行。
"""
import argparse, pathlib, re, sys

RULES = [
    ("超光速", r"超光速|曲率(?:驱动|引擎)?|跃迁|虫洞通信|warp|hyperspace", "error",
     "本世界没有超光速；用光行时/几代人的等待来写距离。"),
    ("地表1g", r"地表\s*1\s*g|地面上\s*1\s*g", "error",
     "内表重力是 0.020 g；1 g 只存在于旋转环/重力球里。"),
    ("自转错误", r"24\s*小时(?:自转|一天)|一天\s*24\s*小时", "error",
     "自转 105.8 分钟；一个昼夜 24 小时（昼 11.23 + 夜 12.77）。"),
    ("大气错误", r"21\s*%\s*(?:的\s*)?氧|101\s*kPa", "warn",
     "大气是 19 kPa、88% O₂ + 12% N₂。"),
    ("废弃概念", r"账本", "warn", "“账本”已删除；改用“四象”。"),
    ("人物死亡", r"(鲁滨|美奈子|奥利菲亚|gump|伊戈尔|顾岸)\s*(?:死了|身亡|阵亡)",
     "warn", "主线人物不得写死；旁支可写过去/未来。"),
]
NEG = ("没有", "无", "不许", "禁止", "不写", "不得", "不存在", "杜绝")
DIST_OK = {"天苑四": 10.5, "天仓五": 11.9, "鲸鱼座YZ": 12.1}

def strip_code(text: str) -> str:
    out, fence = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
            out.append("")
            continue
        out.append("" if fence else line)
    return "\n".join(out)

def check_file(p: pathlib.Path):
    raw = p.read_text(encoding="utf-8", errors="ignore")
    lines_raw = raw.splitlines()
    text = strip_code(raw)
    issues = []
    for name, pat, level, hint in RULES:
        for m in re.finditer(pat, text, flags=re.I):
            line_no = text[:m.start()].count("\n") + 1
            line = lines_raw[line_no - 1] if line_no <= len(lines_raw) else ""
            if "canon-lint:ignore" in line:
                continue
            ctx = text[max(0, m.start() - 8): m.end() + 8]
            if level == "error" and name == "超光速" and any(n in ctx for n in NEG):
                continue
            issues.append((level, name, line_no, m.group(0)[:40], hint))
    for m in re.finditer(r"(天苑四|天仓五|鲸鱼座\s*YZ)[^\n]{0,20}?(\d+(?:\.\d+)?)\s*(?:光年|ly)", text):
        star, val = m.group(1).replace(" ", ""), float(m.group(2))
        if star in DIST_OK and abs(val - DIST_OK[star]) > 0.05:
            line_no = text[:m.start()].count("\n") + 1
            line = lines_raw[line_no - 1] if line_no <= len(lines_raw) else ""
            if "canon-lint:ignore" in line:
                continue
            issues.append(("error", "距离数值", line_no, f"{star} {val}",
                           f"应为 {DIST_OK[star]} 光年"))
    return issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(__file__).resolve().parents[2]
    files = [pathlib.Path(f) for f in a.files] if a.files and not a.all \
        else sorted(root.rglob("*.md"))
    e = w = 0
    for f in files:
        if ".git" in f.parts:
            continue
        for level, name, line, frag, hint in check_file(f):
            e += level == "error"; w += level == "warn"
            print(f"{level.upper():5} {f.relative_to(root)}:{line} [{name}] {frag!r}\n      → {hint}")
    print(f"\n{len(files)} files, {e} errors, {w} warnings")
    sys.exit(1 if (e or (a.strict and w)) else 0)

if __name__ == "__main__":
    main()
