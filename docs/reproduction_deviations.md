# 复现差异

方法部分是相对 Chang 等人 AAAI 2015 原文的假设和纠正。实验数字只来自 `runs/`，标为 Our Reproduction，不是论文表格的拷贝。

| 项目 | 原文 | 本实现 | 性质 |
| --- | --- | --- | --- |
| 求解 | Algorithm 1 第 10 行 \((S_t+\gamma\widetilde W)^{-1}S_t X\) | 式 (13)：\((S+\gamma\widetilde L)^{-1}SF\)，稀疏求解，无显式逆 | 锁定纠正 |
| \(\widetilde W,\widetilde L\) | 算法第 4 行在循环外计算 | 每次迭代由当前 \(G\) 按式 (11) 重算 | 锁定纠正。式 (11) 依赖 \(G\) |
| \(S\) | 式 (10) 按嵌入维数的对角元 \(1/(2\lVert h_j\rVert_2)\) | \(n\times n\)，按行 \(S_{ii}=1/(2\max(\lVert h_i\rVert_2,\varepsilon))\) | 锁定纠正。式 (10) 与式 (9) 的维度以及行 \(\ell_{2,1}\) 不一致 |
| 式 (13) 的系数 | 印出的系数是 \(\gamma\widetilde L\)。式 (8) 的驻点是 \((S+2\gamma\widetilde L)G=SF\) | 求解印出的式 (13)。它对应把式 (8) 的图项写成 \((\gamma/2)\sum_{ij}W_{ij}\lVert g_i-g_j\rVert_2\) | 锁定。与式 (8) 不等价，见审计中的 CVXPY 对照 |
| 初值 | 未指定 | \(G_0=F\) | 假设 |
| 初值处的式 (10) | \(H=0\) 时未定义 | 仅第一次全零残差用行间距离中位数作分母尺度；其后用 \(\varepsilon\)（默认 \(10^{-8}\)） | 数值纠正。始终用 \(\varepsilon\) 会使迭代停在 \(F\)；每次回到 \(F\) 都用大尺度会循环 |
| 监控目标 | 证明讨论式 (8)；实验曲线对应哪一个式子，图中没有公式 | 同时记录式 (8) 原始目标和 \(\sqrt{\lVert v\rVert^2+\varepsilon^2}\) 平滑目标 | 平滑目标、分母 \(\varepsilon\) 和式 (8) 三者都不宣称相等 |
| 停止 | 未说明 | 相对 Frobenius 步长，默认 `tol=1e-6`，`max_iter=100` | 假设 |
| \(\delta\) | 未给出 | 每个图各自取正的 \(k\) 近邻平方距离的中位数作为 \(\delta^2\) | 假设 |
| \(k\) 近邻无向化 | 未说明 | 并集，权重取高斯值，对角线为 0。\(k=5\) | 假设。邻居数是原文实验设置 |
| 谱嵌入 | 最小化 \(\operatorname{Tr}(F^\top L_n F)\)，\(L_n\) 为式 (4) | \(L_n\) 的 \(c\) 个最小特征向量。符号按最大绝对值元素为正。孤立点 \(D^{-1/2}=0\) | 符号和孤立点是约定。不用 PCA |
| 数据形状 | Algorithm 1 写 \(X\in\mathbb{R}^{d\times n}\) | 数组行为样本，形状 `(n, d)` | 约定。式 (13) 不使用 \(X\) |
| K-means | 在 \(G\) 上聚类；实验文本同时出现 50 次和最优目标 | 标签只在 \(G\) 上计算，不参与学习。每个 trial 一个随机种子、`init="random"`、`n_init=1` | 50 次属于实验协议。实际完成次数见下表，没有补造 |
| \(\gamma\) 默认 | 在 \(\{10^{-6},10^{-3},1,10^{3},10^{6}\}\) 上选择，并称除 MSRA50 与 USPS 外 \(\gamma=1\) 通常较好 | API 默认 `gamma=1` | API 默认，不是“每个数据集的最优值” |

## 实验差异（来自实际 runs/）

- 数据集：JAFFE、USPS 已核对；ORL 是 Olivetti 64×64 再缩到 32×32；YaleB 是邓蔡 32×32 mat。AR、UMIST、BinAlpha、MSRA50 不可得。
- 基线：SPLS 为 `NOT_IMPLEMENTED`（6 个 SKIPPED 目录）。LDA-SC 为 `APPROXIMATE`，不进主公平表。
- 试验次数：ORL/JAFFE 上 K-means、SC、SSC、LLC 为 50；YaleB 为 10；USPS SSC 为 1，USPS K-means 为 10。不要把后两行读成 50 次复现。
- ORL SSC Track A：53.9±3.0（n=50，γ=1e-6）对论文 76.0±1.6。与本实现 SC 54.2±3.1 不可分。**没有复现论文声称的 ORL 大幅增益。**
- JAFFE SSC Track A：74.8±8.4（n=50，选中 γ=1e6）对论文 81.2±1.6。γ=1 时为 68.6±11.3。
- YaleB SSC：19.7±1.1（n=10）对论文 49.8±1.6。
- USPS SSC：62.1（n=1）对论文 75.5±1.9。
- 扩展 mutual-kNN：ORL 53.7±2.8 vs 54.0±2.8（n=50）；JAFFE 68.6 vs 68.7（n=50）；YaleB 19.7 vs 19.9（n=10）。混合/可忽略，不是赢。
- 一次失败：`20261020_015425__TRACKA__LDAKM__ORL__fb14ac44`（NameError），已用 `20261020_020157__TRACKA__LDAKM__ORL__fb14ac44` 重跑完成；FAILED 目录保留。
- IRLS：γ=1 时 ORL 与 YaleB 在 max_iter=300 未达到 tol=1e-6。

完整表：`results/tables/` 与 `docs/critical_analysis.md`。
