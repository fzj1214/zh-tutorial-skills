# Typst 工具链（首选）

无需 sudo、单二进制、编译以毫秒计、直接用系统中文字体。没有 TeX 的机器上这是唯一能
让 agent 自己闭环的选择。

```bash
brew install typst          # 普通 formula，不需要 sudo
typst --version
typst fonts | grep -iE 'songti|heiti|libertinus|menlo'   # 先确认字体存在
```

骨架直接复制 `../assets/template.typ`（已验证可编译，含八类说明框定义）。

## 日常命令

```bash
typst compile main.typ main.pdf
typst watch   main.typ main.pdf          # 写作时开着，保存即重编

# 抽查排版：渲染成 PNG 亲眼看（agent 无法"看" PDF，必须转图）
typst compile main.typ "/tmp/pg{n}.png" --format png --ppi 110
```

**每完成一章就渲染几页看一眼。** 图注压字、表格出血、分页把图和正文拆散，
这些编译器都不报错，只有看图才能发现。

## 语法坑（实测踩过）

| 坑 | 症状 | 正解 |
|---|---|---|
| `diff` | `unknown variable: diff` | 偏导用 `partial`：`$partial g\/partial x$` |
| 正文里的 `#1`、`#2` | 报错或吞内容 | `#` 在 markup 里进入代码模式。表格序号写 `[1]`，或转义 `\#1` |
| 分式斜杠 | 排版错乱 | 数学里写 `\/`（如 `$5\/3$`），`/` 是 Typst 的运算符 |
| 图片路径 | `file not found` | 路径相对于 **项目根**，不是当前工作目录。从 `doc/` 编译就写 `figures/x.svg` |
| 中文不显示 | 豆腐块 | `#set text(font: ("Libertinus Serif", "Songti SC"))` —— 西文字体在前，中文回退在后 |

数学里多字母标识符会被当变量逐字排版，函数名要加引号：`$"softmax"(x)$`、`$"Attention"(Q,K,V)$`。
`sin` `cos` `log` `exp` `max` `min` 等是内置的，不用加。

## 公式编号：保留原著编号 + 自增编号

改写英文原著时，原文公式保留原编号，自己补的另起一套，读者才能对照原书：

```typst
// 原文公式：手动给编号，与原书一致
$ E = m c^2 $ <eq-1-17>
#place(right, dy: -1.7em)[(1.17)]

// 自己新增的推导：用「补」前缀，与原文区分
#set math.equation(numbering: n => "(补1." + str(n) + ")")
```

## 与 LaTeX 的取舍

Typst 的短板：期刊模板生态、`biblatex` 级别的文献功能、成熟的 `algorithm2e` 伪代码宏包。
如果文档要投稿或必须套用既有 `.tex` 模板，走 `latex.md`；自用教程/讲义/报告，Typst 更省事。
