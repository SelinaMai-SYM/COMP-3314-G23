# 第一轮修复问题清单

日期：2026-10-20。数学变体、ORL 诊断、数据回收、转移实验和四页报告都已做完。数字来自 `runs/repair_round1/` 与 `results/repair_round1/`。**没有把 ORL 76% 标成已复现。**

## Git 检查点

开工时工作区干净，没有做空提交。检查点就是当时的 `HEAD`：

`d73a6d1fe5cd514d1448e7c4e01d322e42bf1f9f`

数学变体检查点：`a29efda`（Add E13 and E8 shrinkage variants as a math checkpoint）。报告与数据回收的收尾提交另记。

此前提交：

- `d73a6d1` Keep validation_report.json in sync with the markdown report.
- `6bd1373` Record post-commit validation and the origin/v1 403 push denial.
- `5d2d467` COMP3314 GP v1: faithful SSC reproduction, benchmark evaluation, method extension and report

## 字段

每条都含：Issue ID，Severity，Affected component，Original paper reference，Current implementation，Confirmed discrepancy，Suspected cause，Proposed repair，Experiments required，Verification criteria，Final status。

没有把小凸核对写成 ORL 差距已修复。

## 总表

| Issue ID | Severity | Final status |
| --- | --- | --- |
| P0-EQ8-EQ13 | P0 | 小凸核对已验证。聚类上 E8 未填上 ORL/YaleB 差距（ORL E8 53.3±3.2 n=50；YaleB E8 19.5±1.5 n=10） |
| P0-EQ10-DIM | P0 | 已确认；仍用按行 \(n\times n\)，印出的嵌入维对角未实现 |
| P0-ALG1-L10 | P0 | 已确认；第 10 行仍不执行 |
| P0-ORL-ACC | P0 | **未修复。** 忠实 E8 53.3±3.2（n=50）对论文 76.0±1.6。att92 n=5 最高约 58.8。禁止写成已复现 76% |
| P0-YALEB-ACC | P0 | **未修复。** E8 19.5±1.5（n=10，不是 50）对论文 49.8±1.6。cropped2414 E13 18.0±0.7 |
| P0-DATA-MISSING | P0 | 部分回收。att92 与 cropped2414 已取得，默认加载器未改。AR / BinAlpha / MSRA50 仍无。UMIST 是 1012/575，不是 564 |
| P0-SPLS | P0 | 未修复；仍是 `NOT_IMPLEMENTED` |
| P0-REPORT-PAGES | P0 | 已压正文。`pdfinfo` 13 页；结论与致谢在第 4 页结束；References 起于第 4 页；附录起于第 5 页。无 Overfull |
| P1-STEP-VS-FP | P1 | 已在块例子上观察到；停止规则未改。ORL/YaleB \(\gamma=1\) IRLS 常未达 \(10^{-6}\) |
| P1-E8-EPS-FLOOR | P1 | 已观察到；默认地板未改 |

## P0-EQ8-EQ13

- Severity: P0
- Affected component: `SSC_method/optimizer.py` 的线性系统；`SSC_method/objective.py` 的式 (8)
- Original paper reference: 式 (8)、式 (12)、式 (13)；证明中的式 (15)。\(\sum_{i,j}\) 为有序对
- Current implementation: 默认仍是印出的式 (13)，\(A=S+\gamma\widetilde L\)。新增 `variant="E8"`，\(A=S+2\gamma\widetilde L\)。省略参数的调用保持 E13
- Confirmed discrepancy: 有序对、式 (11) 的 \(1/2\) 和组合拉普拉斯下，式 (8) 的驻点系数是 2。式 (13) 的系数是 1，因为它来自少了一个 2 的式 (12)。\(n=6\) 的链和块上，CVXPY 1.9.3 / CLARABEL 0.11.1（`tol_gap_abs=tol_gap_rel=tol_feas=1e-10`）状态 `optimal`。E8 与式 (8) 的目标差约 \(10^{-10}\)，矩阵最大绝对差约 \(10^{-6}\)。E13 与图系数 \(\gamma/2\) 的问题达到同样的一致，而式 (8) 在 E13 的解上更大（链上约 \(4.537\) 对 \(4.021\)，块上约 \(3.656\) 对 \(3.652\)）
- Suspected cause: \(\sum_{ij}\widetilde W_{ij}\lVert g_i-g_j\rVert_2^2=2\operatorname{Tr}(G^\top\widetilde L G)\)，式 (12) 写成了 \(\gamma\operatorname{Tr}\)，没有这个 2
- Proposed repair: 两个变体都保留。E13 是印出的线性步。E8 是按推导得到的式 (8) 驻点。后续诊断要分别报告，不能把其中一个叫成另一个
- Experiments required: 小凸核对已完成。ORL / YaleB / JAFFE 短名单已跑：E8 并不比 E13 或 \(K\)-means(\(F\)) 更好
- Verification criteria: `tests/test_repair_round1_math.py` 中梯度有限差分、两种变体的维度和交叉残差、CLARABEL 的目标和矩阵、以及二次代理的 L-BFGS-B。式 (8)、平滑目标、IRLS 代理、不动点残差四项不相等
- Final status: 小凸核对已验证。E8 是忠实驻点，但不是 ORL 76% 的修复。不标为聚类差距已修复

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
- Confirmed discrepancy: 忠实 E8 ACC \(53.3\pm 3.2\)（n=50，`20261020_032508__REPAIR1__ORL__D12_KMEANS_G_E8__d484f3c9`）对论文 \(76.0\pm 1.6\)。E13 \(53.7\pm 2.8\)。\(K\)-means(\(F\)) \(53.9\pm 3.0\)。收缩没有帮助。k-means++（B）\(62.1\pm 1.6\) 仍差约 14 点。行归一化（C）\(60.2\pm 2.9\) 不是论文方法。att92 双线性 E13 \(53.9\pm 3.8\)（n=5）；最近邻 \(58.8\pm 5.3\)（n=5）
- Suspected cause: 单因子矩阵未找到能接近 76% 的 A/B 设定。剩余候选包括未公开的 2015 预处理、未公开的 \(K\)-means 细节，以及图像身份
- Proposed repair: 不把任何 C 类结果写成复现。作者问题见 `docs/repair_round1_author_questions.md`
- Experiments required: 已做 ORL 单因子 + n=50 短名单。无效变体没有扩到 50
- Verification criteria: 新的 run 目录、实际试验次数，以及与 \(76.0\pm 1.6\) 的差距。现有 \(53.9\) / \(53.3\) 不能被改写成 76
- Final status: **未修复。禁止声称 ORL 76% 已复现**

## P0-YALEB-ACC

- Severity: P0
- Affected component: YaleB 上的 SSC 聚类结果
- Original paper reference: Chang et al. 表中的 YaleB SSC，\(49.8\pm 1.6\)
- Current implementation: 邓蔡 mat 上 E8 \(19.5\pm 1.5\)（n=10），E13 \(19.7\pm 1.1\)（n=10）。不是 50 次
- Confirmed discrepancy: 与论文 \(49.8\pm 1.6\) 仍差约 30 点。cropped2414 双线性 E13 \(18.0\pm 0.7\)（n=10）没有提升。k-means++（B）\(25.2\pm 0.6\)；行归一化（C）\(26.7\pm 1.8\)
- Suspected cause: 与 ORL 相同，尚未分离。试验次数和图像来源本身就和论文协议不同。不声称与论文逐样本同一
- Proposed repair: 不满 50 次就写实际次数。不把 C 写成忠实
- Experiments required: 已转移 E8/E13/\(F\)/++/row-norm/cropped2414；n=10
- Verification criteria: 实际 \(n\)、数据来源，以及与 \(49.8\pm 1.6\) 的差距
- Final status: **未修复**

## P0-DATA-MISSING

- Severity: P0
- Affected component: `benchmarks/ar`、`benchmarks/umist`、`benchmarks/binalpha`、`benchmarks/msra50`
- Original paper reference: AR、UMIST、BinAlpha、MSRA50 的样本数和图像尺寸，见论文实验节
- Current implementation: 默认 `load_dataset("AR"|"UMIST"|"BinAlpha"|"MSRA50")` 仍抛 `DatasetUnavailable`。额外版本：ORL `att92`（400 张 92×112）、YaleB `cropped2414`（2414 张）、UMIST 1012/575。默认 ORL/YaleB 加载器未改
- Confirmed discrepancy: AR、BinAlpha、MSRA50 仍无文件。UMIST 读到的不是 564。没有用 Binary Alphadigits 或其它 MSRA 集合顶名
- Suspected cause: 公开链接失效、WAF、许可，或论文子集无法从现有档案重建
- Proposed repair: 只接入能核对样本数的文件。找不到就记 URL、日期和 HTTP 状态。见 `docs/repair_round1_dataset_recovery.md`
- Experiments required: 回收已做。att92 / cropped2414 的聚类没有填上论文 ACC
- Verification criteria: 清单中的样本数、尺寸和校验和。没有 564 / 26×30 / 1799×12 之前，对应单元格保持未复现
- Final status: 部分回收；论文计数下的四个名字仍未对齐。不标成数据问题已关闭

## P0-SPLS

- Severity: P0
- Affected component: `baselines/spls/spls.py`
- Original paper reference: Hou, Nie, Jiao, Zhang, Wu，Information Processing & Management 2013；Chang et al. 将其写作 SPLS，原文缩写为 SLPS
- Current implementation: `fit_predict` 抛出 `NotImplementedError`，不替换成 K-means 或谱聚类
- Confirmed discrepancy: 论文比较表含 SPLS。仓库里没有 SPLS 的数字
- Suspected cause: 开放摘要没有第 3 节的更新公式，也没有官方代码
- Proposed repair: 只有目标函数和算法写清楚才实现。否则保持 `NOT_IMPLEMENTED`
- Experiments required: 2026-10-20 全文检索见 `docs/repair_round1_baseline_audit.md`。Unpaywall/OpenAlex 非 OA，arXiv 0 hits，作者页 PDF 链到 Elsevier DOI
- Verification criteria: 实现必须能对着写出的更新式做小例子。在此之前结果单元格是未复现
- Final status: 未修复。仍是 `NOT_IMPLEMENTED`

## P0-REPORT-PAGES

- Severity: P0
- Affected component: `report/main.tex` 的正文（标题到结论，含摘要）
- Original paper reference: 课程要求正文最多 4 页。参考文献和附录不计入。不改 `neurips_2026.sty` 的字号、页边距和行距
- Current implementation: 重写后的 `report/main.tex` 使用 `\usepackage[preprint]{neurips_2026}`，未改 `neurips_2026.sty`。`latexmk -pdf` 成功。`pdfinfo`：13 页，letter。`pdftotext -layout`：第 4 页含 `6 Conclusion`、`Acknowledgments` 和 `References` 标题；第 5 页参考文献续页后进入附录 A；第 6 页附录 B；第 7 页清单。`rg Overfull main.log` 无匹配。`Group_23.pdf` 与 `main.pdf` 字节相同
- Confirmed discrepancy: 旧 22 页叙述已删除。正文（标题到结论，含摘要与致谢）结束于第 4 页
- Suspected cause: 已压缩
- Proposed repair: 已执行
- Experiments required: 无。检查命令见 `docs/repair_round1_validation.md`
- Verification criteria: 正文结束页到第 4 页或之前，且正文能独立读完。编译失败不能写成成功
- Final status: 正文 4 页目标已满足（检查时间 2026-10-20 03:49 CST）

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
