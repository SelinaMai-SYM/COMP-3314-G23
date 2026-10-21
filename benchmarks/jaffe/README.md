# JAFFE

论文身份状态：**SOURCE_VERIFIED** + **PREPROCESSING_VERIFIED**。插值未写，故不是 **PAPER_PROTOCOL_MATCHED**。聚类协议未按论文 50 次对齐复现到表格，故不是 **FULLY_REPRODUCED**。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)。清单：`manifest.yaml`。

## 身份

Japanese Female Facial Expression，Lyons, Kamachi, Gyoba, 1997。官方 Zenodo 14974867。213 张 TIFF，10 位模特。

## Chang et al. 2015 原文 vs 推断

- **原文：** 213 张，10 人，缩到 26×26，像素特征。
- **未写：** 插值；标签编码。
- **本加载器选择：** PIL 双线性；两位 poser 代码按字母序 KA…YM → 0…9。

## 本机文件（2026-10-21 重算）

| 文件 | 字节 | SHA-256 | HTTP（2026-10-21） |
| --- | --- | --- | --- |
| `data/jaffe.zip` | 12290558 | `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b` | 记录页与 `jaffe.zip?download=1` HEAD 均为 **200**，`Content-Length: 12290558`。2026-10-20 对 curl 曾是 403，本机文件未覆盖。 |

许可：仅非商业科研，**禁止再分发**（含 git）。Zenodo 另报 md5 `fe13f3302eb9968ef04367456f665436`（Round 1 已核对）。

## 版本对照

只有 `zenodo`（默认）。没有第二份“论文未发表拷贝”。

## 样本选择

zip 内全部 213 张 TIFF，按文件名排序。每人张数：KA 23, KL 22, KM 22, KR 20, MK 21, NA 21, NM 20, TM 21, UY 21, YM 22。

## 预处理

256×256 → 26×26 双线性，除以 255，C 序。190 张 mode L，23 张灰度调色板 P（R=G=B）先转 L。

## 完整性测试 / 实测命令

```text
python3 -c "from benchmarks import load_dataset; X,y,m=load_dataset('JAFFE'); assert X.shape==(213,676) and m['SHA256_checksum'].startswith('6da27f59')"
```

加载器在形状不是 `(213, 676)` 或不是 10 类时会抛错。

## 哪些实验用了这个版本

Phase 1 JAFFE 与 repair_round1 全部 6 条 COMPLETED 均为 `zenodo`。Round 2 D12（n=50）同版本：SC `20261021_161557__ROUND2__JAFFE__D12_JAFFE_SC__2983a645` ACC 68.5±11.2；E8 `20261021_161558__ROUND2__JAFFE__D12_JAFFE_E8__b643eae7` ACC 68.4±11.1；E13 `20261021_161559__ROUND2__JAFFE__D12_JAFFE_E13__50a3c90d` ACC 68.6±11.3。没有其它版本。

## Task 1（2026-10-21）哈希复核

未重下。`data/jaffe.zip` 12290558 字节 SHA-256 `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b`；加载 `(213, 676)`。矩阵状态：`COMPLETE_WITH_UNSPECIFIED_SETTINGS`。

## Strict URL Task 1（2026-10-21 晚）

未重下。SHA-256 仍为 `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b`。
