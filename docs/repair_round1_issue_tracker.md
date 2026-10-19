# 第一轮修复问题清单

日期：2026-10-20。数学变体这一阶段的记录。ORL 诊断、数据集下载、报告压缩和推送不在本阶段。

## Git 检查点

开工时工作区干净，没有做空提交。检查点就是当时的 `HEAD`：

`d73a6d1fe5cd514d1448e7c4e01d322e42bf1f9f`

分支 `v1`，与 `origin/v1` 一致。此前三条提交：

- `d73a6d1` Keep validation_report.json in sync with the markdown report.
- `6bd1373` Record post-commit validation and the origin/v1 403 push denial.
- `5d2d467` COMP3314 GP v1: faithful SSC reproduction, benchmark evaluation, method extension and report

本阶段之后若有新提交，那是数学变体检查点，不是最终修复，也不取代上面的哈希。

## 字段

每条都含：Issue ID，Severity，Affected component，Original paper reference，Current implementation，Confirmed discrepancy，Suspected cause，Proposed repair，Experiments required，Verification criteria，Final status。

没有把小凸核对写成 ORL 差距已修复。

## 总表

| Issue ID | Severity | Final status |
| --- | --- | --- |
| P0-EQ8-EQ13 | P0 | 小凸核对已验证；聚类差距未跑 |
| P0-EQ10-DIM | P0 | 已确认；仍用按行 \(n\times n\)，印出的嵌入维对角未实现 |
| P0-ALG1-L10 | P0 | 已确认；第 10 行仍不执行 |
| P0-ORL-ACC | P0 | 未修复；本阶段未重跑 |
| P0-YALEB-ACC | P0 | 未修复；本阶段未重跑 |
| P0-DATA-MISSING | P0 | 未修复；本阶段未下载 |
| P0-SPLS | P0 | 未修复；仍是 `NOT_IMPLEMENTED` |
| P0-REPORT-PAGES | P0 | 未修复；本阶段未改报告 |
| P1-STEP-VS-FP | P1 | 已在块例子上观察到；停止规则未改 |
| P1-E8-EPS-FLOOR | P1 | 已观察到；默认地板未改 |

## P0-EQ8-EQ13

- Severity: P0
- Affected component: `SSC_method/optimizer.py` 的线性系统；`SSC_method/objective.py` 的式 (8)
- Original paper reference: 式 (8)、式 (12)、式 (13)；证明中的式 (15)。\(\sum_{i,j}\) 为有序对
- Current implementation: 默认仍是印出的式 (13)，\(A=S+\gamma\widetilde L\)。新增 `variant="E8"`，\(A=S+2\gamma\widetilde L\)。省略参数的调用保持 E13
- Confirmed discrepancy: 有序对、式 (11) 的 \(1/2\) 和组合拉普拉斯下，式 (8) 的驻点系数是 2。式 (13) 的系数是 1，因为它来自少了一个 2 的式 (12)。\(n=6\) 的链和块上，CVXPY 1.9.3 / CLARABEL 0.11.1（`tol_gap_abs=tol_gap_rel=tol_feas=1e-10`）状态 `optimal`。E8 与式 (8) 的目标差约 \(10^{-10}\)，矩阵最大绝对差约 \(10^{-6}\)。E13 与图系数 \(\gamma/2\) 的问题达到同样的一致，而式 (8) 在 E13 的解上更大（链上约 \(4.537\) 对 \(4.021\)，块上约 \(3.656\) 对 \(3.652\)）
- Suspected cause: \(\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2=2\operatorname{Tr}(G^\top\widetilde L G)\)，式 (12) 写成了 \(\gamma\operatorname{Tr}\)，没有这个 2
- Proposed repair: 两个变体都保留。E13 是印出的线性步。E8 是按推导得到的式 (8) 驻点。后续诊断要分别报告，不能把其中一个叫成另一个
- Experiments required: 小凸核对已完成。ORL / YaleB 的单因子诊断未做，不能用这里的目标差解释 \(53.9\) 或 \(19.7\)
- Verification criteria: `tests/test_repair_round1_math.py` 中梯度有限差分、两种变体的维度和交叉残差、CLARABEL 的目标和矩阵、以及二次代理的 L-BFGS-B。式 (8)、平滑目标、IRLS 代理、不动点残差四项不相等
- Final status: 小凸核对已验证。聚类差距未验证，不标为已修复

## P0-EQ10-DIM

- Severity: P0
- Affected component: `SSC_method/objective.py` 的 `row_l21_diagonal`
- Original paper reference: 式 (9) 的迹 \(\operatorname{Tr}((G-F)^\top S(G-F))\)；式 (10) 的 \(\operatorname{diag}(1/(2\lVert h_1\rVert_2),\ldots,1/(2\lVert h_d\rVert_2))\)，\(d\) 为谱嵌入维数
- Current implementation: \(S\) 为 \(n\times n\)，\(S_{ii}=1/(2\max(\lVert h_i\rVert_2,\varepsilon))\)，\(h_i\) 是 \(G-F\) 的第 \(i\) 行
- Confirmed discrepancy: \(\widetilde L\) 是 \(n\times n\)，式 (13) 要求 \(S\) 同阶。长度为 \(c\) 的对角不能加进 \(S+\gamma\widetilde L\)，也乘不进式 (9) 的迹。式 (8) 的 \(\ell_{2,1}\) 是对样本行求和
- Suspected cause: 式 (10) 把行残差和嵌入坐标轴混写
- Proposed repair: 保持按行的 \(n\times n\)。不把式 (10) 的嵌入维对角做成可执行分支
- Experiments required: 无聚类实验。维度核对已在既有 `test_row_wise_s_shape_and_hand_value` 和新的变体测试里
- Verification criteria: \(S\) 的对角长度等于样本数。\(c\neq n\) 时它不等于嵌入维数
- Final status: 已确认。实现保持行加权。印出的式 (10) 仍未按字面执行，因为那个对角不可执行。不标为“已按式 (10) 修复”

## P0-ALG1-L10

- Severity: P0
- Affected component: `SSC_method/optimizer.py`
- Original paper reference: Algorithm 1 第 10 行 \(G_{t+1}=(S_t+\gamma\widetilde W)^{-1}S_t X\)；第 4 行把依赖 \(G\) 的 \(\widetilde W\) 放在循环外。对照式 (13) 的 \(\widetilde L\) 和 \(F\)
- Current implementation: 求解 \((S+c\gamma\widetilde L)G=SF\)。\(c=1\) 为 E13，\(c=2\) 为 E8。不乘 \(X\)，不用 \(\widetilde W\) 代替 \(\widetilde L\)。\(\widetilde W\) 每步按当前 \(G\) 重算
- Confirmed discrepancy: 第 10 行的矩阵是 \(\widetilde W\) 不是 \(\widetilde L\)，右端是 \(X\) 不是 \(F\)。论文中 \(X\in\mathbb{R}^{d\times n}\)，与 \(F\) 不同形
- Suspected cause: Algorithm 1 与式 (13) 的排版不一致
- Proposed repair: 继续不执行第 10 行。线性系统只在 E13 与 E8 之间选择
- Experiments required: 无。不把第 10 行当作待跑的聚类因子
- Verification criteria: 求解调用的是 `spsolve` 和 \(\widetilde L\)，源码中没有显式逆。右端是 \(SF\)
- Final status: 已确认。第 10 行仍不执行。这是保持式 (13) / E8，不是把第 10 行修好

## P0-ORL-ACC

- Severity: P0
- Affected component: ORL 上的 SSC 聚类结果；`report/main.tex` 所引的 Track A
- Original paper reference: Chang et al. 表中的 ORL SSC，\(76.0\pm 1.6\)（报告对表 1–2 的引用）
- Current implementation: 报告中的复现是 \(53.9\pm 3.0\)，\(n=50\)，\(\gamma=10^{-6}\)，且 \(\gamma\) 按标签选择。数据是 Olivetti \(64\times 64\) 双线性缩到 \(32\times 32\)，不是论文的 \(92\times 112\) 再缩到 \(32\times 32\)
- Confirmed discrepancy: \(53.9\) 与 \(76.0\) 的差距记在现有报告里。本阶段没有重新测量
- Suspected cause: 尚未分离。候选包括式 (8)/(13) 的系数、带宽、嵌入、初始化、图像尺寸和插值。本阶段只实现了系数变体，没有检验哪一个造成差距
- Proposed repair: 后续单因子诊断再决定。E8 不能事先写成 ORL 的修复
- Experiments required: ORL 单因子矩阵，同一数据和同一 K-means 种子下比较 \(F\)、\(G_{E13}\)、\(G_{E8}\)。本阶段明确不做
- Verification criteria: 新的 run 目录、实际试验次数，以及与 \(76.0\pm 1.6\) 的差距。现有 \(53.9\) 不能被改写
- Final status: 未修复

## P0-YALEB-ACC

- Severity: P0
- Affected component: YaleB 上的 SSC 聚类结果
- Original paper reference: Chang et al. 表中的 YaleB SSC，\(49.8\pm 1.6\)
- Current implementation: 报告中的复现是 \(19.7\pm 1.1\)，\(n=10\)，不是 50。数据是 Deng Cai 的 `YaleB_32x32.mat`
- Confirmed discrepancy: \(19.7\) 与 \(49.8\) 的差距记在现有报告里。本阶段没有重新测量
- Suspected cause: 与 ORL 相同，尚未分离。试验次数和图像来源本身就和论文协议不同
- Proposed repair: 在 ORL 上验证过的设定再移到 YaleB。不满 50 次就写实际次数
- Experiments required: 本阶段不做
- Verification criteria: 实际 \(n\)、数据来源，以及与 \(49.8\pm 1.6\) 的差距
- Final status: 未修复

## P0-DATA-MISSING

- Severity: P0
- Affected component: `benchmarks/ar`、`benchmarks/umist`、`benchmarks/binalpha`、`benchmarks/msra50`
- Original paper reference: AR、UMIST、BinAlpha、MSRA50 的样本数和图像尺寸，见论文实验节
- Current implementation: 这四个数据集没有可用的本地文件。ORL 与 YaleB 是近似来源，不是逐像素同一文件
- Confirmed discrepancy: 报告已写明四个数据集未取得。本阶段没有下载，也没有把别的集合顶名
- Suspected cause: 公开链接失效或许可不允许再分发。另一阶段在做回收
- Proposed repair: 只接入能核对样本数的文件。找不到就记 URL、日期和 HTTP 状态
- Experiments required: 数据回收不在本提交里。本提交不加入 `benchmarks/` 下的新数据
- Verification criteria: 清单中的样本数、尺寸和校验和。没有这些之前，对应单元格保持未复现
- Final status: 未修复

## P0-SPLS

- Severity: P0
- Affected component: `baselines/spls/spls.py`
- Original paper reference: Hou, Nie, Jiao, Zhang, Wu，Information Processing & Management 2013；Chang et al. 将其写作 SPLS，原文缩写为 SLPS
- Current implementation: `fit_predict` 抛出 `NotImplementedError`，不替换成 K-means 或谱聚类
- Confirmed discrepancy: 论文比较表含 SPLS。仓库里没有 SPLS 的数字
- Suspected cause: 开放摘要没有第 3 节的更新公式，也没有官方代码
- Proposed repair: 只有目标函数和算法写清楚才实现。否则保持 `NOT_IMPLEMENTED`
- Experiments required: 全文检索不在本阶段
- Verification criteria: 实现必须能对着写出的更新式做小例子。在此之前结果单元格是未复现
- Final status: 未修复

## P0-REPORT-PAGES

- Severity: P0
- Affected component: `report/main.tex` 的正文（标题到结论，含摘要）
- Original paper reference: 课程要求正文最多 4 页。参考文献和附录不计入。不改 `neurips_2026.sty` 的字号、页边距和行距
- Current implementation: `docs/validation_report.md` 记录编译后的 PDF 为 22 页。本阶段没有改 `report/`
- Confirmed discrepancy: 现有 PDF 不是 4 页正文的成品。正文结束页、参考文献起始页和附录起始页这一阶段没有重测
- Suspected cause: 复现说明、偏差和实验叙述都写在正文里
- Proposed repair: 实验完成后再压正文。长推导放附录
- Experiments required: 无数学实验。需要 `pdfinfo` 和分页核对，本阶段不做
- Verification criteria: 正文结束页到第 4 页或之前，且正文能独立读完。编译失败不能写成成功
- Final status: 未修复

## P1-STEP-VS-FP

- Severity: P1
- Affected component: `shrink_embedding` 的 `converged` 旗标与 `fixed_point_residual`
- Original paper reference: 论文没有停止准则。实现用相对 Frobenius 步长
- Current implementation: 步长 \(\lVert G_{t+1}-G_t\rVert_F\le\mathrm{tol}(1+\lVert G_t\rVert_F)\) 时 `converged=True`。不动点残差另算
- Confirmed discrepancy: 块图、E13、\(\gamma=0.8\)、`tol=1e-8` 在第 57 步标成收敛，步长 \(2.18\times 10^{-8}\)，冻结线性残差 \(1.06\times 10^{-6}\)，重算权重后的不动点残差为 \(0.361\)。同一例子跑到不动点残差 \(1.41\times 10^{-6}\) 时，步长仍在约 \(10^{-7}\) 抖动，`converged` 为假，但目标已经和 CLARABEL 一致
- Suspected cause: \(\widetilde W\) 对很小的距离敏感，步长变小不等于 \(AG=SF\) 已在当前 \(G\) 上成立
- Proposed repair: 诊断里同时记录步长旗标和不动点残差。未收敛不写成成功。本阶段不改停止规则
- Experiments required: 已有块例子。不需要数据集
- Verification criteria: `test_block_e13_small_step_is_not_a_small_fixed_point_residual` 要求该例子上步长收敛与大于 \(0.1\) 的不动点残差同时出现
- Final status: 现象已验证。停止规则未改，不标为已修复

## P1-E8-EPS-FLOOR

- Severity: P1
- Affected component: `zero_residual_floor="eps"` 在 E8 上的迭代
- Original paper reference: 式 (10) 在 \(G_0=F\) 时除以零。论文没有 \(\varepsilon\)
- Current implementation: 默认地板仍是 `median_pairwise`，只用于第一次全零残差。`"eps"` 保留。E13 在线性间距的链式例子上停在 \(F\) 的 \(1.41\times 10^{-8}\) 邻域内
- Confirmed discrepancy: 同一例子上 E8 的第一步是 \(2.83\times 10^{-8}\)，30 步后 \(\lVert G-F\rVert_F=0.390\)，式 (8) 降到 \(2.277\)，不动点残差 \(0.987\)，没有收敛
- Suspected cause: 因子 2 的第一步把部分行残差推出 \(\varepsilon\)，随后 \(S\) 变小，迭代离开 \(F\)。E13 的第一步停在地板内部
- Proposed repair: 不删除 `"eps"`。默认仍是 `median_pairwise`。以后的初始化实验要把 E8 加 `"eps"` 单独记录，不能沿用“停在 \(F\)”描述 E8
- Experiments required: 初始化对比属于后续诊断。本阶段只保留这个反例
- Verification criteria: E13 加 `"eps"` 的位移小于 \(10^{-5}\)；E8 加 `"eps"` 能跑，且第一步小于 \(10^{-6}\)
- Final status: 现象已验证。默认地板未改
