# AR

论文身份状态：**CANDIDATE_FOUND**（Zenodo 第三方包被核验后拒绝）后仍为 **NOT_FOUND**。没有 **DOWNLOADED_UNVERIFIED** 的图像。不是 **SAMPLE_SET_RECONSTRUCTED**（840/120 规则未写，未编造）。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)、[docs/round2_missing_resources.md](../../docs/round2_missing_resources.md)。清单：`manifest.yaml`。

## 身份

AR Face Database，Martinez and Benavente, CVC TR 24, 1998。官方通过大学邮箱申请密码分发，禁止再分发。通常描述为 126 人、4000+ 张，不是论文的 840/120。

## Chang et al. 2015 原文 vs 推断

- **原文：** 840 张脸、120 人，像素特征。未写尺寸、未写哪 840 张。
- **推断（不升格）：** 常见做法是 120 人 × 7 张，或 100 人子集。**本仓库不发明子集。**

## 本机文件

无图像。未保存 `ARDB_Full.zip`，因此 **没有 SHA-256**。

## Zenodo 19683234 核验（使用前）

| 项 | 读到的内容 |
| --- | --- |
| 记录 | https://zenodo.org/records/19683234 ，API 同 id，2026-10-21 HEAD **200** |
| 标题 | Facial Image datasets |
| 上传者 | Manu shree（ORCID 0009-0007-8493-5282），不是 Martinez / OSU |
| 描述 | 供 2026 年文稿 “MAS Machine: Multi-kernel Attention Spatio Machine” 使用，内含 AR、Extended Yale B、CK+ |
| 声称许可 | CC-BY-4.0（上传者填写） |
| `ARDB_Full.zip` | API size 120587997；HEAD **200**，`Content-Length: 120587997`，`filename=ARDB_Full.zip`；API md5 `bb97bd9237680744c0c7268624696263`（**不是**本机 SHA-256） |

官方 AR 禁止再分发。该记录不是官方发行方，声称的 CC-BY 不能覆盖原许可。**因此不下载、不加载、不提交图像。** 没有绕过申请流程。

## 版本对照

无可用 version。`load_dataset("AR")` 抛 `DatasetUnavailable`。

## 样本选择

840/120 未指定。未构造子集。

## 预处理

未应用。

## 完整性测试（已跑）

```text
python3 -m pytest benchmarks/ar/test_ar.py -q
```

必须继续抛 `DatasetUnavailable`。

## 哪些实验用了这个版本

无。Phase 1 / repair_round1 / Round 2 都没有 AR 作业。Zenodo 包未下载。

## 复现命令（本轮实测）

```python
from benchmarks import load_dataset
from benchmarks.exceptions import DatasetUnavailable
try:
    load_dataset("AR")
except DatasetUnavailable as exc:
    assert "Zenodo" in str(exc)
```

## Task 1（2026-10-21）

仍无图像。官方页 HTTP **503**；HTTPS curl **60**；普渡 404；RVL 502。Wayback CDX 有 OSU 页捕获；GET `resources/ARdatabase_wayback_20120501.html`（19396 字节，SHA-256 `fea9bd20c825f94f9abd8862be63f7261cd533c43085149af0179d784a4344d8`）：126 人、需密码、禁止再分发、**无 840**。CVC TR 24：`resources/Martinez_Benavente_1998_CVC_TR24.pdf` 306151 字节 SHA-256 `9dfb1d979781d48f5a2de1b7c277a59dc71ffcb768da60f20e562d689418951b`。Zenodo 19683234 **未下载**。矩阵状态：官方图像 `BLOCKED_ACCESS`；840/120 `NOT_FOUND`。
