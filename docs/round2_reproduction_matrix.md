# Round 2 复现矩阵（D1–D12）

日期：2026-10-21。工作区：`v1/`。硬件目标：8 CPU / 16 GB。所有 ACC/NMI 来自 `runs/round2/` 的真实 run，单位为百分数。论文数字只作对照，**不是我们的结果**。未覆盖 `runs/` 历史目录或 `runs/repair_round1/`。未 git commit。

Git：HEAD `f9c381487d8a4915f35c2eadb638b5f28d830b11`（`v1`）。工作树 **有未提交改动**；本轮数字来自该脏树。登记表：`results/round2/experiment_registry.csv`。

保真标签：`A_PAPER_FAITHFUL` / `B_AMBIGUITY` / `C_DIAGNOSTIC`。忠实主表用 **E8**（式 (8) 驻点 \(A=S+2\gamma\widetilde L\)）。E13（\(A=S+\gamma\widetilde L\)）单列。K-means 默认 `random`、`n_init=1`、协议层 50 个种子；**不用 ACC 选种子**。报全部 trial 的 mean±std，另记最佳 inertia。无效 / C 类变体不跑 50 次。

共享图：同一 `SpectralGraphConfig` 下 `baselines.spectral_clustering` 的 \(F\) 与 `SSC_method.spectral_embedding` 的 \(F\) 一致（符号：最大幅值分量为正）。`prepare_spectral` 不再在 \(n>1500\) 切换后端。

## 身份（本轮用到的版本）

| 数据集 | version | 身份 | 可否称 original-source |
| --- | --- | --- | --- |
| ORL | `olivetti` | `approximate_olivetti_64_to_32_not_att92_native` | **否** |
| ORL | `att92` | `original_source_att92_92x112_bilinear_32x32` | 是（插值未写，非 PAPER_PROTOCOL_MATCHED） |
| ORL | `att92_nearest` / `att92_bicubic` | 同 zip，插值为 B | 源是 AT&T；插值是 B |
| JAFFE | `zenodo` | `verified_zenodo_213_not_paper_unpublished_copy` | 已核实 zip，不是论文未公开预处理 |
| YaleB | `dengcai32` | `approximate_dengcai32_not_claimed_sample_identity_with_paper` | 否 |
| YaleB | `cropped2414` | `obtained_cropped2414_bilinear_not_claimed_sample_identity_with_dengcai` | 官方裁剪 zip；不声称与邓蔡逐像素同一 |
| USPS | `libsvm` | `verified_libsvm_9298` | 已核实；pilot \(n=3\)，不是 50 次协议 |

## D1 数据源（同一 SC 配置）

配置：式 (4)，\(k=5\)，并集 kNN，有向正 kNN 平方距离中位数作 \(\delta^2\)，原始特征向量，K-means random。Olivetti **未**标 original-source。

历史 v1 SC ORL（核验 run 记录，不是口算）：ACC **54.2±3.1**（\(n=50\)），NMI **76.5±1.6**，backend `baselines.spectral`，Olivetti 64→32。Track A `20261020_015207__TRACKA__SC__ORL__a86c9d70` 与 Track B `20261020_015621__TRACKB__SC__ORL__263aa38a` 的 `acc_mean` 均为 `0.54215`。

| 因子 | version | 保真 | \(n\) | ACC | NMI | 边 / 连通分量 | \(\delta^2\) | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D01_OLIVETTI_SC | olivetti | A | 50 | 53.9±3.0 | 76.5±1.7 | 1329 / 2 | 7.093 | `20261021_161536__ROUND2__ORL__D01_OLIVETTI_SC__9118018b` |
| D01_ATT92_SC | att92 | A | 50 | 56.2±4.2 | 80.5±2.3 | 1273 / 3 | 9.337 | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` |
| D01_ATT92_NEAREST_SC | att92_nearest | B | 5 | 57.7±4.5 | 81.0±3.0 | 1286 / 2 | — | `20261021_161538__ROUND2__ORL__D01_ATT92_NEAREST_SC__e6bb4f6e` |
| D01_ATT92_BICUBIC_SC | att92_bicubic | B | 5 | 54.8±5.0 | 79.8±3.1 | 1278 / 3 | — | `20261021_161539__ROUND2__ORL__D01_ATT92_BICUBIC_SC__5d93088d` |

论文 SC ORL：72.7±2.3。论文 SSC ORL：76.0±1.6。统一 \(F\) 后 Olivetti SC 相对历史 54.2 为 **−0.3 pp**。att92 相对 Olivetti **+2.3 pp**，相对论文 SC **−16.5 pp**。nearest/bicubic 未升到 50 次。

## D2 图 A / 共享 \(F\) / 特征根

对照文件：`results/round2/d2_shared_f.json`。同一 `SpectralGraphConfig`（\(k=5\)，union，中位有向带宽，式 (4)）：

| version | SC \(F\) = SSC \(F\) | max‖Δ‖ | 无向边 | 连通分量 | \(\delta^2\) | 式 (4) 近零根个数 |
| --- | --- | --- | --- | --- | --- | --- |
| olivetti | 是 | 0 | 1329 | 2 | 7.093 | 2 |
| att92 | 是 | 0 | 1273 | 3 | 9.337 | 3 |

att92 组合拉普拉斯前 8 个根含 3 个数值零（`combinatorial_laplacian_eigenvalues_A`），与 3 个连通分量一致。求解器 `scipy.linalg.eigh`。这不是聚类试验。

## D3–D6 单因子（ORL att92 SC；C 类 \(n=5\)）

对照默认 att92 SC 的前 5 个种子 mean ACC **54.6**（种子 0–4：53.00, 48.75, 54.75, 59.75, 56.75）。默认 \(n=50\) 是 56.2±4.2。

| 因子 | 改动 | 保真 | \(n\) | ACC | 边 / CC | \(\delta^2\) | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D03_BW_MEAN_SC | 有向 kNN 欧氏距离均值的平方 | B | 5 | 54.6±4.1 | 1273 / 3 | 9.171 | `20261021_161548__ROUND2__ORL__D03_BW_MEAN_SC__8f25437b` |
| D03_BW_UNDIRECTED_MEDIAN_SC | 无向边平方距离中位数 | B | 5 | 55.6±3.8 | 1273 / 3 | 10.499 | `20261021_161549__ROUND2__ORL__D03_BW_UNDIRECTED_MEDIAN_SC__96ae6849` |
| D04_MUTUAL_SC | 对称化 mutual（AND） | C | 5 | 49.6±3.8 | 727 / 46 | 同默认尺度 | `20261021_161550__ROUND2__ORL__D04_MUTUAL_SC__64f5f71e` |
| D06_ROW_NORM_SC | 行归一化特征向量 | C | 5 | 67.7±3.1 | 1273 / 3 | 9.337 | `20261021_161551__ROUND2__ORL__D06_ROW_NORM_SC__c17f11c3` |

带宽几乎不改边集。mutual 更差、分量更多，未升 50 次。行归一化 +11 pp 量级，**仍是 C**，即使 ACC 升高也未升 50 次。

## D7 \(W\) 建在 \(F\) 上（不是 \(X\)）

来源：att92 E8 `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0` 的 `w_vs_x_overlap`。

- `w_built_on`: **F**
- \(X\) 图无向边 1273；\(F\) 图无向边 1217；交 857；Jaccard **0.525**
- `identical_to_x_graph`: **false**
- 权重在 IRLS 前冻结

E13 同一重叠（同一 \(F\) 上建 \(W\)）：`20261021_161552__ROUND2__ORL__D08_E13_ATT92__a9ac25d0`。

## D8 E8 vs E13（ORL att92，\(\gamma=1\)，cluster \(G\)，\(n=50\)）

| 变体 | 线性系统 | 保真 | ACC | NMI | \(\lVert G-F\rVert_F\) | 式 (8) 目标 | IRLS | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E8 | \(A=S+2\gamma\widetilde L\) | A | 57.3±3.8 | 81.1±2.2 | 0.727 | 14.583 | 300 步未收敛 | `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0` |
| E13 | \(A=S+\gamma\widetilde L\) | B | 56.7±4.1 | 80.8±2.2 | 0.443 | 16.969 | 300 步未收敛 | `20261021_161552__ROUND2__ORL__D08_E13_ATT92__a9ac25d0` |
| SC / K-means(\(F\)) | 无收缩 | A | 56.2±4.2 | 80.5±2.3 | — | — | — | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` |

E8 目标更低，聚类不显著好于 E13 或 SC。相对论文 SSC 76.0：**E8 −18.7 pp**。未改优化器去追 ACC。

## D9 IRLS 最优性 / 收敛

| 设定 | \(n\) | 收敛 | 步数 | 式 (8) | ACC | run_id |
| --- | --- | --- | --- | --- | --- | --- |
| E8 max_iter=300 | 50 | 否 | 300 | 14.58275 | 57.3±3.8 | 同上 E8 |
| E8 max_iter=1000 | 5 | 是 | 825 | 14.58272 | 55.9±4.5 | `20261021_161555__ROUND2__ORL__D09_E8_ITER1000_ATT92__b959d78e` |

300 步固定点残差 0.013。加到 1000 步目标几乎不变，ACC 不升。未把 1000 步升到 50 次。

JAFFE E13 在 263 步收敛；JAFFE E8 300 步未收敛。USPS E8 298 步收敛。YaleB E8 两版本均 300 步未收敛。

## D10/D11 保存的 \(F\) 上的 K-means

\(F\) 只算一次，写入 `embedding_F.npy`。50 个 random 与 50 个 k-means++，`n_init=1`。mean±std 用全部 trial。最佳 inertia **单独**记录，其 ACC 不是选种规则。明细：`results/round2/d10_d11_kmeans_on_saved_f.json`。

| 保存的 \(F\) | 来源 run | random ACC | random 最佳 inertia 的 ACC | k-means++ ACC（B） | ++ 最佳 inertia 的 ACC |
| --- | --- | --- | --- | --- | --- |
| ORL olivetti SC | `…D01_OLIVETTI_SC__9118018b` | 53.9±3.0 | 62.75（seed 21，inertia 9.382） | 62.7±1.4 | 62.5（seed 37，inertia 5.469） |
| ORL att92 SC | `…D01_ATT92_SC__4fe80e2e` | 56.2±4.2 | 62.25（seed 21，inertia 9.935） | **78.3±1.3** | 79.0（seed 13，inertia 3.699） |
| ORL att92 E8 的 \(F\) | `…D08_E8_ATT92__d3809fd0` | 56.2±4.2 | 同 SC（同一 \(F\)） | 78.3±1.3 | 同 SC |
| JAFFE SC | `…D12_JAFFE_SC__2983a645` | 68.5±11.2 | 95.3（seed 23，inertia 0.623） | 95.3±0.0 | 95.3（seed 0，inertia 0.614） |

att92 上 SC 的 \(F\) 与 E8 保存的 \(F\) 给出相同的 random / ++ 数字，与 D2 逐元素一致相符。k-means++ 的 78.3 **超过**论文 SC 72.7 与 SSC 76.0；标 **B_AMBIGUITY**，不是忠实复现。

## D12 短名单 \(n=50\)（仅 ORL att92 与 JAFFE）

| 数据集 | 方法 | 保真 | ACC | NMI | run_id |
| --- | --- | --- | --- | --- | --- |
| ORL att92 | SC | A | 56.2±4.2 | 80.5±2.3 | `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` |
| ORL att92 | SSC E8 | A | 57.3±3.8 | 81.1±2.2 | `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0` |
| ORL att92 | SSC E13 | B | 56.7±4.1 | 80.8±2.2 | `20261021_161552__ROUND2__ORL__D08_E13_ATT92__a9ac25d0` |
| JAFFE zenodo | SC | A | 68.5±11.2 | 83.0±5.7 | `20261021_161557__ROUND2__JAFFE__D12_JAFFE_SC__2983a645` |
| JAFFE zenodo | SSC E8 | A | 68.4±11.1 | 83.0±5.7 | `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7` |
| JAFFE zenodo | SSC E13 | B | 68.6±11.3 | 83.0±5.8 | `20261021_161559__ROUND2__JAFFE__D12_JAFFE_E13__50a3c90d` |

论文：ORL SC 72.7 / SSC 76.0；JAFFE SC 76.1 / SSC 81.2。收缩相对 K-means(\(F\)) 的增益 < 2 pp。

## YaleB（E8 / SC，\(n=10\)，不是 50）

| version | 方法 | ACC | NMI | 边 / CC | IRLS | run_id |
| --- | --- | --- | --- | --- | --- | --- |
| dengcai32 | SC | 20.1±1.2 | 29.9±0.9 | 8568 / 1 | — | `20261021_161602__ROUND2__YALEB__D01_DENGCAI32_SC__6411988e` |
| dengcai32 | E8 | 19.5±1.5 | 29.3±1.2 | 8060 / 13 | 300 未收敛 | `20261021_161603__ROUND2__YALEB__D08_DENGCAI32_E8__27f746d1` |
| cropped2414 | SC | 18.1±1.3 | 26.6±0.6 | 8510 / 1 | — | `20261021_161625__ROUND2__YALEB__D01_CROPPED2414_SC__d1a360fb` |
| cropped2414 | E8 | 17.4±1.1 | 26.0±1.1 | 7957 / 13 | 300 未收敛 | `20261021_161626__ROUND2__YALEB__D08_CROPPED2414_E8__5fb5af8b` |

论文 YaleB SC 34.8、SSC 49.8。cropped 没有提升。邓蔡 SC 20.1 与 Round 1 相同。

## USPS（E8 / SC pilot，\(n=3\)，超时允许）

均 COMPLETED，未 TIMEOUT。

| 方法 | ACC | NMI | IRLS | run_id |
| --- | --- | --- | --- | --- |
| SC | 63.8±1.7 | 77.4±3.9 | — | `20261021_161647__ROUND2__USPS__D12_USPS_SC__6324d037` |
| E8 | 60.7±4.0 | 76.8±3.1 | 298 步收敛，\(\lVert G-F\rVert_F=0.071\) | `20261021_161650__ROUND2__USPS__D08_USPS_E8__c638f49b` |

论文 USPS SC 64.3、SSC 75.5。SC 的 \(n=3\) 点估计靠近 64.3；E8 低约 15 pp。\(n=3\) 不是论文 50 次协议。共享路径，无 \(n>1500\) 后端切换。

## 扩展：同一 \(F\) 上 mutual-kNN vs SSC（JAFFE \(n=50\)）

有时间，已跑。C 类。

| 方法 | ACC | 边 / CC | \(\lVert G-F\rVert_F\) | 收敛 | run_id |
| --- | --- | --- | --- | --- | --- |
| SSC E8 union | 68.4±11.1 | 655 / 9 | 0.093 | 否（300） | `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7` |
| RSSC mutual | 68.4±11.2 | 410 / 20 | 0.077 | 是（241） | `20261021_161924__ROUND2__JAFFE__EXT_JAFFE_MUTUAL_KNN__45fd1c1f` |

负结果：边更少、分量更多，ACC 无增益。

## 与论文仍差多少（忠实协议）

| 数据集 | 论文 SC | 我们 SC | 论文 SSC | 我们 E8 | 剩余 SC / E8（pp） |
| --- | --- | --- | --- | --- | --- |
| ORL att92 \(n=50\) | 72.7±2.3 | 56.2±4.2 | 76.0±1.6 | 57.3±3.8 | −16.5 / −18.7 |
| ORL olivetti \(n=50\) | 72.7 | 53.9±3.0 | 76.0 | （本轮未再跑 Olivetti E8） | −18.8 / — |
| JAFFE \(n=50\) | 76.1±1.6 | 68.5±11.2 | 81.2±1.6 | 68.4±11.1 | −7.6 / −12.8 |
| YaleB dengcai \(n=10\) | 34.8±1.4 | 20.1±1.2 | 49.8±1.6 | 19.5±1.5 | −14.7 / −30.3 |
| USPS \(n=3\) | 64.3±1.4 | 63.8±1.7 | 75.5±1.9 | 60.7±4.0 | −0.5 / −14.8（\(n=3\)） |

k-means++ 与行归一化的更高数字见 RCA，**不得写入忠实主表**。
