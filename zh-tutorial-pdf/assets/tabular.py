"""把程序结果同时输出成【终端表格】和【排版用的 LaTeX 表格】。

放置：复制到项目的 examples/tabular.py。它假定项目根目录是 examples/ 的上一级，
数据写到 examples/out/tables/，表格源码写到 tables/。导言区需要 booktabs 与 caption。

为什么需要它：
    正文里的数字必须来自真实运行（技能 §6）。旧做法是把 stdout 原样贴进等宽代码块，
    结果是：表头缩写没人看得懂；一排数字看不出在比什么；中文要靠等宽字体，
    而那个字体常常嵌入失败，读者那边整列消失。

    现在每张表由脚本一次生成三份产物，三份来自同一批字符串：
        终端                        对齐的纯文本，给跑脚本的人看
        examples/out/tables/<id>.json  结构化数据，给核对脚本和作图脚本读
        tables/<id>.tex             booktabs 表格，正文用 \\input 引入
    所以正文里的数字不可能和运行结果对不上 —— 也不存在"抄"这一步。

用法：
    from tabular import Table, num, mat, txt

    t = Table("ex1_width", __file__,
              caption=r"从阶跃初值弛豫出的界面宽度 vs 解析值 $4.164\\,\\epsilon$",
              columns=[("eps", r"$\\epsilon$"), ("宽度", "弛豫所得宽度"), ...])
    t.row(num(eps, ".4f"), num(w, ".6f"), ...)
    t.emit()
"""
import hashlib
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "examples", "out", "tables")
TEX_DIR = os.path.join(ROOT, "tables")

_SCI = re.compile(r"^([+-]?)(\d+(?:\.\d*)?)[eE]([+-]?\d+)$")
_DEC = re.compile(r"^[+-]?\d+(?:\.\d*)?$")
_TEX_SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape_tex(s):
    return "".join(_TEX_SPECIAL.get(ch, ch) for ch in s)


def tex_number(s, keep_zero_exp=False):
    """'3.153466e-01' -> '$3.153466\\times10^{-1}$'；'0.015625' -> '$0.015625$'。

    尾数的每一位原样保留 —— 只改排版，不改数字。
    恰好为零的数写成 0（'+0.000e+00' 读成"+0.000"只会让人疑惑）。
    指数为 0 时默认省掉 ×10^0；同一列里混有别的指数时由调用方要求保留，免得一列两种写法。
    """
    s = s.strip()
    m = _SCI.match(s)
    if m:
        sign, mant, exp = m.groups()
        if float(mant) == 0.0:
            return "$0$"
        e = int(exp)
        body = mant if (e == 0 and not keep_zero_exp) else rf"{mant}\times10^{{{e}}}"
        return f"${sign}{body}$"
    if _DEC.match(s):
        return f"${s}$"          # 定点小数原样保留：同一列小数位一致，对得齐
    return None


def _sci_exp(s):
    m = _SCI.match(s.strip())
    return None if m is None else int(m.group(3))


class Cell:
    """一个单元格：plain 给终端，tex 给排版，value 给核对与作图（可为 None）。"""
    __slots__ = ("plain", "tex", "value")

    def __init__(self, plain, tex, value=None):
        self.plain, self.tex, self.value = plain, tex, value


def num(x, fmt):
    """数值单元格。fmt 是 Python 格式说明，如 '.6e'、'+.3e'、'.5f'。"""
    s = format(x, fmt)
    return Cell(s, tex_number(s), float(x))


def mat(M, fmt=".4f"):
    """2x2 等小矩阵：终端里印成 [a b; c d]，排版成 bmatrix。"""
    rows = [[format(float(v), fmt) for v in r] for r in M]
    plain = "[" + "; ".join(" ".join(r) for r in rows) + "]"
    body = r"\\".join("&".join(v for v in r) for r in rows)
    tex = r"$\begin{bmatrix}" + body + r"\end{bmatrix}$"
    return Cell(plain, tex, [[float(v) for v in r] for r in M])


def txt(s, tex=None):
    """文字单元格。tex 给出时用它排版（可含数学），否则转义 s。"""
    return Cell(s, tex if tex is not None else escape_tex(s))


DASH = Cell("-", "—")


def _as_cell(c):
    if isinstance(c, Cell):
        return c
    if c is None:
        return DASH
    s = str(c)
    t = tex_number(s)
    return Cell(s, t if t is not None else escape_tex(s))


def _as_header(h):
    """表头可以是 (终端文字, 排版文字) 二元组、Cell 或纯字符串。"""
    if isinstance(h, tuple):
        return Cell(h[0], h[1])
    return _as_cell(h)


def _width(s):
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def _pad(s, w, right=True):
    gap = " " * max(0, w - _width(s))
    return gap + s if right else s + gap


def render_tex(d):
    """由 JSON 字典生成表格源码。核对脚本也调用它来确认 .tex 没被手改过。"""
    ncol = len(d["columns_tex"])
    align = d.get("align") or ("l" + "r" * (ncol - 1))
    lines = [
        f"% 自动生成：{d['script']} -> 表 {d['id']}",
        "% 不要手改。要改就改脚本，再跑 build.sh。",
        f"% data-sha256: {d['sha256']}",
        r"\par\medskip",
        r"\noindent\begin{minipage}{\linewidth}",
        r"\centering",
        r"\captionof{table}{" + d["caption"] + r"}\label{tab:" + d["id"] + "}",
        r"\small",
        r"\renewcommand{\arraystretch}{1.12}",
        r"\begin{tabular}{@{}" + align + r"@{}}",
        r"\toprule",
    ]
    groups = d.get("groups")
    if groups:
        cells, rules, col = [], [], 1
        for label, span in groups:
            if label:
                cells.append(r"\multicolumn{" + str(span) + "}{c}{" + label + "}")
                rules.append(r"\cmidrule(lr){" + f"{col}-{col + span - 1}" + "}")
            else:
                cells.extend([""] * span)
            col += span
        lines.append(" & ".join(cells) + r" \\")
        lines.append(" ".join(rules))
    lines.append(" & ".join(d["columns_tex"]) + r" \\")
    lines.append(r"\midrule")
    sep = r" \\ \addlinespace[4pt]" if d.get("has_matrix") else r" \\"
    for k, r in enumerate(d["rows_tex"]):
        last = k == len(d["rows_tex"]) - 1
        lines.append(" & ".join(r) + (r" \\" if last else sep))
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    if d.get("note_tex"):
        lines.append(r"\par\smallskip")
        lines.append(r"\parbox{0.94\linewidth}{\footnotesize " + d["note_tex"] + "}")
    lines.append(r"\end{minipage}")
    lines.append(r"\par\medskip")
    return "\n".join(lines) + "\n"


class Table:
    def __init__(self, tid, script, caption, columns, *, title=None, note=None,
                 note_tex=None, groups=None, align=None):
        self.id = tid
        self.script = os.path.relpath(os.path.abspath(script), ROOT)
        self.caption = caption
        self.title = title or tid
        self.columns = [_as_header(h) for h in columns]
        self.note_plain = note
        self.note_tex = note_tex if note_tex is not None else (escape_tex(note) if note else None)
        self.groups = groups
        self.align = align
        self.rows = []

    def row(self, *cells):
        if len(cells) != len(self.columns):
            raise ValueError(f"表 {self.id}：该行 {len(cells)} 格，表头 {len(self.columns)} 列")
        self.rows.append([_as_cell(c) for c in cells])

    def _print(self):
        heads = [c.plain for c in self.columns]
        body = [[c.plain for c in r] for r in self.rows]
        w = [max(_width(x) for x in col) for col in zip(heads, *body)]
        print(f"  [表 {self.id}] {self.title}")
        print("    " + "  ".join(_pad(h, w[i]) for i, h in enumerate(heads)))
        for r in body:
            print("    " + "  ".join(_pad(x, w[i]) for i, x in enumerate(r)))
        if self.note_plain:
            print("    注：" + self.note_plain)
        print()

    def _normalize_columns(self):
        """同一列里既有 ×10^k（k≠0）又有指数为 0 的数时，指数 0 也写出来，免得一列两种写法。"""
        for j in range(len(self.columns)):
            auto = [r[j] for r in self.rows if r[j].tex == tex_number(r[j].plain)]
            exps = {_sci_exp(c.plain) for c in auto} - {None}
            if 0 in exps and len(exps) > 1:
                for c in auto:
                    c.tex = tex_number(c.plain, keep_zero_exp=True)

    def _default_align(self):
        first_numeric = all(tex_number(r[0].plain) is not None for r in self.rows)
        return ("r" if first_numeric else "l") + "r" * (len(self.columns) - 1)

    def emit(self):
        self._print()
        self._normalize_columns()
        if self.align is None:
            self.align = self._default_align()
        d = {
            "id": self.id,
            "script": self.script,
            "caption": self.caption,
            "columns_plain": [c.plain for c in self.columns],
            "columns_tex": [c.tex for c in self.columns],
            "rows_plain": [[c.plain for c in r] for r in self.rows],
            "rows_tex": [[c.tex for c in r] for r in self.rows],
            "rows_value": [[c.value for c in r] for r in self.rows],
            "note_plain": self.note_plain,
            "note_tex": self.note_tex,
            "groups": self.groups,
            "align": self.align,
            "has_matrix": any(r"\begin{bmatrix}" in c.tex for r in self.rows for c in r),
        }
        payload = json.dumps({k: d[k] for k in ("caption", "columns_tex", "rows_tex",
                                                "note_tex", "groups", "align")},
                             ensure_ascii=False, sort_keys=True)
        d["sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(TEX_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, self.id + ".json"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        with open(os.path.join(TEX_DIR, self.id + ".tex"), "w", encoding="utf-8") as f:
            f.write(render_tex(d))
        return d


def load(tid):
    """作图脚本用：读回某张表的数据。"""
    with open(os.path.join(DATA_DIR, tid + ".json"), encoding="utf-8") as f:
        return json.load(f)
