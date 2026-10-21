# ORL

论文身份状态：**PREPROCESSING_VERIFIED**（对 `att92` 的 400/40 与 32×32 缩放）。不是 **PAPER_PROTOCOL_MATCHED**（插值未写）。不是 **FULLY_REPRODUCED**。

默认 `load_dataset("ORL")` 仍是 Olivetti 64×64→32×32，状态 **SOURCE_VERIFIED**（对 figshare/sklearn 矩阵），但**不是**论文常见的 92×112 原图。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)、[docs/round2_missing_resources.md](../../docs/round2_missing_resources.md)。清单：`manifest.yaml`、`manifest_att92.yaml`。

## 身份

AT&T / ORL 人脸库（Samaria and Harter, 1994）。剑桥托管的 `att_faces.zip` 是 92×112 PGM，400 张、40 人、每人 10 张。scikit-learn / figshare 的 `olivettifaces.mat` 是另一份 64×64 矩阵，校验和与 sklearn 1.8.0 一致。

## Chang et al. 2015 原文 vs 推断

- **原文：** 40 人、每人 10 张，缩到 32×32，像素特征。
- **未写：** 92×112 还是 64×64；插值；是否先裁剪。
- **推断（不升格为原文）：** 文献里 ORL 通常是 92×112。Round 2 标 original-source 的实验应显式 `version="att92"`。

## 本机文件（2026-10-21 重算 SHA-256，未覆盖）

| 文件 | 字节 | SHA-256 | HTTP（2026-10-21） |
| --- | --- | --- | --- |
| `data/olivettifaces.mat` | 4260520 | `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794` | 源 `https://ndownloader.figshare.com/files/5976027` HEAD **403**（文件是 2026-10-20 已取得，未重下） |
| `data/att92/att_faces.zip` | 3769022 | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` | `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip` HEAD **200** |
| `orl_att92_32x32_nearest_uint8.npy` | 409728 | `d056a67cd3850f3c5cdf726c35247d0db11f41d45bfd11f4a5ee4da26f0fe2ea` | 本地处理 |
| `orl_att92_32x32_bilinear_uint8.npy` | 409728 | `db8ed7a2db8b65aba8d34c9387420c014834d39cef5d27f6b994181de87a5f7d` | 本地处理 |
| `orl_att92_32x32_bicubic_uint8.npy` | 409728 | `2e70df62a253d4f42b45dbb16b44ec0de1c832f5a1775fb398a77cbf4f058683` | 本地处理 |
| `orl_att92_native_uint8.npy` | 4121728 | `c8559063d2dde31cdd1746f2038431d995013c96eaff31ef1aaa37f8053066fa` | 本地处理 |

许可：zip README 要求注明 Olivetti Research Laboratory；剑桥页要求注明 AT&T Laboratories Cambridge。图像 gitignore。

## 版本对照

| version | 内容 | 与论文 |
| --- | --- | --- |
| 默认 / `olivetti` | 64×64→32×32 双线性 | 计数 400/40 相符；空间来源不同 |
| `att92` / `att92_bilinear` | 92×112 PGM，双线性 32×32 | original-source 候选 |
| `att92_nearest` / `att92_bicubic` | 同 zip，另两种插值 | 插值歧义，不升格 |

## 样本选择

全部 400 张。没有未知子集。标签：Olivetti 为列号 `// 10`；att92 为 `s1..s40` 减 1。

## 预处理

att92：PGM 宽 92、高 112，数组 `(400, 112, 92)`，不转置，除以 255，C 序拉直。原生像素 0..251。Olivetti：sklearn 轴序，再双线性 32×32。

## 完整性测试（已跑）

```text
python3 -m pytest benchmarks/orl/test_orl_versions.py -q
```

默认必须仍是 Olivetti；`att92` 必须是 `(400, 1024)` 且与 nearest/bicubic 像素不同。

## 哪些实验用了哪个版本

- Phase 1 Track A/B 与绝大多数 repair_round1 ORL：**默认 Olivetti**（registry 中 `olivetti` 27 条）。
- repair_round1 D01 数据源：`att92`、`att92_nearest`、`att92_bicubic`（各至少 1 条 COMPLETED）。
- Round 2 忠实短名单用 `att92`：SC `20261021_161537__ROUND2__ORL__D01_ATT92_SC__4fe80e2e` ACC 56.2±4.2（n=50）；E8 `20261021_161553__ROUND2__ORL__D08_E8_ATT92__d3809fd0` ACC 57.3±3.8。Olivetti 对照 SC `20261021_161536__ROUND2__ORL__D01_OLIVETTI_SC__9118018b` ACC 53.9±3.0。

## 复现命令（本轮实测）

```python
from benchmarks import load_dataset
X, y, m = load_dataset("ORL")
assert m["version"] == "olivetti64" and X.shape == (400, 1024)
X2, y2, m2 = load_dataset("ORL", version="att92")
assert m2["original_spatial_size"] == [112, 92]
```

## Task 1（2026-10-21）哈希复核

未重下。`data/att92/att_faces.zip` 3769022 字节 SHA-256 `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec`（400 PGM）。`data/olivettifaces.mat` 4260520 字节 SHA-256 `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794`。处理阵列在 `data/att92/processed/`，哈希与上表相同。矩阵状态：`att92` 为 `COMPLETE_WITH_UNSPECIFIED_SETTINGS`（插值未写）。

## Strict URL Task 1（2026-10-21 晚）

未重下。`att_faces.zip` SHA-256 仍为 `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec`。
