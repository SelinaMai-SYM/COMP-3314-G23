# YaleB

论文身份状态（`cropped2414`）：**SOURCE_VERIFIED**（Wayback 官方 zip）+ 计数匹配 2414/38。插值未写，故不是 **PAPER_PROTOCOL_MATCHED**。不是 **FULLY_REPRODUCED**。

默认 `load_dataset("YaleB")` 仍是邓蔡 `YaleB_32x32.mat`：**SOURCE_VERIFIED** 作为邓蔡矩阵，**不声称**与 cropped 或论文逐像素同一。

索引：[docs/round2_source_of_truth.md](../../docs/round2_source_of_truth.md)。清单：`manifest.yaml`、`manifest_cropped.yaml`。

## 身份

Extended Yale Face Database B（Georghiades et al., TPAMI 2001；裁剪 Lee et al., TPAMI 2005）。邓蔡页写明 32×32 来自 UCSD 裁剪图再缩小。

## Chang et al. 2015 原文 vs 推断

- **原文：** 2414 张近正面、38 人、缩到 32×32。
- **未写：** 是否去 Ambient；插值；是否用邓蔡 mat。
- **本仓库：** 默认保留邓蔡 mat；Round 2 主重建应用 `cropped2414`（去 Ambient、32×32）。

## 本机文件（2026-10-21 重算，未覆盖）

| 文件 | 字节 | SHA-256 | HTTP（2026-10-21） |
| --- | --- | --- | --- |
| `data/YaleB_32x32.mat` | 2214688 | `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99` | 邓蔡 `YaleB_32x32.mat` HEAD **200**，`Content-Length: 2214688` |
| `data/cropped_wayback/CroppedYale_wayback_20220127.zip` | 58493820 | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` | 现网 UCSD zip **404**；Wayback `20220127084451id_` HEAD **200** |
| bilinear / nearest / bicubic `*_uint8.npy` | 各 2472064 | 见 `manifest_cropped.yaml` | 本地处理 |

许可：研究使用；引用 Georghiades 2001，裁剪实验另引 Lee 2005。耶鲁限制把图像并进另一公开再分发库。zip gitignore。

## 版本对照

| version | n | 说明 |
| --- | --- | --- |
| 默认 / `dengcai32` | 2414 | 已是 32×32；缩放核未知 |
| `cropped2414` | 2414 | 2452 PGM 去 38 张 Ambient；非环境光全是 `(192, 168)` |
| nearest / bicubic | 2414 | 插值歧义 |

每类张数直方图与邓蔡 `gnd` 相同。**未做逐像素对齐。**

## 样本选择

cropped：非 Ambient PGM，按受试者号再文件名。无 yaleB14。18 个 `.pgm.bad` 不计。

## 预处理

cropped：去 Ambient → 32×32（默认双线性）→ /255 → C 序。邓蔡：不再缩放，只 /255。

## 完整性测试（已跑）

```text
python3 -m pytest benchmarks/yaleb/test_yaleb_versions.py -q
```

## 哪些实验用了哪个版本

- Phase 1 与 repair_round1 多数 YaleB：`dengcai32`（6 COMPLETED，另有 FAILED 记录保留）。
- repair_round1 D01：`cropped2414` 1 条 COMPLETED、1 条 FAILED。
- Round 2（n=10，不是 50）：`dengcai32` SC `20261021_161602__ROUND2__YALEB__D01_DENGCAI32_SC__6411988e` ACC 20.1±1.2；E8 `20261021_161603__ROUND2__YALEB__D08_DENGCAI32_E8__27f746d1` ACC 19.5±1.5。`cropped2414` SC `20261021_161625__ROUND2__YALEB__D01_CROPPED2414_SC__d1a360fb` ACC 18.1±1.3；E8 `20261021_161626__ROUND2__YALEB__D08_CROPPED2414_E8__5fb5af8b` ACC 17.4±1.1。cropped 没有提升。

## Task 1（2026-10-21）哈希复核

未重下。`data/YaleB_32x32.mat` 2214688 字节 SHA-256 `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99`。`data/cropped_wayback/CroppedYale_wayback_20220127.zip` 58493820 字节 SHA-256 `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573`（2452 PGM，2414 非 Ambient）。处理阵列哈希见 `manifest_cropped.yaml`。`cropped2414` 矩阵状态：`COMPLETE_WITH_UNSPECIFIED_SETTINGS`。
