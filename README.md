# zh-tutorial-skills

给 AI coding agent 用的**中文技术教程写作技能**。

把论文 / 英文教材 / 讲义 / 自己的实验结果，做成一本能本地一键编译、
**每个数字和每张图都可复算**的中文教程 PDF。

目前收录一个技能：

| 技能 | 做什么 |
|---|---|
| [`zh-tutorial-pdf`](zh-tutorial-pdf/) | 中文教程 / 讲解版 PDF 的完整流程 |

## 它解决的是什么问题

让模型写中文说明文字是最不容易出错的部分。真正会翻车的是别的地方，
这个技能全部围绕它们：

| 翻车点 | 表现 |
|---|---|
| **不知道读者卡在哪** | 自以为讲清楚了，读者第三页就停住 |
| **编译链没闭环** | 写了一万字交不出 PDF；中文变豆腐块 |
| **没拿到原始材料** | 全凭记忆复述论文，公式记号与原文对不上 |
| **讲得抽象** | 通篇符号推导，读完仍不知道数据长什么样 |
| **数字是"编"的** | 正文数值与代码输出对不上，一核就穿 |
| **图挤成一团** | 文字重叠、箭头含义不明、字被裁掉 |

几条比较硬的规矩：

- **动笔前用 8 道题在依赖图上定位读者的边界。**
  "不要堆砌概念"这条要求你无法自查 —— 你已经懂了，那道坎在你眼里就是平地，只能去测。
  方法照搬**知识空间论 / ALEKS**：`A 很熟 → 剪枝，C 不懂 → 展开`，在依赖图上做二分。
- **动笔前先编出一页测试 PDF**（中文 + 公式 + 插图 + 代码块），
  别攒了几千字才发现编不出来。
- **正文里每个数字都由脚本跑出来**，收尾做一次机器比对：
  文档里所有代码块逐行 grep 真实 stdout。
- **每个关键结论配一条路径不同源的交叉验证**（解析解 / 守恒量 / 高精度重算 / 多实现互校）。
- **每张图画完必须渲染成 PNG 亲眼看过**。压字、遮挡、被裁，代码都不会报错。

## 安装

技能是一个目录，放进 agent 的 skills 目录即可。

**Claude Code**

```bash
git clone https://github.com/fzj1214/zh-tutorial-skills.git
mkdir -p ~/.claude/skills
ln -s "$PWD/zh-tutorial-skills/zh-tutorial-pdf" ~/.claude/skills/
```

**Codex / 其他读同样格式的 agent**

```bash
mkdir -p ~/.codex/skills
ln -s "$PWD/zh-tutorial-skills/zh-tutorial-pdf" ~/.codex/skills/
```

用软链接的好处是 `git pull` 之后几个 agent 同时生效。也可以直接 `cp -R`。

装好后在会话里 `/zh-tutorial-pdf` 调用，或者直接说"把这篇论文做成中文教程 PDF"。

## 目录

```
zh-tutorial-pdf/
  SKILL.md                     主流程，§0 ~ §9
  assets/
    template.typ               Typst 模板：封面 + 八类彩色说明框
    worked_example.py          可直接运行的算例范本（单头自注意力，逐矩阵打印）
  references/
    knowledge-graph.md         读者知识图：schema、8 题算法、三个诊断
    latex.md                   tectonic / XeLaTeX + ctex，中文字体
    typst.md                   Typst 方案
    sources.md                 抓论文 TeX 源码与参考实现
    worked-examples.md         "用真实数字走完整条流程"的方法与范例
    verification.md            数值可追溯、机器比对、交叉验证
    figures.md                 插图版面计算与强制检查清单
```

`SKILL.md` 是入口，`references/` 按需加载，不会一次性全进上下文。

## 关于那 8 道题

这不是客套，是有形式化基础的。「懂 A 才能懂 B」在**知识空间论**
（Doignon & Falmagne, 1985）里叫 surmise relation，依赖结构能把状态空间从 2³¹⁴ ≈ 10⁹⁴
压到 ~10²³ —— ALEKS 就是靠这个用 25~30 题定位一个学生。

我们只有一个读者、十几个概念，所以 **8 题够**：不需要建可复用的群体模型，
只需要知道这份文档的边界在哪。规则就两条：

```
A 很熟   → 剪枝：它依赖的一切一并视为已知，整条支线不再问
C 不懂   → 展开：把它的依赖加进下一轮
```

**但不要试图建全局知识图谱。** Cyc 手工编本体从 1984 年干到现在，
2002 年就烧掉 6000 万美元、600 人年，赌的那个"知道多了就能自己学"的临界点从未到达。
更根本的是：**先修关系不是客观的**，同一主题走不同教学路线就是不同的图，
没有唯一正确的图可供穷尽。所以只建**每份文档一张、从根节点懒展开**的局部图。

## 工具链

默认用 [tectonic](https://tectonic-typesetting.github.io/)：单二进制、**不需要 sudo**、
宏包按需自动下载，完整 LaTeX 生态可用。实测 ctex + 中文 + TikZ 一次编译约 3 秒。

```bash
brew install tectonic
```

也支持 XeLaTeX + ctex（机器已有 TeX Live 时）和 [Typst](https://typst.app/)（想要极简依赖时）。

## 许可

MIT，见 [LICENSE](LICENSE)。
