"""按源码里的注释标记，自动算出正文要截取的代码行号。放在项目根目录。

为什么不直接在正文里写 firstline=147,lastline=153：
    源码一改（比如开头多 import 一行），行号整体错位，正文显示的就变成
    【另一段代码】—— 编译不报错、PDF 照常生成，只是内容错了。
    这里每次构建都按标记重新定位，并把定位结果写成 tables/snip_<名字>.tex，
    正文用 \\input 引入。标记找不到就直接报错退出。
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# (片段名, 源文件, 起始标记, 终止标记——不含该行)
# 标记用源码里本来就有的注释或语句，每个在文件里必须恰好出现一次。
# 正文里写 \input{tables/snip_<片段名>}。
SNIPPETS = [
    # 例：("solver_step", "examples/solver.py", "# 动量预测", "# 投影到无散场"),
]


def locate(lines, marker, start=0):
    hits = [i for i in range(start, len(lines)) if marker in lines[i]]
    if len(hits) != 1:
        raise SystemExit(f"标记 {marker!r} 找到 {len(hits)} 处（应恰好 1 处）")
    return hits[0]


def main():
    os.makedirs(os.path.join(ROOT, "tables"), exist_ok=True)
    if not SNIPPETS:
        print("  （SNIPPETS 为空，没有要截取的代码片段）")
    for name, src, m_start, m_end in SNIPPETS:
        lines = open(os.path.join(ROOT, src), encoding="utf-8").read().split("\n")
        a = locate(lines, m_start)
        b = locate(lines, m_end, a + 1)
        last = b - 1
        while last > a and not lines[last].strip():
            last -= 1                       # 去掉片段末尾的空行
        first, last = a + 1, last + 1       # 转成 1 起算的行号
        out = os.path.join(ROOT, "tables", f"snip_{name}.tex")
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"% 自动生成：make_snippets.py，按标记 {m_start!r} 定位。不要手改。\n")
            f.write(r"\inputminted[autogobble=false,firstline=" + str(first)
                    + ",lastline=" + str(last) + "]{python}{" + src + "}\n")
        print(f"  片段 {name:14s} {src}:{first}-{last}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
