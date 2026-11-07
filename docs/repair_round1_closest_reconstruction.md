# 第一轮修复：按保真度排序的最近重建

日期：2026-10-20。硬件：8 CPU、16 GB。数字全部来自真实 run，试验次数是实际完成的 \(n\)。论文 ACC/NMI 只作对照，不是我们的结果。**C 类一律不是论文方法。** Track B 固定 \(\gamma=1\)，没有用标签选 \(\gamma\)。

排序规则：**先保真度，再看与论文的数值接近程度。**

| 类别 | 含义 | 可否称作论文方法 |
| --- | --- | --- |
| A `A_PAPER_FAITHFUL` | 印出的式 (8) 驻点，\(A=S+2\gamma\widetilde L\)，\(k=5\)，并集 kNN，中位带宽，原始特征向量，\(G_0=F\)，K-means random | 在已证明的排版纠错下，是忠实变体 |
| B `B_AMBIGUITY` | 印出的式 (13)（现默认）以及论文未写的带宽、K-means++ 初始化等 | 重建，不是已证明的式 (8) |
| C `C_DIAGNOSTIC` | K-means(\(F\))、行归一化特征向量、mutual kNN 扩展 | **否** |

没有重跑 ORL 的 31 次单因子矩阵。Phase 1 历史 run 未删除。YaleB 第一次 ARPACK 诊断失败的 6 条 `FAILED` 记录保留在 `runs/repair_round1/` 和 registry 中；聚类本身后来已重跑完成。

## 总表（论文 vs 旧 v1 vs 修复后）

显式列名见 `results/repair_round1/reproduction_comparison.csv` 与 `.tex`。下面按数据集写。

### JAFFE（verified Zenodo 213×676，\(n=50\)）

身份：`verified_zenodo_213_not_paper_unpublished_copy`。不是论文未公开预处理的逐样本同一。

论文（reported）：ACC **81.2±1.6**，NMI **84.3±1.6**。旧 v1 \(\gamma=1\)：68.6±11.3（n=50，`20261020_015452__TRACKA__SSC__JAFFE__536c9eb1`）。

| 保真度 | 设定 | ACC | NMI | \(n\) | run_id |
| --- | --- | --- | --- | --- | --- |
| A 忠实 | E8，cluster \(G\) | 68.4±11.1 | 83.0±5.7 | 50 | `20261020_033024__REPAIR1__JAFFE__D12_KMEANS_G_E8__ee463086` |
| B 默认重建 | E13，cluster \(G\) | 68.6±11.3 | 83.0±5.8 | 50 | `20261020_033023__REPAIR1__JAFFE__D12_KMEANS_G_E13__c943774b` |
| B 歧义 | E13 + k-means++ | 95.3±0.0 | 94.1±0.0 | 50 | `20261020_033025__REPAIR1__JAFFE__D09_KM_PLUSPLUS__585e102e` |
| C 诊断 | K-means(\(F\)) | 68.5±11.2 | 83.0±5.7 | 50 | `20261020_033021__REPAIR1__JAFFE__D12_KMEANS_F__e8036aab` |
| C 诊断 | 行归一化特征向量 | 85.0±9.4 | 91.8±4.1 | 50 | `20261020_033027__REPAIR1__JAFFE__D05_ROW_NORM__b613c07e` |
| C 扩展 | mutual kNN RSSC | 68.7±11.3 | 83.0±5.9 | 50 | `20261020_034223__REPAIR1__JAFFE__EXT_MUTUAL_KNN__c13071f7` |

- **忠实 A**：E8 68.4，距论文 −12.8 pp。IRLS 未在 300 步收敛。\(\lVert G-F\rVert_F=0.093\)，图 9 个连通分量、655 条无向边。
- **最近的 A/B 重建**：E13 68.6（B）。k-means++ 的 95.3 在数值上超过论文，但是 B，**不是**忠实方法；50 个种子 ACC 标准差为 0，只说明该嵌入上 k-means++ 几乎确定性，不能用来宣称复现了 81.2。
- **最近的 C（不是论文方法）**：行归一化 85.0。ORL 上约 +6 pp 的提升在 JAFFE 上变成 +16.4 pp，因此判定 **row-norm 转移了**。仍标 C。
- **收缩有没有帮助**：没有。K-means(\(F\)) 68.5 vs E13 68.6。

### ORL（Olivetti 64→32，未重跑 31 次矩阵；短名单 \(n=50\)）

身份：`approximate_olivetti_64_to_32_not_att92_native`。

论文：ACC **76.0±1.6**，NMI **88.6±1.5**。旧 v1：53.9±3.0（n=50）。\(\gamma=1\) E13：53.7±2.8。

| 保真度 | 设定 | ACC | NMI | \(n\) | run_id |
| --- | --- | --- | --- | --- | --- |
| A 忠实 | E8 | 53.3±3.2 | 76.2±1.8 | 50 | `20261020_032508__REPAIR1__ORL__D12_KMEANS_G_E8__d484f3c9` |
| B 默认 | E13 | 53.7±2.8 | 76.7±1.5 | 50 | `20261020_032506__REPAIR1__ORL__D12_KMEANS_G_E13__3cdaa69b` |
| B 最近 A/B | E13 + k-means++ | 62.1±1.6 | 80.3±0.7 | 50 | `20261020_032509__REPAIR1__ORL__D09_KM_PLUSPLUS__2fa139a6` |
| C 诊断 | K-means(\(F\)) | 53.9±3.0 | 76.5±1.7 | 50 | `20261020_032504__REPAIR1__ORL__D12_KMEANS_F__3c9cd874` |
| C 诊断 | 行归一化 | 60.2±2.9 | 80.1±1.2 | 50 | `20261020_032512__REPAIR1__ORL__D05_ROW_NORM__b7fe4814` |
| C 扩展 | mutual kNN | 54.0±2.8 | 76.6±1.5 | 50 | `20261020_034225__REPAIR1__ORL__EXT_MUTUAL_KNN__91b78dec` |

- 收缩没有帮助（F 53.9 vs E13 53.7）。E8 目标更低，聚类略差。没有任何 A/B 设定接近 76%。
- 最近 A/B 是 k-means++ 62.1（n=50，不是 n=5 的 62.5）。仍差约 14 pp。

### YaleB（邓蔡 32×32，\(n=10\)，不是 50）

身份：`approximate_dengcai32_not_claimed_sample_identity_with_paper`。**不声称与论文或邓蔡矩阵之外的版本逐样本同一。**

论文：ACC **49.8±1.6**，NMI **46.8±1.3**。旧 v1 \(\gamma=1\)：19.7±1.1（n=10）。

| 保真度 | 设定 | ACC | NMI | \(n\) | run_id |
| --- | --- | --- | --- | --- | --- |
| A 忠实 | E8 | 19.5±1.5 | 29.3±1.2 | 10 | `20261020_033639__REPAIR1__YALEB__D12_KMEANS_G_E8__3ab7c3f0` |
| B 默认 | E13 | 19.7±1.1 | 29.5±1.0 | 10 | `20261020_033606__REPAIR1__YALEB__D12_KMEANS_G_E13__537ad7be` |
| B 最近 A/B | E13 + k-means++ | 25.2±0.6 | 30.9±0.8 | 10 | `20261020_033710__REPAIR1__YALEB__D09_KM_PLUSPLUS__72eaaecc` |
| C 诊断 | K-means(\(F\)) | 20.1±1.2 | 29.9±0.9 | 10 | `20261020_033532__REPAIR1__YALEB__D12_KMEANS_F__20297104` |
| C 诊断 | 行归一化 | 26.7±1.8 | 37.4±0.7 | 10 | `20261020_033741__REPAIR1__YALEB__D05_ROW_NORM__fe5fbdd4` |
| C 扩展 | mutual kNN | 20.0±1.3 | 29.8±1.2 | 10 | `20261020_034227__REPAIR1__YALEB__EXT_MUTUAL_KNN__4869bdff` |

- 收缩没有帮助（F 20.1 vs E13 19.7）。IRLS 全部 300 步未收敛。图 13 个连通分量、8060 条边。
- k-means++ 转移到 YaleB（+5.5 pp）。row-norm 因 JAFFE 出现 ≥5 pp 提升而加跑，YaleB 上 +7.0 pp，仍是 C，且远低于 49.8。
- cropped2414 双线性 E13：18.0±0.7（n=10），NMI 26.4±0.7，`20261020_033811__REPAIR1__YALEB__D01_CROPPED2414_E13__cbd4d1ff`。身份：`obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai`。没有 ACC 提升，**不声称与邓蔡像素同一**。

### USPS（LIBSVM 9298，仅 pilot）

身份：`verified_libsvm_9298`。不是 50 次复现。没有子采样冒充 9298。

论文：ACC **75.5±1.9**，NMI **79.8±1.6**。旧 v1：62.1（n=1）。

E13 \(\gamma=1\)，3 个 K-means 种子，稀疏 IRLS：ACC **63.8±1.7**，NMI **77.5±4.0**（n=3），已收敛，171 步，\(\lVert G-F\rVert_F=0.038\)，1 个连通分量。run `20261020_033852__REPAIR1__USPS__D12_KMEANS_G_E13__5c5f8321`。墙钟约 205 s，未 TIMEOUT。没有跑 E8 / F / ++ / row-norm / RSSC。距论文约 −12 pp，且 \(n=3\) 不能当论文协议。

## 收缩有没有在任何数据集上帮助

没有。K-means(\(F\)) 与 E13 cluster \(G\) 之差：

- ORL：53.9 vs 53.7
- JAFFE：68.5 vs 68.6
- YaleB：20.1 vs 19.7

E8 往往 \(\lVert G-F\rVert\) 更大、式 (8) 更低，聚类不更好。

## k-means++ 与行归一化是否转移

- **k-means++（B）转移了**：ORL 62.1（+8.4 pp）、JAFFE 95.3（+26.7 pp，50 种子方差为 0）、YaleB 25.2（+5.5 pp）。论文未指定初始化；历史协议是 random。JAFFE 的 95.3 **不是**忠实复现。
- **行归一化（C）转移了**：ORL 60.2、JAFFE 85.0（+16.4 pp，因此 YaleB 也跑了）、YaleB 26.7。**禁止称作论文方法。**

## 扩展：mutual-kNN vs 原 SSC

同一数据版本、同一预处理、同一嵌入（原始特征向量、\(k=5\)、F 上中位带宽再 mutual 过滤）、同一 \(\gamma=1\)、同一种子。RSSC 为 C。

| 数据集 | union SSC ACC | mutual RSSC ACC | \(\lVert G-F\rVert\) SSC / RSSC | 连通分量 SSC / RSSC | 边数 SSC / RSSC | IRLS s SSC / RSSC | 收敛 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JAFFE n=50 | 68.6±11.3 | 68.7±11.3 | 0.050 / 0.033 | 9 / 20 | 655 / 410 | 0.20 / 0.40 | 是 / 是（298 步） |
| ORL n=50 | 53.7±2.8 | 54.0±2.8 | 0.650 / 0.473 | 13 / 42 | 1242 / 758 | 0.63 / 0.54 | 否 / 否 |
| YaleB n=10 | 19.7±1.1 | 20.0±1.3 | 0.292 / 0.182 | 13 / 176 | 8060 / 4010 | 7.19 / 2.66 | 否 / 否 |

负结果成立：mutual 边更少、分量更多，ACC 差 < 1 pp。Phase 1 EX1 是 53.7 vs 54.0、68.6 vs 68.7、19.7 vs 19.9；repair1 配对与之一致。USPS 未跑扩展。

## 与论文仍差多少

用 **忠实 A（E8）** 对论文：JAFFE −12.8 pp，ORL −22.7 pp，YaleB −30.3 pp（n=10）。USPS 只有 B 的 E13 n=3：−11.7 pp。

用 **最近 A/B**（仍不是把 C 算进去）：JAFFE E13 68.6（−12.6）、ORL k-means++ 62.1（−13.9）、YaleB k-means++ 25.2（−24.6）、USPS E13 63.8（−11.7，n=3）。

没有任何忠实或 A/B 设定填上 ORL 的 76%、YaleB 的 49.8%。JAFFE 的 95.3 / 85.0 来自 B/C，不能写成论文 SSC。
