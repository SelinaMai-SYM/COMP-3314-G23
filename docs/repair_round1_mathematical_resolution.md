# 第一轮修复：式 (8) 与式 (13) 的独立推导

日期：2026-10-20。范围只到数学变体和 \(n=6\) 的凸核对。没有跑 ORL / YaleB 诊断，也没有改报告。

来源是 Chang, Nie, Ma, Yang, Zhou，*A Convex Formulation for Spectral Shrunk Clustering*，AAAI 2015，`9736-45063-1-PB.pdf` 的式 (8)–(13)、Algorithm 1 和收敛证明里的式 (14)–(18)。下面的系数是按这些印出的式子重新求导得到的，不沿用 `docs/ssc_mathematical_audit.md` 的结论当证据。旧审计里的因子 2 与这次推导一致，但数值以本文记录的 CVXPY 运行为准。

记号：样本按行。\(G,F\in\mathbb{R}^{n\times c}\)，\(g_i,f_i\in\mathbb{R}^c\) 是第 \(i\) 行。\(W\) 对称，对角线为 0，两条有向边都存着。\(\widetilde L=\widetilde D-\widetilde W\) 是组合拉普拉斯，\(\widetilde D_{ii}=\sum_j\widetilde W_{ij}\)。

## 印出的对象

式 (8) 是

\[
\min_G \lVert G-F\rVert_{2,1}+\gamma\sum_{i,j}W_{ij}\lVert g_i-g_j\rVert_2,
\qquad
\lVert H\rVert_{2,1}=\sum_i\lVert h_i\rVert_2,
\]

\(h_i\) 是 \(H=G-F\) 的第 \(i\) 行。\(\sum_{i,j}\) 把对称 \(W\) 的两个有序对都加进去。实现里的 `equation8_objective` 就是这个和。

式 (10) 把 \(S\) 写成嵌入维数那么长的对角，\(H=[h_1,\ldots,h_d]\)。式 (11) 是 \(\widetilde W_{ij}=W_{ij}/(2\lVert g_i-g_j\rVert_2)\)。式 (12) 写成

\[
\operatorname{Tr}((G-F)^\top S(G-F))+\gamma\operatorname{Tr}(G^\top\widetilde L G),
\]

式 (13) 是它的驻点 \(G=(S+\gamma\widetilde L)^{-1}SF\)。Algorithm 1 第 10 行写成 \((S_t+\gamma\widetilde W)^{-1}S_t X\)。证明里的式 (15) 最小化

\[
f(G)+\gamma\sum_{i,j}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2,
\qquad
f(G)=\operatorname{Tr}((G-F)^\top S(G-F)).
\]

## 系数是 2

在 \(h_k\neq 0\) 且所有用到的边长都非零时，式 (8) 对第 \(k\) 行的梯度是

\[
\frac{\partial}{\partial g_k}\lVert h_k\rVert_2
=\frac{h_k}{\lVert h_k\rVert_2}
=2S_{kk}h_k,
\qquad
S_{kk}=\frac{1}{2\lVert h_k\rVert_2}.
\]

图项 \(\phi(G)=\sum_{i,j}W_{ij}\lVert g_i-g_j\rVert_2\) 对 \(g_k\) 有两部分：\(i=k\) 的项，以及 \(j=k\) 的项。\(W\) 对称时这两部分相同，所以

\[
\frac{\partial\phi}{\partial g_k}
=2\sum_j W_{kj}\frac{g_k-g_j}{\lVert g_k-g_j\rVert_2}.
\]

代入式 (11)，\(W_{kj}(g_k-g_j)/\lVert g_k-g_j\rVert_2=2\widetilde W_{kj}(g_k-g_j)\)，而 \((\widetilde LG)_k=\sum_j\widetilde W_{kj}(g_k-g_j)\)。于是

\[
\frac{\partial\phi}{\partial g_k}=4(\widetilde LG)_k.
\]

式 (8) 的梯度是 \(2S(G-F)+4\gamma\widetilde LG\)。令它为零并除以 2：

\[
(S+2\gamma\widetilde L)G=SF.
\]

同一个因子从式 (15) 再出来一次。对称权重下

\[
\sum_{i,j}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2
=2\operatorname{Tr}(G^\top\widetilde L G).
\]

因此式 (15) 的二次部分是 \(f(G)+2\gamma\operatorname{Tr}(G^\top\widetilde L G)\)，驻点仍是 \((S+2\gamma\widetilde L)G=SF\)。式 (12) 少写了这个 2，所以式 (13) 的图系数是 \(\gamma\)，对应的是把式 (8) 的图项改成 \((\gamma/2)\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\) 之后的驻点。

两点的手算和这个恒等式一致。\(g=(0.2,0.8)\)，\(W_{01}=W_{10}=1\)，距离 \(0.6\)：

| 量 | 值 |
| --- | --- |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.72\) |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\) | \(1.2\) |
| \(\widetilde W_{01}=1/(2\cdot 0.6)\) | \(5/6\) |
| \(\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.6\) |
| \(\operatorname{Tr}(G^\top\widetilde L G)\) | \(0.3\) |

\(0.6=2\times 0.3\)。在展开点上，这条边的二次主化项等于图项的一半，再乘上引理里的常数才回到原来的范数。二次代理和式 (8) 的函数值不相等。

有限差分核对了梯度，不是核对旧文档。\(n=5\)、\(c=2\)、链式 \(W\)、\(\gamma=0.8\)、种子 7，解析梯度 \(2S(G-F)+4\gamma\widetilde LG\) 与步长 \(10^{-6}\) 的中心差分最大绝对差为 \(2.45\times 10^{-9}\)。该解析梯度等于 E8 残差矩阵的 2 倍。

## 式 (10) 和 Algorithm 1 第 10 行

\(\widetilde L\) 是 \(n\times n\)。式 (13) 里的 \(S+\gamma\widetilde L\) 只有在 \(S\) 也是 \(n\times n\) 时才能相加。式 (10) 的对角长度是嵌入维数 \(c\)，加不进这个线性系统，也乘不进式 (9) 那个要求 \(S\) 为 \(n\times n\) 的迹。按行的

\[
S_{ii}=\frac{1}{2\max(\lVert h_i\rVert_2,\varepsilon)}
\]

同时满足式 (8) 的样本 \(\ell_{2,1}\)、式 (11) 和式 (13) 的维度。这一轮继续用它，不实现式 (10) 的嵌入维对角。

Algorithm 1 第 10 行用 \(\widetilde W\) 替换 \(\widetilde L\)，用 \(X\) 替换 \(F\)。论文里 \(X\in\mathbb{R}^{d\times n}\)，和 \(F\) 不同形。这一轮仍然不执行第 10 行。\(\widetilde W\) 和 \(\widetilde L\) 每次迭代按当前 \(G\) 重算，因为式 (11) 依赖 \(G\)。

## 实现的两个变体

`SSC_method/optimizer.py` 的 `variant` 决定 \(A=S+c\gamma\widetilde L\)：

| 变体 | \(c\) | 线性系统 | 默认 |
| --- | --- | --- | --- |
| E13 | \(1\) | 印出的式 (13) | 是。省略 `variant` 时就是它 |
| E8 | \(2\) | 上面导出的式 (8) 驻点 | 否 |

\(S\) 仍是按行的 \(n\times n\)。\(G_0=F\)。`zero_residual_floor` 默认仍是 `median_pairwise`，`"eps"` 保留。`SpectralShrunkClustering` 把同一个参数传下去；默认调用的 `info_["linear_update"]` 仍是 `equation_13`。

历史里四项分开记，不写成同一个量：

- `equation8_objective`：式 (8) 的原始范数，系数是调用者传入的 \(\gamma\)。E13 并不最小化它。
- `sqrt_smoothed_equation8_objective`：每个欧氏范数换成 \(\sqrt{\lVert v\rVert_2^2+\varepsilon^2}\)。求解器所用的 \(\varepsilon\) 很小时它会贴着式 (8)；这只是数值接近。
- `irls_quadratic_surrogate`：冻结的 \(S,\widetilde L\) 下，该变体真正最小化的二次函数。E13 用 \(\gamma\operatorname{Tr}(G^\top\widetilde L G)\)，E8 用 \(2\gamma\operatorname{Tr}(G^\top\widetilde L G)\)。
- `fixed_point_residual`：在返回的 \(G\) 上重算 \(S\) 和 \(\widetilde L\) 之后的 \(\lVert AG-SF\rVert_F\)。循环内的 `linear_residual` 只说明一次冻结系统被解过。

## 小规模凸核对

例子：\(n=6\)，\(c=2\)，\(F\) 来自 `numpy` 种子 1 的标准正态，\(\gamma=0.8\)。两个图都是对称的，两条有向边都存：

- 链：相邻点权重 1。
- 块：两个三角形团，团内权重 1，中间一条桥权重 \(0.15\)。

IRLS：\(\varepsilon=10^{-10}\)，`tol=10^{-12}`，`max_iter=1000`，`zero_residual_floor="median_pairwise"`，\(G_0=F\)。独立求解器用 CVXPY 1.9.3 / CLARABEL 0.11.1，设置 `tol_gap_abs=tol_gap_rel=tol_feas=10^{-10}`，`max_iter=500`。两个问题的状态都是 `optimal`。

| 图 | 求解 | 式 (8) 或对应目标 | 与参照解的最大绝对差 | 不动点残差 | 迭代 |
| --- | --- | --- | --- | --- | --- |
| 链 | CLARABEL，图系数 \(\gamma\) | \(4.021064576768\)（12 次） |  |  |  |
| 链 | E8 | \(4.021064576828\) | \(1.07\times 10^{-6}\) | \(1.12\times 10^{-6}\) | 103，步长收敛 |
| 链 | CLARABEL，图系数 \(\gamma/2\) | \(3.843869772520\)（10 次） |  |  |  |
| 链 | E13 放进 \(\gamma/2\) 的目标 | \(3.843869772479\) | \(4.08\times 10^{-6}\) | \(8.66\times 10^{-7}\) | 1000，步长未标收敛 |
| 链 | E13 放进印出的式 (8) | \(4.536864561036\) |  |  |  |
| 块 | CLARABEL，图系数 \(\gamma\) | \(3.652064947785\)（10 次） |  |  |  |
| 块 | E8 | \(3.652064947951\) | \(9.94\times 10^{-7}\) | \(3.03\times 10^{-6}\) | 1000，步长未标收敛 |
| 块 | CLARABEL，图系数 \(\gamma/2\) | \(3.573381366945\)（13 次） |  |  |  |
| 块 | E13 放进 \(\gamma/2\) 的目标 | \(3.573381366967\) | \(2.70\times 10^{-6}\) | \(1.41\times 10^{-6}\) | 1000，步长未标收敛 |
| 块 | E13 放进印出的式 (8) | \(3.655950751916\) |  |  |  |

E8 对上印出的式 (8)。E13 对上图项为 \(\gamma/2\) 的凸问题。链上式 (8) 的最优值比 E13 处的式 (8) 小约 \(0.516\)；块上小约 \(0.0039\)。块上的差距小，但大于求解容差，所以两套解仍然不是同一个问题。

同一点上的四个量，以链上的 E8 为例：式 (8) 为 \(4.021064576828\)；求解器 \(\varepsilon=10^{-10}\) 的平滑目标为 \(4.021064577355\)；\(\varepsilon=10^{-2}\) 的平滑目标为 \(4.101876705618\)；IRLS 二次代理为 \(2.010532438591\)；不动点残差为 \(1.12\times 10^{-6}\)。代理大约是式 (8) 的一半，因为展开点上每个范数的二次项只承担范数的一半。残差是矩阵残差，不是目标值。

冻结 \(S,\widetilde L\) 后，\(c=1\) 和 \(c=2\) 的二次函数都用 `scipy.optimize` 的 L-BFGS-B 从随机起点最小化，与 `spsolve` 的解一致。这只核对二次代理，不核对式 (8)。

步长收敛和不动点残差也不是一回事。块图、E13、`tol=10^{-8}`、`max_iter=80` 时，第 57 步就标成收敛，Frobenius 步长 \(2.18\times 10^{-8}\)，冻结线性残差 \(1.06\times 10^{-6}\)，但在最终 \(G\) 上重算权重后的不动点残差是 \(0.361\)。把 `tol` 收到 \(10^{-12}\) 并跑满 1000 步后，残差降到 \(1.41\times 10^{-6}\)，目标才和 CLARABEL 一致。步长旗标不能代替不动点残差。

`zero_residual_floor="eps"` 在 E13 上仍停在 \(F\) 附近。线性间距的 \(6\times 2\) 嵌入、链式 \(W\)、\(\gamma=1\)、\(\varepsilon=10^{-8}\) 时，E13 两步后 \(\lVert G-F\rVert_F=1.41\times 10^{-8}\)。E8 接受同一个选项，第一步也是 \(2.83\times 10^{-8}\)；随后最小行残差逐次变大，30 步时 \(\lVert G-F\rVert_F=0.390\)，式 (8) 从 \(2.828\) 降到 \(2.277\)，不动点残差 \(0.987\)，没有收敛。默认仍是 `median_pairwise`。凸核对用的是这个默认值。

## 这一轮没有说明的事

ORL 的 \(53.9\) 对 \(76.0\)、YaleB 的 \(19.7\) 对 \(49.8\) 都没有用 E8 或 E13 重跑。小例子上的目标差不能外推成聚类精度。式 (8)、平滑目标、IRLS 代理和不动点残差继续分开记录。
