"""数值核对（技能 §6.3）。放在项目根目录，依赖 examples/tabular.py。任何一项不过，返回码为 1。

四道检查：
  1. 表格    正文 \\input 的每张 tables/<id>.tex，都必须能由 examples/out/tables/<id>.json
            逐字节重新生成 —— 证明表格来自这次运行的数据，没人手改过。
  2. 代码片段 \\input 的 tables/snip_*.tex 必须存在（由 make_snippets.py 按标记生成）。
  3. 等宽输出块  残留的 minted{text} 里含数字的行，必须能在真实 stdout 里逐字找到。
            （现在程序输出都已改成表格，这一项应当为空。）
  4. 正文数字  正文句子、表格标题、表注里带小数的数字，必须能在运行数据里找到：
            逐字相同，或按它的精度四舍五入后相同。找不到的要么是编的，
            要么写进下面的白名单并注明来源。
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "examples"))
from tabular import render_tex  # noqa: E402

# 正文里合法地出现、但不来自本书运行数据的数字。每一条都要写清来源。
WHITELIST = {
    # "2201.11875": "arXiv 编号，不是测量值",
    # 每一条都写清来源。不许为了让检查通过而往这里加。
}

NUM_TOKEN = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
SCI_TEX = re.compile(r"(?<![\d.])([-+]?\d+(?:\.(\d+))?)\s*\\times\s*10\^\{?\s*([-+]?\d+)\s*\}?")
DEC = re.compile(r"(?<![\w.\\])([-+]?\d+\.(\d{2,}))(?![\d])")


def load_tables():
    out = {}
    for f in glob.glob(os.path.join(ROOT, "examples", "out", "tables", "*.json")):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        out[d["id"]] = d
    return out


def data_numbers(tables):
    """运行数据里出现过的全部数字：stdout 里的记号 + 表格里的数值。"""
    strings, values = set(), []
    for f in glob.glob(os.path.join(ROOT, "examples", "out", "*.txt")):
        text = open(f, encoding="utf-8").read()
        for tok in NUM_TOKEN.findall(text):
            strings.add(tok)
            try:
                values.append(float(tok))
            except ValueError:
                pass
    for d in tables.values():
        for row in d["rows_plain"]:
            strings.update(row)
        for row in d["rows_value"]:
            for v in row:
                if isinstance(v, list):
                    values.extend(x for r in v for x in r)
                elif v is not None:
                    values.append(v)
    return strings, values


def strip_tex(src):
    src = re.sub(r"(?<!\\)%.*", "", src)                                   # 注释
    src = re.sub(r"\\begin\{minted\}.*?\\end\{minted\}", "", src, flags=re.S)
    src = re.sub(r"\\input(minted)?(\[[^\]]*\])?\{[^}]*\}(\{[^}]*\})?", "", src)
    src = re.sub(r"\\(label|ref|eqtag|supeq|includegraphics)(\[[^\]]*\])?\{[^}]*\}", "", src)
    return src


def prose_tokens(text):
    found = []
    for m in SCI_TEX.finditer(text):
        found.append(("sci", m.group(0), float(m.group(1)), len(m.group(2) or ""), int(m.group(3))))
    text = SCI_TEX.sub(" ", text)
    for m in DEC.finditer(text):
        found.append(("dec", m.group(1), float(m.group(1)), len(m.group(2)), 0))
    return found


def traceable(tok, strings, values):
    kind, raw, val, nd, exp = tok
    if kind == "dec":
        if raw in strings or raw.lstrip("+") in strings:
            return True
        return any(abs(round(v, nd) - val) < 1e-9 * max(1.0, abs(val)) for v in values)
    for v in values:                                   # 科学计数法：比较尾数
        if v == 0:
            continue
        if abs(round(v / 10.0 ** exp, nd) - val) < 1e-9 * max(1.0, abs(val)):
            return True
    return False


def main():
    fails = 0
    tables = load_tables()
    parts = sorted(glob.glob(os.path.join(ROOT, "parts", "*.tex")))
    sources = {os.path.basename(p): open(p, encoding="utf-8").read() for p in parts}

    # ---- 1 / 2：表格与代码片段
    used = set()
    for name, src in sources.items():
        for tid in re.findall(r"\\input\{tables/([^}]+)\}", src):
            used.add(tid)
            path = os.path.join(ROOT, "tables", tid + ".tex")
            if tid.startswith("snip_"):
                if not os.path.exists(path):
                    print(f"  [片段] {name}: tables/{tid}.tex 不存在（先跑 make_snippets.py）")
                    fails += 1
                continue
            if tid not in tables:
                print(f"  [表格] {name}: 没有数据 examples/out/tables/{tid}.json")
                fails += 1
                continue
            have = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if have != render_tex(tables[tid]):
                print(f"  [表格] {name}: tables/{tid}.tex 与数据重新生成的结果不一致（被手改过？）")
                fails += 1
    n_tab = len([u for u in used if not u.startswith("snip_")])
    print(f"  1. 表格：正文引用 {n_tab} 张，逐张由数据重新生成比对")
    unused = sorted(set(tables) - used)
    if unused:
        print(f"     （生成了但正文没用：{', '.join(unused)}）")

    # ---- 3：残留的等宽输出块
    stdout = set()
    for f in glob.glob(os.path.join(ROOT, "examples", "out", "*.txt")):
        stdout.update(l.rstrip("\n") for l in open(f, encoding="utf-8"))
    n_text = 0
    for name, src in sources.items():
        for m in re.finditer(r"\\begin\{minted\}\{text\}\n(.*?)\\end\{minted\}", src, re.S):
            for line in m.group(1).split("\n"):
                if re.search(r"\d", line):
                    n_text += 1
                    if line.rstrip() not in stdout:
                        print(f"  [输出块] {name}: 在 stdout 里找不到：{line.strip()!r}")
                        fails += 1
    print(f"  2. 等宽输出块：残留含数字的行 {n_text} 行")

    # ---- 4：正文、表题、表注里的数字
    strings, values = data_numbers(tables)
    checked = 0
    texts = [(name, strip_tex(src)) for name, src in sources.items()]
    texts += [(f"表 {d['id']}", (d["caption"] or "") + " " + (d["note_tex"] or ""))
              for d in tables.values() if d["id"] in used]
    for where, text in texts:
        for tok in prose_tokens(text):
            checked += 1
            if tok[1] in WHITELIST or traceable(tok, strings, values):
                continue
            print(f"  [正文数字] {where}: {tok[1]!r} 在运行数据里找不到")
            fails += 1
    print(f"  3. 正文数字：核对 {checked} 个（白名单 {len(WHITELIST)} 条，各附来源）")

    print()
    print("  全部通过。" if fails == 0 else f"  {fails} 处未通过。")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
