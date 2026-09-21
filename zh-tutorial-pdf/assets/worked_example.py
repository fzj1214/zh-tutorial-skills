"""
算例脚本模板：用真实数字把一条流程从头走到尾，并直接生成 LaTeX 表格源码。

教程正文里的每个数字都应当由这类脚本产出，禁止手算誊抄。
脚本同时打印「人看的」和「排版用的」两种形式，后者直接粘进 .tex 即可。

本例：单头自注意力，T=3 个 token，d_model=4，d_k=2。
维度取小到能印在纸上，又大到仍能暴露转置与形状问题（d=1 会把错误藏起来）。

用法：python3 worked_example.py
"""

import math

# ---------------------------------------------------------------- 输入与权重
# 权重刻意取「不漂亮」的值：全 1 或单位阵会让算错也看不出来。

X = [                      # (T=3, d_model=4)  三个 token 的输入表示
    [1.0, 0.0, 2.0, 1.0],  # token 1  "猫"
    [0.0, 2.0, 1.0, 0.0],  # token 2  "坐"
    [1.0, 1.0, 0.0, 2.0],  # token 3  "垫"
]
W_Q = [[0.5, 0.0], [0.0, 1.0], [1.0, 0.5], [0.0, 0.5]]   # (4, 2)
W_K = [[1.0, 0.5], [0.5, 0.0], [0.0, 1.0], [0.5, 0.5]]   # (4, 2)
W_V = [[0.0, 1.0], [1.0, 0.0], [0.5, 0.5], [1.0, 1.0]]   # (4, 2)

TOKENS = ["猫", "坐", "垫"]


# ---------------------------------------------------------------- 线性代数
def matmul(A, B):
    """(n,k) x (k,m) -> (n,m)"""
    n, k, m = len(A), len(B), len(B[0])
    assert len(A[0]) == k, f"形状不匹配: {len(A[0])} vs {k}"
    return [[sum(A[i][p]*B[p][j] for p in range(k)) for j in range(m)]
            for i in range(n)]


def transpose(A):
    return [list(col) for col in zip(*A)]


def softmax_rows(A):
    """按行 softmax；减去行最大值以避免 exp 溢出（数值稳定写法）"""
    out = []
    for row in A:
        mx = max(row)
        exps = [math.exp(v - mx) for v in row]
        s = sum(exps)
        out.append([e/s for e in exps])
    return out


# ---------------------------------------------------------------- 输出helper
def show(name, M, shape_note=""):
    """人看的形式"""
    print(f"\n{name}  {shape_note}")
    for row in M:
        print("   [" + "  ".join(f"{v:7.4f}" for v in row) + "]")


def latex_matrix(M, fmt="{:.4f}"):
    """排版用：直接粘进 .tex 的 bmatrix 源码"""
    body = r" \\ ".join(" & ".join(fmt.format(v) for v in row) for row in M)
    return r"\begin{bmatrix} " + body + r" \end{bmatrix}"


# ---------------------------------------------------------------- 逐步计算
def main():
    d_k = len(W_Q[0])

    print("=" * 66)
    print("单头自注意力算例：T=3, d_model=4, d_k=2")
    print("=" * 66)

    show("X  输入", X, "(T=3, d_model=4)")

    Q = matmul(X, W_Q)
    K = matmul(X, W_K)
    V = matmul(X, W_V)
    show("Q = X W_Q", Q, "(3, 2)")
    show("K = X W_K", K, "(3, 2)")
    show("V = X W_V", V, "(3, 2)")

    scores = matmul(Q, transpose(K))
    show("S = Q K^T  未缩放打分", scores, "(3, 3)")

    scaled = [[v/math.sqrt(d_k) for v in row] for row in scores]
    show(f"S / sqrt(d_k),  sqrt({d_k}) = {math.sqrt(d_k):.4f}", scaled, "(3, 3)")

    A = softmax_rows(scaled)
    show("A = softmax(S/sqrt(d_k))  注意力权重", A, "(3, 3)")

    # 给读者的自查点：softmax 每行必须和为 1
    print("\n   检查点：A 每行之和 =",
          "  ".join(f"{sum(r):.10f}" for r in A), " (应当都是 1)")

    out = matmul(A, V)
    show("Out = A V  输出", out, "(3, 2)")

    # 逐 token 用文字说一遍，比只给矩阵更容易懂
    print("\n   逐 token 解读：")
    for i, tok in enumerate(TOKENS):
        parts = "  ".join(f"{TOKENS[j]}:{A[i][j]:.3f}" for j in range(len(TOKENS)))
        print(f"     token{i+1} 「{tok}」把注意力分给 —— {parts}")

    # ------------------------------------------------------------ 排版用输出
    print("\n" + "=" * 66)
    print("以下为 LaTeX 源码，直接粘进正文（切勿手抄数字）")
    print("=" * 66)
    for name, M in (("X", X), ("Q", Q), ("K", K), ("A", A), ("Out", out)):
        print(f"\n% {name}")
        print(f"{name} = {latex_matrix(M)}")


if __name__ == "__main__":
    main()
