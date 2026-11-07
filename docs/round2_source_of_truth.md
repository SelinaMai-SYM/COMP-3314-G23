# Round 2 source of truth（索引）

日期：2026-10-21。工作区：`v1/`。本文件是索引，**不重复**各数据集的完整表格。细节、SHA-256、实验归属和复现命令在各包 README：

- [benchmarks/orl/README.md](../benchmarks/orl/README.md)
- [benchmarks/jaffe/README.md](../benchmarks/jaffe/README.md)
- [benchmarks/yaleb/README.md](../benchmarks/yaleb/README.md)
- [benchmarks/usps/README.md](../benchmarks/usps/README.md)
- [benchmarks/ar/README.md](../benchmarks/ar/README.md)
- [benchmarks/umist/README.md](../benchmarks/umist/README.md)
- [benchmarks/binalpha/README.md](../benchmarks/binalpha/README.md)
- [benchmarks/msra50/README.md](../benchmarks/msra50/README.md)

HTTP 全日志：[round2_missing_resources.md](round2_missing_resources.md)、[round2_http_log.json](round2_http_log.json)。

校验和均为 2026-10-21 对本机文件重算，或对新下载文件当场计算。没有编造。未覆盖已有 archive。默认 `load_dataset("ORL")` / `load_dataset("YaleB")` 未改。未改 `SSC_method/` 优化器，未重写报告，未 git commit。

README 保真词（八档）与下表六档同时使用：NOT_FOUND / CANDIDATE_FOUND / DOWNLOADED_UNVERIFIED / SOURCE_VERIFIED / SAMPLE_SET_RECONSTRUCTED / PREPROCESSING_VERIFIED / PAPER_PROTOCOL_MATCHED / FULLY_REPRODUCED。

## 数据集六档

符号：Y = 是；N = 否；P = 部分（论文未写全）；R = 仅 reconstruction；U = 身份未核实。

| 数据集 | SOURCE_FOUND | ARCHIVE_DOWNLOADED | CONTENTS_VERIFIED | SAMPLE_SET_MATCHED | PREPROCESSING_MATCHED | FULL_PROTOCOL_REPRODUCED | README 总评 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ORL `att92` | Y | Y | Y | Y（400/40） | P（32×32 已做，插值未写） | N | PREPROCESSING_VERIFIED |
| ORL 默认 Olivetti | Y（另一来源） | Y | Y | Y（400/40） | N（64×64 不是 92×112） | N | SOURCE_VERIFIED（对 mat） |
| JAFFE | Y | Y | Y | Y（213/10） | P（26×26 双线性） | N | SOURCE_VERIFIED |
| YaleB `cropped2414` | Y | Y | Y | Y（2414/38，去 Ambient） | P | N | SOURCE_VERIFIED |
| YaleB 默认邓蔡 | Y | Y | Y | Y（计数） | N（缩放核未知） | N | SOURCE_VERIFIED（对 mat） |
| USPS | Y | Y | Y | Y（9298/10） | P（发布已是 16×16） | N | SOURCE_VERIFIED |
| AR | N（官方）；候选 Zenodo 已拒 | N | N | N（840/120 未写） | N | N | NOT_FOUND |
| UMIST 564 | P（页写 564，文件不是） | Y（1012/575） | Y（对已有档案） | N | N | N | CANDIDATE_FOUND，样本集未匹配 |
| BinAlpha 论文集 | U | Y（父集） | Y（36×39×20×16） | R（26×30 seed0） | P（父集无需缩放） | N | SAMPLE_SET_RECONSTRUCTED / UNVERIFIED |
| MSRA50 | P（文献指针，无 URL） | N | N | N | N | N | CANDIDATE_FOUND → NOT_FOUND |

没有一个数据集达到 **FULL_PROTOCOL_REPRODUCED** 或 **PAPER_PROTOCOL_MATCHED**。

## 回收结论（短）

- **BinAlpha 子集存在：** `version="letters26x30_seed0"`，780 张，索引在 `benchmarks/binalpha/reconstructions/letters26x30_seed0.json`。默认名仍不可用。36 类全集不是论文 BinAlpha。
- **AR：** Zenodo `ARDB_Full.zip` HEAD 200 / 120587997 字节，上传者不是官方，声称 CC-BY 与官方禁再分发冲突。**未下载、未使用。**
- **MSRA50：** Nie/Yang 同组文引用 He et al. 2004 给出 1799/12/1024；He ICCV 2003 / TPAMI 2005 只有 12 人与 64–80/场，无 1799、无文件。未替换其它 MSRA 库。
- **UMIST：** 575 裁剪包文件名无重复；10 组像素重复（`1b` 的 `final*.pgm`）。去掉后是 565，不是 564。未删 11 张。

## 基线保真

依据 `baselines/*/…py` 与 [repair_round1_baseline_audit.md](repair_round1_baseline_audit.md)。无作者二进制，故无 **ORIGINAL_CODE_VERIFIED**。

| 方法 | 标签 | 说明 |
| --- | --- | --- |
| K-means | PAPER_FAITHFUL_REIMPLEMENTATION | Lloyd + `init="random"`。k-means++ 是 AMBIGUITY_RECONSTRUCTION，不是默认。 |
| Spectral clustering | PAPER_FAITHFUL_REIMPLEMENTATION | 式 (4)，k=5，不用 sklearn `SpectralClustering`。带宽与 union kNN 为 AMBIGUITY_RECONSTRUCTION。 |
| PCA-KM | PAPER_FAITHFUL_REIMPLEMENTATION | 居中、不默认白化。维数步长 10 为 AMBIGUITY_RECONSTRUCTION。 |
| PCA-SC | PAPER_FAITHFUL_REIMPLEMENTATION | PCA 后接式 (4)。 |
| LDA-KM | PAPER_FAITHFUL_REIMPLEMENTATION | Ding–Li 交替，伪标签。 |
| LDA-SC | APPROXIMATE | Chang 未写循环；不进忠实主表。 |
| LLC | PAPER_FAITHFUL_REIMPLEMENTATION | Wu & Schölkopf。k=5 是比较协议。 |
| SPLS / SLPS | NOT_IMPLEMENTED | 第 3 节仍未读到。 |

Round 1 数字只作历史对照，见 `results/repair_round1/`。
