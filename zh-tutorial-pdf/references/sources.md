# 原始材料：先下载，再动笔

凭记忆复述论文是这类教程最隐蔽的错误来源 —— 记号会漂移、系数会记错、
版本会张冠李戴，而且写出来读着很顺，不容易被发现。**动笔前先把材料抓到本地。**

## 论文 TeX 源码（首选）

arXiv 对绝大多数论文提供完整的 LaTeX 源码打包：

```bash
mkdir -p sources/attention && cd sources/attention
curl -L -o src.tar.gz "https://arxiv.org/e-print/1706.03762"   # 用 arXiv ID
tar xzf src.tar.gz
ls        # ms.tex  model_architecture.tex  background.tex  Figures/ ...
```

实测 `1706.03762` 得到 2.0 MB，含全部 `.tex` 正文与原始插图 PNG。

拿到源码的好处：

- **逐字引用定义与公式**，记号与原文严格一致，不靠转述
- **照搬原图**（若许可允许）或以原图的 TikZ/数据为基础重绘中文版
- 看到论文里被编译隐藏的东西：注释掉的段落、`\newcommand` 定义的记号约定

没有源码时退而求其次下载 PDF：

```bash
curl -L -o paper.pdf "https://arxiv.org/pdf/1706.03762"
pdftotext -layout paper.pdf paper.txt     # 抽文字层，便于检索与引用
```

## 参考实现与数据

- **官方仓库**：论文脚注或 `paperswithcode.com` 上找；`git clone --depth 1` 即可
- **权重 / 数据集**：HuggingFace Hub、官方发布页
- **体积门槛**：几百 MB 以内就下；过大的只在 `sources/README.md` 里
  记录获取命令、版本号与校验和，不要往仓库里塞

```
sources/
  attention/         论文源码（解包后）
  annotated-transformer/   参考实现
  README.md          每一项的来源 URL、下载日期、commit / 版本号
```

**记录下载日期与 commit hash**。代码仓库会变，半年后读者照着走不通，
有 commit 至少能定位到当时的状态。

## 写作时：原文与代码必须对照着讲

这是教程最有价值的部分，也是只有做了上面两步才写得出来的部分。三件事要摆在一起：

1. **论文怎么写的**（公式 + 原文措辞）
2. **代码实际怎么算的**（贴关键几行真实源码，不要伪代码）
3. **两者的差异**

差异几乎总是存在，而且往往正是初学者卡住的地方：

| 常见差异 | 例子 |
|---|---|
| 论文省略的数值细节 | LayerNorm 里的 $\epsilon$、softmax 前减最大值 |
| 代码多出的工程步骤 | dropout、梯度裁剪、混合精度下的 cast |
| 维度顺序不同 | 论文 $(T, d)$，实现里是 $(B, T, d)$ 甚至 $(T, B, d)$ |
| 等价但不同的写法 | 三个独立投影 vs 一个大矩阵切三份 |
| 论文与官方实现本身不一致 | 残差与 LayerNorm 的先后（post-LN / pre-LN） |

写法示例：

> 论文式 (1) 写作 $\mathrm{LN}(x)=\gamma\odot\frac{x-\mu}{\sigma}+\beta$，
> 但实现里分母是 $\sqrt{\sigma^2+\epsilon}$（`torch/nn/modules/normalization.py`，
> 默认 `eps=1e-5`）。省掉 $\epsilon$ 在数学上无妨，工程上会在
> 某一行全为同一个值时除零 —— 这正是 §5 算例里那个检查点要验的东西。

## 引用与许可

- 引用原文图表要注明出处；大段照搬前先确认许可（arXiv 多为
  CC-BY / arXiv 非独占许可，但**逐篇确认**，不要一概而论）
- 自己重绘的图注明"据原文图 N 重绘"
- 参考文献在教程末尾列全，给 arXiv ID 与 DOI
