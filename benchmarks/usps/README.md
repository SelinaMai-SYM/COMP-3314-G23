# USPS

论文身份状态：**SOURCE_VERIFIED**。发布已是 16×16，加载器不再缩放。论文写“resize to 16×16”，因此预处理与论文字面不完全同一，标 **PREPROCESSING_VERIFIED**（对这份标准发布），不是 **PAPER_PROTOCOL_MATCHED**。SSC 只有 n=3 pilot，不是 **FULLY_REPRODUCED**。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)。清单：`manifest.yaml`。

## 身份

LIBSVM 多类页上的 `usps.bz2` + `usps.t.bz2`（Hull, TPAMI 1994；16×16 形式见 Hastie et al. zip.info）。

## Chang et al. 2015 原文 vs 推断

- **原文：** 9298 张灰度手写数字，缩到 16×16。
- **未写：** 哪一份 USPS；是否已是 16×16。
- **本加载器：** 标准 LIBSVM 7291+2007，已是 256 维，`[-1, 1]`，不再缩放。

## 本机文件（2026-10-21 重算）

| 文件 | 字节 | SHA-256 | HTTP（2026-10-21） |
| --- | --- | --- | --- |
| `data/usps.bz2` | 6579383 | `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` | HEAD **200**，`Content-Length: 6579383`，`application/x-bzip2` |
| `data/usps.t.bz2` | 1831726 | `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` | HEAD **200**（与清单一致，未覆盖） |

许可：压缩包内无许可证。LIBSVM 公开研究发布。精确条款：unknown。

## 版本对照

只有 `libsvm`（默认）。没有第二份“论文自己缩放过的”USPS。

## 样本选择

全部 7291 训练行 + 2007 测试行。标签 1..10 → 数字 0..9。类别计数与 Hastie zip.info 表一致。

## 预处理

解析 LIBSVM；特征 1..256；不再缩放。

## 完整性 / 实测命令

```python
from benchmarks import load_dataset
X, y, m = load_dataset("USPS")
assert X.shape == (9298, 256)
assert m["SHA256_checksum"]["usps.bz2"].startswith("3771e9dd")
```

## 哪些实验用了这个版本

Phase 1 USPS 与 repair_round1 均为 `libsvm`。Round 2 pilot n=3（不是 50）：SC `20261021_161647__ROUND2__USPS__D12_USPS_SC__6324d037` ACC 63.8±1.7；E8 `20261021_161650__ROUND2__USPS__D08_USPS_E8__c638f49b` ACC 60.7±4.0。
