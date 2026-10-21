# MSRA50

论文身份状态：**CANDIDATE_FOUND**（文献指针）后仍 **NOT_FOUND**（无文件）。Strict URL 轮：`BLOCKED_DATA_NOT_OBTAINED`。计数相符不等于身份。不是 **DOWNLOADED_UNVERIFIED**。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)。清单：`manifest.yaml`。

## 身份

Chang et al. 写 MSRA50：1799 张、12 类、缩到 32×32。无 URL、无引用。

同组 Chang, Nie, Yang 等，*Improved Spectral Clustering via Embedded Label Propagation*（arXiv:1411.6241）写：“The MSRA50 dataset (He et al. 2004) consists of 1799 images and 12 classes”，表列为 1024 维。其参考文献 “He et al. 2004” 实为 *Face Recognition Using Laplacianfaces*, IEEE TPAMI 27(3):328–340（期刊 2005）。

He, Yan, Hu, Zhang，ICCV 2003 *Learning a Locality Preserving Subspace for Visual Recognition*，以及 He, Yan, Hu, Niyogi, Zhang，TPAMI 2005：MSRA 库在微软亚洲研究院采集，**12 人**，每人每场 **64–80** 张正面，两场，裁到 **32×32**。**两文都不写 1799，都没有下载地址。**

12×2×(64..80) = 1536..1920，1799 落在区间内。这只说明算术可能，**不能**当作已找到该文件。

## Chang et al. 2015 原文 vs 推断

- **原文：** 1799 / 12 / 32×32。
- **推断（不升格）：** 可能是 He 的 MSRA 人脸两场合计后的某个裁剪矩阵。
- **禁止：** 用 MSRA-B、MSRA10K、MSRA-TD500、MSRA-CFW 顶名。清华 TUNA / PyPI 不是数据集源。

## 本机文件

无。无 SHA-256。

## 本轮实际请求

| URL | HTTP | 结果 |
| --- | --- | --- |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` | 200 | 页面无 MSRA50 / BinAlpha 文件 |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` | 200 | 仅 Yale / ORL / Extended Yale B |
| `https://lear.inrialpes.fr/people/triggs/events/iccv03/cdrom/iccv03/0385_he.pdf` | 200 | ICCV 2003 全文；MSRA 无 1799、无 URL |
| `https://people.engr.tamu.edu/rgutier/web_courses/cpsc689_s07/he2005laplacianfaces.pdf` | 200 | TPAMI 2005 副本；12 人、64–80/场 |
| `https://arxiv.org/abs/1411.6241` | 200 | 同组论文引用 He 2004 + 1799/12/1024 |
| `https://arxiv.org/pdf/1411.6241.pdf` | 404 | 该 PDF 路径当天无效 |

未下载任何 MSRA-B / 10K / TD500。

## 版本对照

无。`load_dataset("MSRA50")` 抛 `DatasetUnavailable`。

## 样本选择 / 预处理

未知。未应用。

## 完整性测试（已跑）

```text
python3 -m pytest benchmarks/msra50/test_msra50.py -q
```

## 哪些实验用了这个版本

无。Phase 1 / repair_round1 / Round 2 都没有 MSRA50 作业。无文件。

## 复现命令（本轮实测）

```python
from benchmarks import load_dataset
from benchmarks.exceptions import DatasetUnavailable
try:
    load_dataset("MSRA50")
except DatasetUnavailable as exc:
    assert "1799" in str(exc)
```

## Task 1（2026-10-21）

仍无 1799/12 文件。邓蔡三页 HTTP **200**，无 MSRA50。GitHub 仓库搜索 `MSRA50 mat` `total_count=0`。新保存同组 OA：`resources/Chang_Nie_Yang_Huang_2014_arxiv_1411.6241v1.pdf` 463461 字节 SHA-256 `d3d00b0fa2eeff938d65800a3a7e4d1b08987de73932e9bd04de801e708badb2`（`arxiv.org/pdf/1411.6241v1.pdf` **200**；无版本路径 **404**）。未下 MSRA-B/10K/TD500。矩阵状态：`NOT_FOUND`。

## Strict URL Task 1（2026-10-21 晚）

无下载 URL。本地 `data/` 仍空。UTS 署名 AAAI PDF 与同组 1411.6241v1 只有 1799/12/1024 文献计数。状态：`BLOCKED_DATA_NOT_OBTAINED`。
