# UMIST

论文 564 张身份：**CANDIDATE_FOUND**（2001 页写 564）但档案不是 564，故 **SAMPLE_SET** 未匹配。575/1012 档案是 **SOURCE_VERIFIED** 作为 Wayback/Figshare 文件，不是论文集。不是 **FULLY_REPRODUCED**。

默认 `load_dataset("UMIST")` 仍抛 `DatasetUnavailable`。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)。清单：`manifest.yaml`、`manifest_wayback.yaml`、`manifest_figshare_cropped.yaml`。

## 身份

Sheffield / UMIST 人脸（Graham and Allinson, 1998）。2001-04-05 Wayback 页写 564 张、20 人、约 220×220，并链 `face.tar.gz`≈29Mb 与 `cropped.tar.gz`≈4.5Mb。

## Chang et al. 2015 原文 vs 推断

- **原文：** 564 张、20 人，像素特征。未写缩放。
- **未写：** 如何从更大集合得到 564。
- **禁止：** 随便删 11 张凑 564。

## 本机文件（2026-10-21 重算，未覆盖）

| 文件 | 字节 | SHA-256 |
| --- | --- | --- |
| `data/wayback_sheffield/face_wayback_20050403.tar.gz` | 29385054 | `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` |
| `data/wayback_sheffield/cropped_wayback_20070805.tar.gz` | 4506480 | `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` |
| `data/figshare_umist_cropped/umist_cropped.mat` | 5927440 | `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` |

2026-10-21 HTTP：Lincoln `face.tar.gz` **202**（WAF）；`images.ee.umist.ac.uk` **502**；Sheffield 页 **404**。未重下已有档案。

许可：2001 页称仅受试者 1a 可在书面许可下发表。Figshare API：CC BY 4.0（该 mat，不是 Graham 发行）。

## 版本对照

| version | n | 说明 |
| --- | --- | --- |
| 默认 / `sheffield564` | — | `DatasetUnavailable` |
| `precropped575` | 575 | 全部 `(112, 92)`，像素 0..238 |
| `figshare575` | 575 | 每类张数与 cropped tar 相同，像素哈希交集为 0（转置后仍 0） |
| `uncropped1012` | — | 122 种形状，不能编成 `(n, d)` |

## 样本选择 / 重复检查（2026-10-21 实测）

cropped tar：

- PGM 成员 575，**文件名无重复**，basename 也无重复。
- 像素哈希 565 个互异。10 组完全相同像素，全部在 `1b/face/`：

`1b014.pgm=final00.pgm`，`1b016=final01`，`1b024=final02`，`1b032=final03`，`1b038=final04`，`1b040=final05`，`1b048=final06`，`1b056=final07`，`1b064=final08`，`1b072=final09`。

去掉这 10 张 `final*.pgm` 得到 **565，不是 564**。再删 1 张会是任意选择。因此 **没有证据充分的 564 子集**，也不另做“凑 564”的 reconstruction 版本。

未裁剪 tar：1013 个 PGM 成员，1012 个不重复名（`1t/1t052.pgm` 存了两次）。

## 预处理

`precropped575`：全部 575 张 /255，不缩放。含 10 张像素副本。

## 完整性测试（已跑）

```text
python3 -m pytest benchmarks/umist/test_umist.py -q
```

默认必须不可用；`precropped575` 必须是 `(575, 10304)` 且 `not_exact_564`。

## 哪些实验用了这个版本

无论文 564 作业。Phase 1 / repair_round1 / Round 2 都没有 UMIST 聚类。565≠564，未删图凑数。

## 复现命令（本轮实测）

```python
from benchmarks import load_dataset
from benchmarks.exceptions import DatasetUnavailable
X, y, m = load_dataset("UMIST", version="precropped575")
assert m["n"] == 575 and m["unique_pixel_arrays"] == 565
```

## Task 1（2026-10-21）哈希复核

未重下三份档案（SHA 与上表相同）。新保存 2001 页：`resources/database_wayback_20010405.html` 3878 字节 SHA-256 `a8a91fbea393f524e3275acad9356512145547217c18f446eb08eae849cb263a`（GET Wayback `id_` **200**）。该页写 564 张并链 4.5Mb `cropped.tar.gz`；本机对应 tar 是 **575** PGM。现网 UMIST 502、Sheffield 404、Lincoln 202。矩阵状态：论文 564 为 `CANDIDATE_ONLY`。未删图。

## Strict URL Task 1（2026-10-21 晚）哈希复核

未重下两条 Wayback tar（SHA 仍为 `df58ad9a…c8fb` / `c1f7f6ea…dff4`）。Roweis `https://cs.nyu.edu/home/people/in_memoriam/roweis/data/umist_cropped.mat` GET **200**，5927440 字节，SHA-256 `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361`，与本地 Figshare 副本 **逐字节相同**。本轮重算：575 文件名；565 互异字节 **等于** 565 互异像素；去掉 10 张 `final*.pgm` 仍是 **565≠564**。未删 11 张。论文 564 仍未取得。
