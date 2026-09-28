# LaTeX 工具链：tectonic（首选）与 XeLaTeX

## tectonic —— 无 sudo 的完整 LaTeX

```bash
brew install tectonic        # 普通 formula，不需要 sudo
tectonic --version           # 实测 0.17.0
tectonic -X compile main.tex # 首次运行会按需下载宏包，之后走本地缓存
```

单个二进制，宏包**按需自动下载**，不必预装几 GB 的 TeX Live，也不需要管理员权限。
基于 XeTeX，因此 `ctex` + 系统中文字体、TikZ、pgfplots、tcolorbox、algorithm2e、
biblatex 都能正常工作。

**实测**：`ctexart` + `amsmath` + `tcolorbox[most]` + `tikz` 的中文文档，
一次编译 3.3 秒，自动找到 macOS 的 Songti / Kaiti / STHeiti，无需任何字体配置。

会看到这类告警，**属正常**，不影响产物：

```
warning: accessing absolute path `/System/Library/Fonts/Supplemental/Songti.ttc`;
         build may not be reproducible in other environments
```

它只是提醒"换台机器可能没有这个字体"。要严格可复现就改用 TeX Live 自带的
`fandol` 字体族（`\documentclass[fontset=fandol]{ctexart}`）。

常用参数：

```bash
tectonic -X compile main.tex --keep-intermediates   # 保留 .aux/.log 便于排错
tectonic -X compile main.tex --outdir build/
tectonic -X watch                                   # 需先 tectonic -X new 建项目
```

tectonic 会自动决定编译轮数（解决交叉引用），不必像 xelatex 那样手动跑两遍。

使用本技能默认的 minted 代码高亮时，还需要 Pygments。装进项目自己的小环境，避免污染
系统 Python：

```bash
python3 -m venv .venv-doc
.venv-doc/bin/python -m pip install pygments
PATH="$PWD/.venv-doc/bin:$PATH" \
  tectonic -X compile main.tex --outdir . --keep-logs \
  -Z shell-escape-cwd="$PWD"
```

实测组合：Tectonic 0.17.0、minted 2.6、Pygments 2.21.0。`-Z shell-escape-cwd`
既启用 minted 所需的外部命令，又把命令工作目录固定在项目根目录；省掉它时常见症状是
`Package minted Error: You must invoke LaTeX with the -shell-escape flag`。`--untrusted`
会禁用 shell escape，不能与 minted 同用。只对自己下载并检查过的教程源码启用它。

## XeLaTeX + ctex

已有 TeX Live / MacTeX，或必须套用既有 `.tex` 项目与期刊模板时用这条。

**注意**：MacTeX / BasicTeX 是需要 sudo 的 pkg，agent 一般装不上。机器上没有 TeX 时
不要在安装上反复尝试 —— 装 tectonic。

## 导言区

```latex
\documentclass[11pt, fontset=macnew]{ctexart}   % macnew: 用 macOS 自带中文字体
\usepackage{amsmath, amssymb, amsthm}
\usepackage{graphicx, xcolor}
\usepackage[most]{tcolorbox}                     % 说明框
\usepackage{minted}                              % 代码（需 Pygments + shell escape）
\usepackage[colorlinks=true, linkcolor=blue]{hyperref}
\usepackage{siunitx}                             % 单位与数值
\usepackage{booktabs, caption}                   % 脚本生成的表格：三线表 + \captionof
\usepackage[top=2.4cm, bottom=2.4cm, left=2.2cm, right=2.2cm]{geometry}

% macnew 的等宽中文是 STFangsong，授权禁止嵌入（fsType=0x0002），读者那边会整片消失。
% 换成允许嵌入的字体。原因与检查方法见下文「等宽中文字体必须可嵌入」。
\setCJKmonofont{Hiragino Sans GB}
```

## 代码排版：默认 minted

`listings` 不依赖外部程序，但 Python 的关键字、类型、字符串和注释层次不够清楚；长代码
尤其难读。教程默认使用 minted，让 Pygments 负责词法高亮：

```latex
\usepackage{xcolor}
\usepackage{minted}
\definecolor{codebg}{HTML}{F6F8FA}
\usemintedstyle{friendly}
\setminted{
  fontsize=\small,
  bgcolor=codebg,
  breaklines=true,
  breakanywhere=true,
  linenos=true,
  numbersep=7pt,
  frame=lines,
  framesep=2mm,
  tabsize=4,
  autogobble=true
}
\setminted[text]{linenos=false}  % 只给必须逐字保留的报错、日志、命令用
```

源代码写成：

```latex
\begin{minted}{python}
def contact_step(mass: float, velocity: float) -> float:
    impulse = max(0.0, -mass * velocity)  # 地面只能推，不能拉
    return impulse
\end{minted}
```

## 程序输出：排成表格，不要贴 stdout

把 stdout 原样贴进 `minted{text}` 看似最"诚实"，读者却读不懂：表头是变量名缩写，
一排数字挤在一起，看不出每列是什么、在和谁比；对照组分成两个块，要来回翻着比。
实测一本教程交付后，读者拿着截图说"完全看不懂在干嘛"。

做法：算例脚本在构建时**直接生成表格源码**，正文 `\input`。用 `assets/tabular.py`
（复制到项目的 `examples/` 下）：

```python
from tabular import Table, num, mat, txt

t = Table("ex1_convergence", __file__, title="两种 eps 取法下的离散误差",
          caption=r"在解析 $\tanh$ 廓线上算离散的 $\beta$，理论值为 $0$。"
                  r"比值 $=$ 上一行误差 $\div$ 本行误差：二阶收敛时趋近 $4$。",
          columns=[("N", "$N$"), ("max|beta|", r"$\max|\beta|$"), ("比值", "比值"),
                   ("max|beta|", r"$\max|\beta|$"), ("比值", "比值")],
          groups=[("", 1), (r"$\epsilon$ 固定", 2), (r"$\epsilon=2.5h$", 2)])
t.row(num(64, "d"), num(0.3153466, ".6e"), None, num(0.3384232, ".6e"), None)
...
t.emit()   # 终端打印 + examples/out/tables/<id>.json + tables/<id>.tex
```

一次产出三份，来自同一批格式化后的字符串，所以正文数字和运行结果不可能对不上：

| 产物 | 给谁 |
|---|---|
| 终端里对齐的纯文本 | 跑脚本的人 |
| `examples/out/tables/<id>.json` | 核对脚本、作图脚本（作图数据从这里读，不再手抄） |
| `tables/<id>.tex` | 正文 `\input{tables/<id>}`，标签自动是 `tab:<id>` |

生成的表格是非浮动的（`minipage` + `\captionof`），紧跟在引出它的那句话后面，
标题在上、三线表、表注在下。排版细节由生成器统一处理：

- 尾数的每一位原样保留，只改写法：`3.153466e-01` → $3.153466\times10^{-1}$
- 恰好为零写 `0`（`+0.000e+00` 读成"+0.000"只会让人疑惑）
- 同一列里混有 $\times10^{k}$ 时，指数为 0 的也写出 $\times10^{0}$，免得一列两种写法
- 首列是数字就右对齐；矩阵单元格排成 `bmatrix`，行与行之间加空而不是整体拉大行距
  （`arraystretch` 会连矩阵内部一起撑开）

写标题时想清楚三件事：这张表**在比较什么**、**怎么读**、**哪一列能自查**。
表头用正式记号和单位，不用变量名。

仍然用 `minted{text}` 的场合只有一种：**文本本身就是要讲的对象**，必须逐字保留 ——
报错信息（`Error: mass and inertia of moving bodies must be larger than mjMINVAL`）、
日志行、命令。它们不是数据表。

Typst 项目同理：读同一份 JSON，用 `#table(...)` 渲染即可。

长文件不要复制进正文，用
`\inputminted[autogobble=false,firstline=40,lastline=65]{python}{examples/demo.py}`；
这样正文与实际运行文件共用一份源码。

**但行号不要手写。** 源码开头多一行 import，截取范围就整体下移，正文显示的变成另一段
代码 —— 编译通过、PDF 照常生成。用 `assets/make_snippets.py` 按源码里已有的注释标记
（如 `# 应力散度`）算出行号，写成 `tables/snip_<名字>.tex`，正文 `\input` 它；
标记找不到或出现多次就构建失败。中文注释可正常渲染，但图书式教程仍应优先让变量名和
结构本身说话，注释保持短。程序输出关闭行号；需要逐行讲解的源代码才保留行号。

这里的 `autogobble=false` 不能省：实测 minted 2.6 在全局 `autogobble=true` 时，
`\inputminted` 再叠加 `firstline/lastline` 会把所选区间处理成空块，轻则代码静默消失，
重则报 `FancyVerb Error: Empty verbatim environment`。行内 `minted` 环境仍可使用全局
autogobble；只有按行截取外部文件时显式关闭。

如果来源不可信、构建环境禁止 shell escape，或者无法提供 Pygments，退回 `listings`。
这是兼容方案，不要同时加载两个宏包并混用环境。

Linux 上 `fontset=macnew` 不可用，换 `fontset=ubuntu` 或 `fandol`（跨平台、随 TeX Live 分发）。

## 等宽中文字体必须可嵌入

PDF 里没嵌入的字体由**读者的机器**提供。你装了这个字体，打开一切正常；读者没装，
那些字就是空白。编译过程不报任何错，你自己的渲染检查也全部通过。

实测：ctex 的 `fontset=macnew` 在 `ctex-fontset-macnew.def` 里写着
`\setCJKmonofont{STFangsong}`。STFangsong 的 OS/2 表 `fsType=0x0002`（授权禁止嵌入），
xdvipdfmx 于是不嵌它，只在 PDF 里留下名字。结果代码注释、程序输出里的中文在读者那边
整片消失 ——"终态界面形状（沿 x 取 8 个点）"只剩"x 8"。

换字体前先查授权标志：

```python
from fontTools.ttLib import TTFont, TTCollection
f = TTCollection(path).fonts[i] if path.endswith(".ttc") else TTFont(path)
print(f["name"].getDebugName(6), hex(f["OS/2"].fsType))
# 0x0002 禁止嵌入；0x0004 仅预览打印；0x0008 可编辑嵌入；0x0000 无限制
```

`.ttc` 里各个成员的标志可能不同（Songti.ttc 里 SC-Black 是 `0x0002`，SC-Light/Bold 是
`0x0008`），要查你实际用到的那个。macOS 上 `Hiragino Sans GB`（冬青黑体，`0x0008`，
在 `/System/Library/Fonts/`）适合做等宽中文。

最后用 `assets/check_pdf_fonts.py main.pdf` 逐个检查 PDF 里的字体，
有一个没嵌入就返回 1 —— 放进 `build.sh`，让构建失败。

## 八类说明框

```latex
\newtcolorbox{cnbox}[2]{
  enhanced, breakable, colback=#1!6, colframe=#1,
  boxrule=0pt, leftrule=2.5pt, arc=2pt,
  left=8pt, right=8pt, top=6pt, bottom=6pt,
  fonttitle=\bfseries\small, coltitle=#1!80!black,
  title=#2, attach title to upper=\par
}
\newenvironment{intuition}{\begin{cnbox}{blue!70!black}{直觉图像}}{\end{cnbox}}
\newenvironment{beginner}{\begin{cnbox}{green!50!black}{给初学者}}{\end{cnbox}}
\newenvironment{derive}{\begin{cnbox}{orange!85!black}{推导补全}}{\end{cnbox}}
\newenvironment{pitfall}{\begin{cnbox}{red!75!black}{易错点}}{\end{cnbox}}
\newenvironment{history}{\begin{cnbox}{black!50}{历史与背景}}{\end{cnbox}}
\newenvironment{vernote}{\begin{cnbox}{violet!75!black}{版本注}}{\end{cnbox}}
\newenvironment{keypoints}{\begin{cnbox}{teal}{本节要点}}{\end{cnbox}}
\newenvironment{exercise}{\begin{cnbox}{brown!80!black}{思考题}}{\end{cnbox}}
```

## 目录结构与一键编译

```
main.tex          封面、导言、\input 各节
preamble.tex      宏包、说明框、数学宏（各章共用）
parts/p1_xxx.tex  正文按节拆开
figures/
  fig_xxx.tex     每图一个 standalone 源码
  figpre.tex      插图共用导言
  build_figs.sh   单独编译插图
build.sh          先编图，再编正文两遍（交叉引用）
```

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for f in examples/ex*.py; do           # 跑算例：stdout 落盘，同时生成 tables/*.tex
    python "$f" > "examples/out/$(basename "$f" .py).txt"
done
python make_snippets.py                # 代码片段行号按标记生成
(cd figures && ./build_figs.sh)        # 再编图（数据从表格 JSON 读）
python verify_numbers.py               # 表格可重建、正文数字可追溯，否则失败

DOC_VENV="${DOC_VENV:-.venv-doc}"
if [ ! -x "$DOC_VENV/bin/pygmentize" ]; then
    python3 -m venv "$DOC_VENV"
    "$DOC_VENV/bin/python" -m pip install pygments
fi
export PATH="$PWD/$DOC_VENV/bin:$PATH"

if command -v tectonic >/dev/null; then
    tectonic -X compile main.tex --keep-logs \
      -Z shell-escape-cwd="$PWD"       # minted；自动决定编译轮数
else
    xelatex -shell-escape -interaction=nonstopmode main.tex
    xelatex -shell-escape -interaction=nonstopmode main.tex
fi
python check_pdf_fonts.py main.pdf     # 有字体没嵌入就失败
if grep -E "Overfull \\\\hbox|undefined references" main.log; then
    echo "日志里有溢出或未定义引用"; exit 1
fi
```

两个会让检查形同虚设的写法：

- `build.sh` 里用 `|| true` 吞掉编译错误 —— 实测一个旧 `build.sh` 就这样把失败的编译报成了成功
- 写成 `! grep ... main.log`：`set -e` **对用 `!` 取反的命令不生效**，找到溢出也照样往下跑。
  必须写成上面的 `if ...; then exit 1; fi`（实测验证过）

## 保留原著编号

```latex
\begin{equation}\tag{1.17}        % 原文编号，与原书一致
  E = mc^2
\end{equation}

\newcommand{\supeq}[1]{\tag{补1.#1}}   % 自己补的推导
```

## 插图用 standalone

每张图一个独立可编译的 `.tex`，好处是能单独重编一张、排错快：

```latex
% figures/fig_attention.tex
\documentclass[tikz, border=2pt]{standalone}
\input{figpre}                      % 共用颜色、字体、pgfplots 设置
\begin{document}
\begin{tikzpicture} ... \end{tikzpicture}
\end{document}
```

正文里 `\includegraphics{figures/fig_attention.pdf}`。

排错：出错先看 `.log` 里第一个 `!` 开头的行，后面的报错多是它的连锁反应。
中文相关的错误九成是字体名或 `fontset` 不对。
