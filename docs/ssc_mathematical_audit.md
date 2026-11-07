# SSC 数学审计

来源：Chang, Nie, Ma, Yang, Zhou，*A Convex Formulation for Spectral Shrunk Clustering*，AAAI 2015，`9736-45063-1-PB.pdf`，`pdftotext -layout` 文本。审计范围是式 (3)–(13) 和 Algorithm 1，并核对收敛证明里式 (14)–(18) 的系数。实现决定是纠错和复现假设，不是新方法。

记号：样本按行存放，数组形状是 `(n, d)`。Algorithm 1 把数据写成 \(X\in\mathbb{R}^{d\times n}\)。式 (13) 的右端是 \(F\)，求解过程不乘 \(X\)。

## 式 (3)–(4)：谱嵌入

式 (3) 是 \(\min_F \operatorname{Tr}(F^\top L F)\)，约束 \(F=Y(Y^\top Y)^{-1/2}\)。式 (4) 的对称归一化拉普拉斯是

\[
L_n = I - D^{-1/2} A D^{-1/2}.
\]

\(A_{ij}=\exp(-\lVert x_i-x_j\rVert^2/\delta^2)\) 当二者为 \(k\) 近邻，否则为 0。\(D_{ii}=\sum_j A_{ij}\)。论文把所有谱方法的邻域大小设为 \(k=5\)。

实现取 \(L_n\) 的 **最小** \(c\) 个特征值对应的特征向量，按特征值升序排列，作为 \(F\in\mathbb{R}^{n\times c}\)。这不是 PCA。邻居数和带宽都显式传入，不用 scikit-learn 的默认邻居数或 RBF 带宽。

孤立点（度为 0）的 \(D^{-1/2}\) 对角元取 0，于是 \(L_n\) 在该行是单位向量。论文没有写这个边界。

## 式 (5)–(8)：收缩目标

谱嵌入 \(\{f_i\}\) 上再造 \(k\) 近邻图，\(W_{ij}=\exp(-\lVert f_i-f_j\rVert^2/\delta^2)\)。式 (5)–(7) 先写平方损失，式 (8) 改成行 \(\ell_{2,1}\)：

\[
\min_G \lVert G-F\rVert_{2,1} + \gamma\sum_{ij} W_{ij}\lVert g_i-g_j\rVert_2,
\quad G,F\in\mathbb{R}^{n\times c}.
\]

\(\lVert H\rVert_{2,1}=\sum_i\lVert h_i\rVert_2\)，\(h_i\) 是 \(H=G-F\) 的第 \(i\) 行。\(\sum_{ij}\) 按有序对求和；对称 \(W\) 的两条有向边都计入。

## 式 (9)–(10)：\(S\) 必须是 \(n\times n\)，并且按行

式 (9) 的 \(\operatorname{Tr}((G-F)^\top S(G-F))\) 要求 \(S\) 为 \(n\times n\)。式 (10) 把 \(S\) 写成

\[
S=\operatorname{diag}\Big(\frac{1}{2\lVert h_1\rVert_2},\ldots,\frac{1}{2\lVert h_d\rVert_2}\Big),
\]

并说 \(H=[h_1,\ldots,h_d]\)，\(d\) 是谱嵌入维数。若 \(h_j\) 是列向量，\(S\) 是 \(c\times c\)（文中混用了原始维数 \(d\) 和嵌入维数）。这与式 (9) 的乘法顺序矛盾，也与 Nie 等人 2010 年按样本（行）做 \(\ell_{2,1}\) 抗异常值的写法矛盾。

**纠正：** \(S\) 为 \(n\times n\) 对角阵，

\[
S_{ii}=\frac{1}{2\max(\lVert h_i\rVert_2,\varepsilon)},
\]

\(h_i\) 是 \(G-F\) 的第 \(i\) 行。\(\varepsilon\) 只防止除零。这不是新的正则项。

## 式 (11)–(13) 与 Algorithm 1 第 10 行

式 (11)：\(\widetilde W_{ij}=W_{ij}/(2\lVert g_i-g_j\rVert_2)\)，\(\widetilde L=\widetilde D-\widetilde W\)，\(\widetilde D_{ii}=\sum_j\widetilde W_{ij}\)。这是组合拉普拉斯，不是式 (4) 的归一化拉普拉斯。

式 (12) 写成

\[
\min_G \operatorname{Tr}((G-F)^\top S(G-F))+\gamma\operatorname{Tr}(G^\top\widetilde L G).
\]

对 \(G\) 求导并令其为 0，得到式 (13)：

\[
G=(S+\gamma\widetilde L)^{-1}SF.
\]

Algorithm 1 第 10 行写成 \(G_{t+1}=(S_t+\gamma\widetilde W)^{-1}S_t X\)。这里把 \(\widetilde L\) 换成了 \(\widetilde W\)，把 \(F\) 换成了 \(X\)。第 4 行还把依赖 \(G\) 的 \(\widetilde W\) 放在循环外。

**实现式 (13)，不用第 10 行。** 每次迭代都用当前 \(G\) 重算 \(\widetilde W\) 和 \(\widetilde L\)。线性系统用 `scipy.sparse.linalg.spsolve` 求解，不形成显式逆。\(S_{ii}>0\) 且 \(\gamma\ge 0\) 时，\(S+\gamma\widetilde L\) 对称正定；调用前仍做一次 \((A+A^\top)/2\)，只为去掉浮点不对称。

\(G_0=F\)。论文只写 \(G_0\in\mathbb{R}^{n\times c}\)，没有给初值。这是假设。此时 \(H_0=0\)，式 (10) 除以零。若用 \(\varepsilon\) 作为第一次的分母下界，\(S\sim 1/\varepsilon\)，第一步的位移是 \(O(\varepsilon)\)，迭代停在 \(F\) 附近，而 \(F\) 一般不是式 (8) 的驻点。因此**只有第一次**全零残差使用另一个有限尺度：当前 \(G\) 各行两两距离的正值中位数。之后各次迭代，以及单独为零的行，仍用 \(\varepsilon\)。若每次靠近 \(F\) 都重新使用这个大尺度，迭代会周期性地被弹开，单测里能看到步长回到第一步。这个一次性尺度是数值纠正，默认记录在 `initial_zero_residual_floor`。传入 `zero_residual_floor="eps"` 可恢复“始终用 \(\varepsilon\)、因而停在 \(F\)”的行为。

## 式 (14)–(18) 的系数

引理 1：对非零 \(g,g^t\in\mathbb{R}^{c}\)，

\[
\lVert g\rVert_2-\frac{\lVert g\rVert_2^2}{2\lVert g^t\rVert_2}
\le
\lVert g^t\rVert_2-\frac{\lVert g^t\rVert_2^2}{2\lVert g^t\rVert_2}.
\]

式 (16) 与式 (17) 相加后，二次项抵消，得到式 (18) 的单调性。这一步代数在 \(\widetilde W_{ij}=W_{ij}/(2\lVert g_i^t-g_j^t\rVert_2)\) 的定义下是闭合的。它监控的是式 (8) 的标量目标，本身不经过迹。

迹和求和并不相等。手算例子：\(G=(0.2,0.8)^\top\)，\(W_{01}=W_{10}=1\)，距离 \(0.6\)。

| 量 | 值 |
| --- | --- |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.72\) |
| \(\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\) | \(1.2\) |
| \(\widetilde W_{01}=1/(2\cdot 0.6)\) | \(5/6\) |
| \(\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2\) | \(0.6\) |
| \(\operatorname{Tr}(G^\top\widetilde L G)\) | \(0.3\) |

因此在展开点上

\[
\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2
= 2\operatorname{Tr}(G^\top\widetilde L G)
= \tfrac12\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2.
\]

式 (15) 最小化 \(f(G)+\gamma\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2\)。对对称 \(W\)，\(\sum_{ij}\widetilde W_{ij}\lVert\cdot\rVert_2^2=2\operatorname{Tr}(G^\top\widetilde L G)\)，所以这个主化子的驻点是

\[
(S+2\gamma\widetilde L)G = SF.
\]

式 (12) 写成 \(\gamma\operatorname{Tr}(G^\top\widetilde L G)\)，其驻点才是式 (13) 的 \(\gamma\widetilde L\)。式 (13) 的图系数比式 (8) 的主化子少一个 2。

对式 (8) 直接求导可以得到同一个因子。\(W\) 对称时

\[
\frac{\partial}{\partial g_k}\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2
= 4(\widetilde L G)_k,
\qquad
\frac{\partial}{\partial g_k}\lVert h_k\rVert_2
= 2S_{kk}(g_k-f_k).
\]

令梯度为零即 \((S+2\gamma\widetilde L)G=SF\)。

**锁定实现仍求解式 (13)，系数是 \(\gamma\) 而不是 \(2\gamma\)。** 因此式 (13) 的不动点对应的是把式 (8) 的图项系数换成 \(\gamma/2\) 之后的凸问题，而不是印出来的式 (8)。单测在 \(n=6\)、\(c=2\)、链式 \(W\)、\(\gamma=0.8\)、随机种子 1 上，用 CVXPY 1.9.3 / CLARABEL 独立求解两个凸问题：式 (13) 的 \(G\) 与 \(\gamma/2\) 问题的解一致（目标约 \(3.844\)，最大绝对差约 \(2\times 10^{-5}\)）；同一 \(G\) 上印出来的式 (8) 目标约 \(4.537\)，而式 (8) 本身的最优值约 \(4.021\)。不把二者称为等价。

式 (12) 的二次函数（\(S\) 和 \(\widetilde L\) 冻结）另用 `numpy.linalg.solve` 和 `scipy.optimize`（L-BFGS-B）独立最小化，与稀疏求解一致。那是式 (12) 的核对，不是式 (8) 的核对。

## 监控哪一个目标

每次迭代记录：

- `equation8_objective`：式 (8) 的原始范数，不加 \(\varepsilon\)。
- `sqrt_smoothed_equation8_objective`：每个欧氏范数换成 \(\sqrt{\lVert v\rVert_2^2+\varepsilon^2}\)。这是平滑目标，和平方根平滑、以及分母里的 \(\max(\lVert v\rVert_2,\varepsilon)\)，是三个不同的函数。

历史里的线性残差是冻结的 \(S,\widetilde L\) 下 \(\lVert(S+\gamma\widetilde L)G-SF\rVert_F\)。返回值里的 `fixed_point_residual` 是在最终 \(G\) 上重算 \(S\) 和 \(\widetilde L\) 之后的残差。近邻距离落到 \(\varepsilon\) 上时，后者可以明显大于前者，因为 \(\widetilde W\) 对距离很敏感。

论文没有给停止准则。实现用相对 Frobenius 步长 \(\lVert G_{t+1}-G_t\rVert_F\le \mathrm{tol}(1+\lVert G_t\rVert_F)\)，默认 \(\mathrm{tol}=10^{-6}\)，`max_iter=100`。非光滑重加权在步长约 \(10^{-8}\) 处会有数值抖动，把 `tol` 收到 \(10^{-12}\) 不一定能标成收敛，即使不动点残差已经很小。

## 带宽、对称化和 K-means

\(\delta\) 在文中未指定。复现假设：\(\delta^2\) 等于该图上有向 \(k\) 近邻平方距离中正值的中位数；没有正距离时用 \(1\)。原始特征上的图和嵌入上的图各自算自己的中位数。

“\(k\) 近邻”没有说明无向化。实现采用并集：\(i\) 列出 \(j\) 或 \(j\) 列出 \(i\) 则连边，权重为该距离的高斯值，对角线为 0。平局时较小的下标优先。\(n\le 1500\) 用稳定全排序；更大时用分块 `argpartition`，截断边界上的平局与全排序可能不同。

最终在 \(G\) 上做 K-means（`k-means++`，Lloyd，显式 `n_init` 和 `random_state`）。标签只作为输出，不写回 \(W\)、\(F\) 或 \(G\)。论文实验写 50 次重复，那是实验协议，方法默认 `n_init=10`，调用时可以改。

特征向量符号：每一列绝对值最大的元素为正。这只去掉符号自由度，不改变子空间；重数大于 1 时基的旋转仍不唯一。
