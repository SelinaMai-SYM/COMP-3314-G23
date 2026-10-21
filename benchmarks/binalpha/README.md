# BinAlpha

论文 BinAlpha 身份：**CANDIDATE_FOUND**（Binary Alphadigits 父集）后仍为 **UNVERIFIED**。26×30 是 **SAMPLE_SET_RECONSTRUCTED**，**不是**论文样本集。36 类全集 **禁止**叫作论文 BinAlpha。默认加载器仍不可用。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)。清单：`manifest.yaml`。索引文件：`reconstructions/letters26x30_seed0.json`。

## 身份

Chang et al. 只写“26 个二进制手写字母，每类随机 30 张”，无出处、无尺寸、无种子。本轮下载的是 **Binary Alphadigits**（Simon Lucas / Algoval；Roweis MATLAB 转储）：0–9 与 A–Z，每类 39 张，20×16，共 36×39=1404。

**未找到** Chang 使用该集的直接证据（AAAI 正文、arXiv:1411.6308、同组 1411.6241 均未写 Binary Alphadigits）。身份保持 **UNVERIFIED**。

## Chang et al. 2015 原文 vs 推断

- **原文：** 26 个字母，每类随机 30 张。
- **未写：** 父集、种子、图像大小、是否含数字。
- **推断（不升格）：** 26 个字母很像 Binary Alphadigits 去掉 10 个数字后再抽样。这只是候选，不是证据。

## 本机文件（2026-10-21 新下载，未覆盖任何旧 archive——原先没有）

| 文件 | 字节 | SHA-256 | HTTP |
| --- | --- | --- | --- |
| `data/binaryalphadigs.mat` | 532304 | `3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7` | 现网 `cs.nyu.edu/~roweis/data/binaryalphadigs.mat` GET **403**；Wayback `20240616024002id_` GET **200** |

许可：mat 内无许可证；Wayback Roweis 页无许可声明。档案 gitignore。索引 JSON 可提交。

## 版本对照

| version | n | 类 | 是否论文 BinAlpha |
| --- | --- | --- | --- |
| 默认 / `paper` | — | — | 否；`DatasetUnavailable` |
| `binaryalphadigs36` | 1404 | 36 | **否** |
| `letters26x30_seed0` | 780 | 26 | **否**（reconstruction，UNVERIFIED） |

## 样本选择

重建规则（已写入 JSON，可重放）：

- 丢掉 `classlabels` 中的 `0`–`9`。
- 对 `A`–`Z`（父下标 10–35），`numpy.random.RandomState(0).choice(39, size=30, replace=False)`，再排序。
- 种子 **0 是本仓库的重建种子**，不是 Chang 的种子。

## 预处理

细胞已是 `uint8` 20×16、值 ∈ {0,1}。不缩放，不除以 255，C 序拉直到 320 维。

## 完整性测试（已跑）

```text
python3 -m pytest benchmarks/binalpha/test_binalpha.py -q
```

默认必须不可用；36 类必须是 `(1404, 320)`；26×30 必须是 `(780, 320)` 且 `identity == "UNVERIFIED"`。

## 哪些实验用了这个版本

无。Phase 1 / repair_round1 / Round 2 都没有 BinAlpha 聚类作业。不要把 36 类或 26×30 重建结果写进论文 BinAlpha 格。

## 复现命令（本轮实测）

```python
from benchmarks import load_dataset
from benchmarks.exceptions import DatasetUnavailable
try:
    load_dataset("BinAlpha")
except DatasetUnavailable:
    pass
X, y, m = load_dataset("BinAlpha", version="letters26x30_seed0")
assert X.shape == (780, 320) and m["not_paper_binalpha"] is True
```

## Task 1（2026-10-21）哈希复核

未重下。`data/binaryalphadigs.mat` 532304 字节 SHA-256 `3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7`。论文 26×30 仍 `NOT_FOUND`；`letters26x30_seed0` 仍 `CANDIDATE_ONLY` / UNVERIFIED。
