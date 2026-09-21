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
\usepackage{listings}                            % 代码
\usepackage[colorlinks=true, linkcolor=blue]{hyperref}
\usepackage{siunitx}                             % 单位与数值
\usepackage[top=2.4cm, bottom=2.4cm, left=2.2cm, right=2.2cm]{geometry}
```

Linux 上 `fontset=macnew` 不可用，换 `fontset=ubuntu` 或 `fandol`（跨平台、随 TeX Live 分发）。

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
(cd figures && ./build_figs.sh)        # 先把 TikZ 图编成 pdf

if command -v tectonic >/dev/null; then
    tectonic -X compile main.tex       # 自动决定编译轮数
else
    xelatex -interaction=nonstopmode main.tex
    xelatex -interaction=nonstopmode main.tex   # 第二遍解决交叉引用与目录
fi
```

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
