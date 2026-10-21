# Round 2 根因分析

日期：2026-10-21。只根据 `runs/round2/` 与已核验的 Round 1 历史 run 下结论。标签仅用 **CONFIRMED / SUPPORTED / PLAUSIBLE / UNRESOLVED**。没有对照实验的条目标 UNRESOLVED，不升格。论文表格数字不是我们的结果。

Git：HEAD `f9c381487d8a4915f35c2eadb638b5f28d830b11`，工作树脏。共享图已统一：同一配置下 SC \(F\) = SSC \(F\)（`results/round2/d2_shared_f.json`，max‖Δ‖=0）。

## 1. ORL 谱聚类相对论文 72.7 的差距，最早出现在哪一阶段？

**CONFIRMED：出现在对式 (4) 嵌入 \(F\) 做 K-means 之时，早于 IRLS。**

证据：

- att92 上 K-means(\(F\))/SC 为 56.2±4.2（\(n=50\)，`…D01_ATT92_SC__4fe80e2e`），E8 cluster \(G\) 为 57.3±3.8（`…D08_E8_ATT92__d3809fd0`），E13 为 56.7±4.1。收缩 < 2 pp。
- 同一保存的 \(F\) 上 random K-means 仍是 56.2（D10）。
- 论文 SC 是 72.7，不是 76.0。76.0 是论文 SSC。我们在 SC 阶段已经差 16.5 pp，SSC 不能从这里“补上”到 76.0。

因此“IRLS / 式 (8) 实现错了所以 SC 也差”不成立：SC 根本不跑 IRLS。

## 2. 统一 \(F\) 相对 Round 1 改了什么？

**CONFIRMED：Olivetti 上几乎没变，不是 72.7 差距的原因。**

历史 v1 SC ORL（核验，不是转述）：`20261020_015207__TRACKA__SC__ORL__a86c9d70` 与 `20261020_015621__TRACKB__SC__ORL__263aa38a`，`acc_mean=0.54215`，**54.2±3.1**（\(n=50\)），backend `baselines.spectral`（sklearn `NearestNeighbors` 图）。Olivetti 64→32。

Round 2 同一 Olivetti、同一 50 个种子协议、共享 `knn_affinity`：53.9±3.0（`…D01_OLIVETTI_SC__9118018b`）。差 **0.3 pp**，落在标准差内。

JAFFE SC 68.5±11.2 对 Round 1 67.7±11.3；YaleB 邓蔡 SC 20.1±1.2 与 Round 1 相同。USPS 现走共享路径（无 \(n>1500\) 切换），SC \(n=3\) 为 63.8±1.7。

D2：Olivetti 与 att92 上 SC \(F\) 与 SSC \(F\) 逐元素相等。用两套 \(F\) 评价收缩在本轮是无效对照，我们没有这样做。

## 3. att92 vs Olivetti

**SUPPORTED：original-source att92 提高约 2.3 pp，远远不够。**

同一 SC 配置，\(n=50\)：Olivetti 53.9±3.0 vs att92 56.2±4.2。图统计不同（1329 边 / 2 分量 / \(\delta^2=7.09\) vs 1273 边 / 3 分量 / \(\delta^2=9.34\)）。Olivetti **不是** original-source。

相对论文 SC 72.7，att92 仍差 16.5 pp。nearest（\(n=5\)，57.7±4.5）与 bicubic（\(n=5\)，54.8±5.0）未升 50 次；与 att92 前 5 种子 54.6 重叠，插值效应 **UNRESOLVED**（样本量不够）。

## 4. 图 A、带宽、对称化、拉普拉斯

**SUPPORTED：默认并集 + 中位有向带宽下，另两种全局带宽几乎不改 ACC 或边集。**

att92 上 \(n=5\)：均值带宽 54.6±4.1（\(\delta^2=9.17\)），无向边中位数 55.6±3.8（\(\delta^2=10.50\)），边数都是 1273、3 个分量。对照默认前 5 种子 54.6。

**SUPPORTED：mutual 对称化更差（C）。** 49.6±3.8，727 边，46 个连通分量（`…D04_MUTUAL_SC__64f5f71e`）。未跑 50 次。

**CONFIRMED：嵌入用的是式 (4) 对称归一化拉普拉斯**，特征根已记录。att92 式 (4) 与组合拉普拉斯都出现 3 个近零根，与 3 个连通分量一致。

**PLAUSIBLE 但被 D10 限制：3 个连通分量对 40 类是粗糙的图。** 图不连通只能保证 3 个平凡方向，不能单独解释 72.7 的缺口——同一 \(F\) 上 k-means++ 达到 78.3，说明 \(F\) 并非没有类结构。

## 5. 行归一化

**SUPPORTED：ACC 明显上升，且必须保持 C。**

att92 SC + 行归一化：67.7±3.1（\(n=5\)），NMI 87.1±0.8。相对默认前 5 种子约 +11 pp。按协议 **未升 50 次**。即使升到 50 次也不能称作论文方法。相对论文 72.7 仍差约 5 pp，且 \(n=5\)。

## 6. \(W\) 是否建在 \(F\) 上

**CONFIRMED：是。** att92 E8：`w_built_on=F`，与 \(X\) 图 Jaccard 0.525，边数 1217 vs 1273，`identical_to_x_graph=false`。权重在 IRLS 前冻结。

## 7. E8 vs E13

**SUPPORTED：E8 目标更低、\(\lVert G-F\rVert\) 更大，聚类几乎一样，都远低于 76.0。**

att92 \(\gamma=1\) \(n=50\)：E8 57.3±3.8，式 (8)=14.583，\(\lVert G-F\rVert_F=0.727\)；E13 56.7±4.1，式 (8)=16.969，\(\lVert G-F\rVert_F=0.443\)。差 0.6 pp。忠实表用 E8。没有改线性系统去追 ACC。

JAFFE：E8 68.4 vs E13 68.6，与 SC 68.5 不可分。YaleB 邓蔡 E8 19.5 vs SC 20.1。USPS E8 60.7 vs SC 63.8（\(n=3\)）。收缩在已测集上都不构成论文声称的大幅增益。

## 8. IRLS 收敛是不是 ACC 缺口？

**CONFIRMED：ORL att92 E8 在 300 步未收敛。SUPPORTED：加到收敛不提高 ACC。**

max_iter=1000、\(n=5\)：825 步收敛，目标 14.58272 vs 300 步的 14.58275，ACC 55.9±4.5 vs 短名单 57.3。固定点残差在 300 步为 0.013。未把 1000 步当作忠实设定，也未升 50 次。

## 9. K-means 初始化 vs 最佳目标

**CONFIRMED：random 的 mean±std 远低于 k-means++；最佳 inertia 不等于最佳 ACC，也到不了 72.7。**

att92 保存的 \(F\)（SC 与 E8 相同）：

- 50 random：56.2±4.2；最低 inertia seed=21，ACC **62.25**（不是按 ACC 选的）
- 50 k-means++（B）：78.3±1.3；最低 inertia seed=13，ACC 79.0

Olivetti 保存的 \(F\)：random 53.9；++ 62.7±1.4（与 Round 1 Olivetti ++ 62.1 同量级）。

JAFFE 保存的 \(F\)：random 68.5±11.2；++ 95.3，50 个种子标准差为 0。random 里最低 inertia 的 trial ACC 也是 95.3（seed 23）。++ 的 95.3 **不是** 81.2 的忠实复现。

论文写了随机初始化并报告平均±标准差。把默认改成 k-means++ 是 **B_AMBIGUITY**。att92 上 ++ 的 78.3 超过论文 SC 72.7 与 SSC 76.0，说明缺口在 **随机 K-means 未能找到 \(F\) 上已有的划分**，而不是 \(F\) 信息量为零。这不能授权把 ++ 写进忠实主表。

## 10. 收缩有没有在任何忠实设定上帮上忙？

**CONFIRMED：没有达到论文量级。**

| 数据集 | K-means(\(F\))/SC | E8 \(G\) |
| --- | --- | --- |
| ORL att92 \(n=50\) | 56.2 | 57.3 |
| JAFFE \(n=50\) | 68.5 | 68.4 |
| YaleB dengcai \(n=10\) | 20.1 | 19.5 |
| YaleB cropped \(n=10\) | 18.1 | 17.4 |
| USPS \(n=3\) | 63.8 | 60.7 |

## 11. YaleB cropped vs 邓蔡；USPS

**SUPPORTED：cropped2414 不比邓蔡更好**（SC 18.1 vs 20.1；E8 17.4 vs 19.5，\(n=10\)）。两者都远低于 34.8 / 49.8。不声称与论文逐样本同一。

**PLAUSIBLE：USPS 上共享路径的 SC 已接近论文 64.3，SSC 没有。** \(n=3\) 的 SC 63.8±1.7 vs 64.3；E8 60.7±4.0 vs 75.5。样本太少，不能当协议完成。未 TIMEOUT。

## 12. 扩展 mutual-kNN（JAFFE \(n=50\)）

**CONFIRMED：同一 \(F\)、同一 E8、\(n=50\)，mutual 不提升 ACC。** 68.4±11.2 vs union E8 68.4±11.1。边 410 vs 655，分量 20 vs 9。已跑，不是跳过。

## 13. 仍未解决的（UNRESOLVED）

- 作者未发布的预处理、\(\delta\)、K-means 实现是否等于我们的 att92 + 中位带宽 + sklearn Lloyd random。
- 论文 72.7 是否来自行归一化、k-means++、最佳目标、或未写出的图规则。本轮这些要么是 C，要么是 B；B 的 ++ 在 att92 上甚至超过 72.7，**不能**反过来说“所以论文用了 ++”。
- nearest vs bicubic 插值（仅 \(n=5\)）。
- \(\gamma\) 网格的 \(n=50\) 扫描（本轮忠实短名单固定 \(\gamma=1\)）。
- USPS / YaleB 的 50 次协议。
- 论文 SSC 相对 SC 的 +3.3 pp（76.0 vs 72.7）在我们协议里复现为约 +1.1 pp（57.3 vs 56.2）。差异来源未分离。

## 14. 结论（给交接）

1. **最早核实阶段：** 式 (4) 的 \(F\) 上的 random K-means。不是 IRLS，不是 E8/E13 系数。
2. **统一 \(F\)：** 相对 Round 1 Olivetti SC 54.2，本轮 53.9；不是主因。
3. **att92 vs Olivetti：** +2.3 pp，剩余 vs 72.7 为 **−16.5 pp**。
4. **E8 vs E13：** 57.3 vs 56.7；忠实表 E8 相对 76.0 为 **−18.7 pp**。
5. **k-means++：** att92 \(F\) 上 78.3±1.3（B）。random 最佳 inertia 62.3。都不是按 ACC 选种。
6. **剩余：** 忠实 random 协议下，ORL att92 SC vs 72.7 = **−16.5 pp**；E8 vs 76.0 = **−18.7 pp**。
