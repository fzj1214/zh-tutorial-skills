// 中文技术教程 PDF 骨架（Typst ≥ 0.12）
// 编译：typst compile template.typ template.pdf
// 用法：把本文件复制为 main.typ，改标题与作者，正文用 #include "parts/xx.typ" 引入。

#let title = "教程标题"
#let subtitle = "副标题"
#let author = "作者"
#let date = "2026 年 9 月"

// ---------------------------------------------------------------- 页面与字体
// 中文宋体正文 / 黑体标题 / 西文 Libertinus / 等宽 Menlo —— 均为 macOS 自带。
// 换机器前先 `typst fonts | grep -i songti` 确认，不要假设存在。
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.4cm),
          numbering: "1 / 1", number-align: center)
#set text(font: ("Libertinus Serif", "Songti SC"), size: 10.5pt, lang: "zh")
#set par(justify: true, leading: 0.78em, first-line-indent: 2em)
#set heading(numbering: "1.1")
#show heading: it => {
  set text(font: ("Libertinus Serif", "Heiti SC"), weight: "bold")
  set par(first-line-indent: 0em)
  block(above: 1.3em, below: 0.75em, it)
}
#show raw: set text(font: "Menlo", size: 8.4pt)
#show raw.where(block: true): it => block(
  fill: rgb("#f5f5f3"), inset: 8pt, radius: 3pt, width: 100%, it,
)
#set figure(gap: 0.9em)
#show figure.caption: set text(size: 9pt)
#set table(stroke: 0.5pt + rgb("#bfbfba"), inset: 6pt)
#show table.cell.where(y: 0): set text(weight: "bold")

// ---------------------------------------------------------------- 八类说明框
// 教程区别于文档的核心。写第一节前就把类型定死，中途新增会前后不一致。
// 同一类内容永远用同一个框——读者靠颜色导航。

#let callout(name, body, color: rgb("#2a78d6")) = block(
  width: 100%, breakable: true,
  fill: color.lighten(93%),
  stroke: (left: 2.5pt + color),
  inset: (x: 10pt, y: 8pt),
  radius: (right: 3pt),
)[
  #set par(first-line-indent: 0em)
  #text(weight: "bold", fill: color.darken(20%), size: 9.5pt)[#name]
  #linebreak()
  #body
]

#let intuition(body) = callout("直觉图像", body, color: rgb("#2a78d6"))   // 蓝
#let beginner(body)  = callout("给初学者", body, color: rgb("#008300"))   // 绿
#let derive(body)    = callout("推导补全", body, color: rgb("#eb6834"))   // 橙
#let pitfall(body)   = callout("易错点",   body, color: rgb("#e34948"))   // 红
#let history(body)   = callout("历史与背景", body, color: rgb("#6b6b66")) // 灰
#let vernote(body)   = callout("版本注",   body, color: rgb("#7b4ea8"))   // 紫
#let keypoints(body) = callout("本节要点", body, color: rgb("#1baf7a"))   // 青
#let exercise(body)  = callout("思考题",   body, color: rgb("#8a6642"))   // 棕

// ---------------------------------------------------------------- 封面
#align(center)[
  #text(size: 17pt, font: ("Libertinus Serif", "Heiti SC"), weight: "bold")[#title]
  #v(0.3em)
  #text(size: 12pt)[#subtitle]
  #v(0.8em)
  #text(size: 10.5pt)[#author]
  #v(0.2em)
  #text(size: 10pt, fill: rgb("#52514e"))[#date]
]
#v(0.6em)
#line(length: 100%, stroke: 0.5pt + rgb("#bfbfba"))
#v(0.4em)

// ================================================================ 正文示例
// 实际项目中这里换成 #include "parts/ch1.typ" 等

= 示例章节

行内公式 $q = W_Q x$，行间公式：

$ "Attention"(Q, K, V) = "softmax"(frac(Q K^top, sqrt(d_k))) V. $

#intuition[
  先给直觉再上数学。缩放因子 $1\/sqrt(d_k)$ 的作用是：$d_k$ 越大，$Q K^top$ 的方差越大，
  softmax 会被推向饱和区导致梯度消失，除以 $sqrt(d_k)$ 把方差拉回 $O(1)$。
]

#pitfall[
  张量形状务必标注并全文统一：$Q, K, V$ 的形状为 $(B, T, d_k)$，
  注意力矩阵为 $(B, T, T)$。读者的困惑九成来自形状对不上。
]

#vernote[
  截至 2026-09：示例代码基于 PyTorch 2.x。涉及具体模型 ID 与 API 形态的内容
  请在此类框中标明日期与版本，这是 AI 教程半年就过期的主因。
]

#keypoints[
  - 说明框只在有话可说时用，不必每节凑满八类。
  - 图内文字用英文，中文说明放图注。
]
