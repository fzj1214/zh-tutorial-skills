# 图表：纪律与实测踩过的坑

## 五条纪律

1. **图由代码生成，源码入库，一条命令可重建。** matplotlib 或 TikZ 均可。
   不贴截图、不手画 —— 审阅时要改一个坐标范围或配色，没有源码就得重画。
2. **版面要算，不要试。** 见下节。
3. **箭头必须有明确语义。** 见下节。
4. **渲染成 PNG 亲眼看过才算画完。** 代码跑通 ≠ 图是对的。标注压字、图例遮数据、
   坐标轴被离群点撑开、曲线互相完全覆盖 —— 这些编译器和解释器都不报错。
5. **图内文字一律英文，中文说明放图注。** 见下面的字形坑。

## 版面要算，不要试

挤成一团、文字重叠，根源都是"随手放一个坐标再看看效果"。正确做法是把位置**算出来**。

**TikZ**：用具名节点 + `positioning` 库声明相对关系，不要撒魔法坐标。

```latex
\usetikzlibrary{positioning, arrows.meta, fit, backgrounds}
\begin{tikzpicture}[
    node distance = 8mm and 14mm,          % 行距 and 列距，全图统一
    box/.style   = {draw, rounded corners=2pt, minimum width=22mm,
                    minimum height=8mm, align=center, font=\small},
]
  \node[box] (emb)  {Embedding};
  \node[box, right=of emb] (attn) {Multi-Head\\Attention};   % 相对定位
  \node[box, right=of attn] (ffn)  {Feed-Forward};
\end{tikzpicture}
```

`minimum width` / `align=center` / 统一的 `node distance` 三件套能消掉绝大多数重叠。
文字长的节点用 `text width=24mm` 强制换行，而不是任它撑破版面。

**matplotlib**：显式设 `xlim`/`ylim`（否则越界数据会把坐标轴撑开、留大片空白），
标注锚点必须落在可见范围内，密集处用 `offset points` 加引线引到空白区。
需要精确知道文字占多大时用 `renderer.get_text_width_height_descent()`
或先 `fig.canvas.draw()` 再取 `get_window_extent()`。

**空间不够时减少内容或拆成两张图，不要缩字号。** 图里字号小于正文的 70% 就该拆了。

## 箭头必须有明确语义

一张图里每种箭头只表达一个意思，不同含义用不同样式，超过一种就配图例：

| 含义 | 建议样式 |
|---|---|
| 数据前向流动 | 实线 `-{Stealth}` |
| 梯度反传 | 虚线 `-{Stealth}`，另一种颜色 |
| 残差 / 跳连 | 曲线 `to[out=,in=]`，细一号 |
| 可选路径 | 点线 |

```latex
\draw[-{Stealth[length=2.2mm]}, thick]        (emb) -- (attn);      % 前向
\draw[-{Stealth[length=2.2mm]}, dashed, gray] (ffn) to[bend left=25] (attn);  % 反传
```

箭头要连**节点边界**而不是中心（TikZ 用具名节点自动做到），起止点悬空或穿过别的节点
都是明显的错误。箭头上有标签时用 `node[midway, above, font=\footnotesize]`，
并确认它没压到线。

配色：若环境里有 `dataviz` 技能，先调它并按它的校验脚本验色板。没有的话用下面这组
（已验证的定性色板，按固定顺序取用，不要打乱、不要循环复用）：

```
slot 1 蓝 #2a78d6   slot 2 绿 #008300   slot 3 洋红 #e87ba4   slot 4 黄 #eda100
slot 5 青 #1baf7a   slot 6 橙 #eb6834   slot 7 紫 #4a3aa7   slot 8 红 #e34948
发散色阶（数据关于 0 对称时）：蓝 ↔ 灰中点 #f0efec ↔ 红，绝不用彩虹色
顺序色阶（单调量）：单一色相由浅到深
```

洋红与黄在白底上对比度偏低：用到它们时必须配直接标注或不同 marker/线型作次级编码
（科学制图本来就该这么做，黑白打印也能区分）。

## 实测踩过的坑

### matplotlib 缺中文字形

```
UserWarning: Glyph 19981 (\N{CJK UNIFIED IDEOGRAPH-4E0D}) missing from font(s) DejaVu Sans
```

默认字体没有汉字，中文会**静默**变成豆腐块。两种处理：

- **推荐**：图内全用英文（`iteration n`、`diverges`、`saddle`），中文放图注。
- 必须用中文时显式指定：`plt.rcParams["font.sans-serif"] = ["Songti SC"]`，
  并加 `plt.rcParams["axes.unicode_minus"] = False`（否则负号变方块）。

### contourf / 大量散点导出 SVG 体积爆炸

41 层填充等高线导出 SVG 有 **4.3 MB**。把背景层光栅化，线条文字仍保持矢量：

```python
ax.set_rasterization_zorder(2)      # zorder < 2 的图层光栅化
ax.contourf(..., zorder=1)          # 填充放到 zorder=1
ax.contour(...,  zorder=2)          # 等值线保持矢量
plt.rcParams["savefig.dpi"] = 220
```

4.3 MB → 382 KB，肉眼无差别。**注意**：`contourf(..., rasterized=True)` 对
`QuadContourSet` **不生效**（实测 SVG 里没有内嵌位图），必须用 `set_rasterization_zorder`。

验证是否生效：`grep -c 'image/png' out.svg`，应 ≥ 1。

### 标注被裁到图外 / 互相压字

标注锚点若落在 `ylim` 之外会被静默裁掉。锚到**仍在可见范围内**的最后一个点：

```python
idx = max((i for i in range(n) if errs[i] >= Y_FLOOR), default=n-1)
ax.annotate(label, xy=(xs[idx], errs[idx]), xytext=(7, 7), textcoords="offset points")
```

多条曲线终点挤在一角时，把标注引到空白处并画细引线（`arrowprops=dict(arrowstyle="-")`）。

### 坐标轴被画面外的数据撑开

轨迹/曲线跑出网格范围时，matplotlib 会自动扩展坐标轴，留下大片空白边。
**显式设定 `set_xlim` / `set_ylim`**，让越界部分自然裁掉。

### 两条曲线完全重合，下面那条看不见

这往往是**正确的物理结果**（例如混合法每步都取了 Newton 步，两条收敛曲线本就重合）。
不要改数据，把上层曲线改成虚线让下层透出来，并在图注里说明两者重合。

### 状态标志一词多义

给曲线标 `(diverges)` 时用了"是否在 `max_iter` 内达到收敛判据"这个标志，
结果把**步长太小、只是还没迭代完**的情形误标成发散 —— 图上写着假话。

判据要对应真实含义：判断发散就看误差**本身**有没有实质下降。

```python
converging = errs[-1] < 1e-6 * errs[0]     # 而不是复用 max_iter 的返回标志
```

一个布尔量不要承担两种语义。

### SVG 字体依赖

`plt.rcParams["svg.fonttype"] = "path"` 把文字转成路径。这样 SVG 在别的机器、
别的排版器里渲染都一致，不依赖字体是否安装。代价是文件略大、文字不可选中 —— 对插图值得。

## 强制检查：画完必须看

**这一步不可跳过。** 代码不报错不等于图是对的，而错图进了教程比没有图更糟。

```bash
# matplotlib：直接存一份 PNG 用来检查
python3 make_figures.py && open /tmp/figs/*.png

# TikZ / LaTeX：编译后转 PNG
tectonic -X compile fig.tex && sips -s format png --out fig.png fig.pdf
#   或 pdftoppm -png -r 150 fig.pdf fig

# Typst 文档：整页渲染抽查
typst compile main.typ "/tmp/pg{n}.png" --format png --ppi 110
```

然后**逐项核对**，不是"扫一眼觉得还行"：

- [ ] 有没有任何两段文字重叠、或文字压在线/色块上
- [ ] 标注有没有被坐标轴边界裁掉
- [ ] 图例有没有遮住数据
- [ ] 坐标轴范围是否被离群点撑开，留出大片空白
- [ ] 每个箭头起止是否都落在节点边界，语义是否一致
- [ ] 元素之间是否挤成一团（相邻文字间距 < 字高的一半就算挤）
- [ ] 完全重合的曲线是否都能看见
- [ ] 图内有没有混进中文
- [ ] 单个图文件 < 1 MB（超了先查矢量爆炸）

发现问题就改代码重画，不要"下次注意"。
