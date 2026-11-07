# Task 2：哪些已发表实验被科学地复现了？

**没有。** Chang et al. (AAAI 2015) Tables 1–2 的 72 个 method×dataset 格子，没有一格达到论文全协议复现（8 个数据集、每格 50 次随机聚类、论文未公开预处理、以及 SPLS / AR / MSRA50 / UMIST-564 / 论文 BinAlpha）。

本轮只把下列格子算作**部分科学执行**（不是论文复现）：方法为忠实重实现；数据为指定忠实版本（ORL `att92`、JAFFE Zenodo、YaleB `cropped2414`、USPS LIBSVM）；数字来自 `runs/strict_repro/` 真实 trial；γ / 维数 / 种子均**不用 ACC 选择**；SC 与 SSC 共用 `SpectralGraphConfig`。LDA-SC 为 APPROXIMATE，不计入忠实 72 格科学复现。SPLS 为 BLOCKED_METHOD。E13 单独记录，不用 ACC 替换 E8。

72 格状态：`{"BLOCKED_DATA": 32, "completed": 30, "NOT_REPRODUCED": 2, "BLOCKED_METHOD": 8}`。忠实已完成 28 格（7 方法 × 4 可加载数据集）。其中 ORL/JAFFE 为 n=50；YaleB n=10、USPS n=3 或 5，协议状态写明不是论文的 50 次。未外推。

## 部分科学执行（真实日志）

### n=50（ORL att92 与 JAFFE Zenodo）

- K-means × JAFFE: ACC 73.2 ± 5.7 (n=50); NMI 83.1 ± 3.5 (n=50); -2.4 pp vs historical paper mean; `20261021_170320__STRICT_REPRO__JAFFE__KMEANS__8776ae41`
- K-means × ORL: ACC 61.5 ± 2.9 (n=50); NMI 82.8 ± 1.2 (n=50); +1.0 pp vs historical paper mean; `20261021_170315__STRICT_REPRO__ORL__KMEANS__4b8ea2b1`
- SC × JAFFE: ACC 68.5 ± 11.2 (n=50); NMI 83.0 ± 5.7 (n=50); -7.6 pp vs historical paper mean; `20261021_170322__STRICT_REPRO__JAFFE__SC_EQ4__91b67b99`
- SC × ORL: ACC 56.2 ± 4.2 (n=50); NMI 80.5 ± 2.3 (n=50); -16.5 pp vs historical paper mean; `20261021_170316__STRICT_REPRO__ORL__SC_EQ4__19517850`
- PCA-KM × JAFFE: ACC 74.8 ± 7.7 (n=50); NMI 83.1 ± 4.5 (n=50); -1.0 pp vs historical paper mean; `20261021_171014__STRICT_REPRO__JAFFE__PCAKM_D10__0e3cf840`
- PCA-KM × ORL: ACC 63.1 ± 3.3 (n=50); NMI 83.6 ± 1.2 (n=50); -1.4 pp vs historical paper mean; `20261021_170921__STRICT_REPRO__ORL__PCAKM_D40__b91fcfbc`
- PCA-SC × JAFFE: ACC 59.3 ± 7.7 (n=50); NMI 72.2 ± 4.7 (n=50); -17.6 pp vs historical paper mean; `20261021_171016__STRICT_REPRO__JAFFE__PCASC_D10__09a8767f`
- PCA-SC × ORL: ACC 55.4 ± 4.3 (n=50); NMI 80.6 ± 2.2 (n=50); -12.4 pp vs historical paper mean; `20261021_170924__STRICT_REPRO__ORL__PCASC_D40__fe3572e1`
- LDA-KM × JAFFE: ACC 64.4 ± 9.2 (n=50); NMI 78.6 ± 5.1 (n=50); -12.1 pp vs historical paper mean; `20261021_171017__STRICT_REPRO__JAFFE__LDAKM_D9__0e99bdae`
- LDA-KM × ORL: ACC 56.3 ± 4.1 (n=50); NMI 81.0 ± 1.7 (n=50); -9.3 pp vs historical paper mean; `20261021_170927__STRICT_REPRO__ORL__LDAKM_D39__94edb79b`
- LLC × JAFFE: ACC 88.4 ± 6.9 (n=50); NMI 91.2 ± 2.7 (n=50); +9.8 pp vs historical paper mean; `20261021_171027__STRICT_REPRO__JAFFE__LLC__aef43932`
- LLC × ORL: ACC 77.9 ± 2.0 (n=50); NMI 88.6 ± 0.8 (n=50); +6.4 pp vs historical paper mean; `20261021_171013__STRICT_REPRO__ORL__LLC__127454d2`
- SSC E8 × JAFFE: ACC 68.4 ± 11.1 (n=50); NMI 83.0 ± 5.7 (n=50); -12.8 pp vs historical paper mean; `20261021_170323__STRICT_REPRO__JAFFE__SSC_E8_G1__2d4a870b`
- SSC E8 × ORL: ACC 57.3 ± 3.8 (n=50); NMI 81.1 ± 2.2 (n=50); -18.7 pp vs historical paper mean; `20261021_170317__STRICT_REPRO__ORL__SSC_E8_G1__68341141`

### 预算受限（YaleB n=10，USPS n=3 或 5）

- K-means × YaleB: ACC 9.1 ± 0.5 (n=10); NMI 12.4 ± 0.7 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_170325__STRICT_REPRO__YALEB__KMEANS__ab478656`
- K-means × USPS: ACC 66.4 ± 0.5 (n=5); NMI 60.9 ± 0.3 (n=5); budget_limited_n=5_paper_protocol_is_50; `20261021_170410__STRICT_REPRO__USPS__KMEANS__efa8d62b`
- SC × YaleB: ACC 18.1 ± 1.3 (n=10); NMI 26.6 ± 0.6 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_170327__STRICT_REPRO__YALEB__SC_EQ4__f8323013`
- SC × USPS: ACC 63.9 ± 1.7 (n=5); NMI 76.1 ± 3.6 (n=5); budget_limited_n=5_paper_protocol_is_50; `20261021_170412__STRICT_REPRO__USPS__SC_EQ4__19529e79`
- PCA-KM × YaleB: ACC 9.0 ± 0.5 (n=10); NMI 12.2 ± 0.5 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171028__STRICT_REPRO__YALEB__PCAKM_D38__31f464c2`
- PCA-KM × USPS: ACC 65.7 ± 1.8 (n=3); NMI 59.8 ± 0.4 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171120__STRICT_REPRO__USPS__PCAKM_D10__31bc23ed`
- PCA-SC × YaleB: ACC 16.2 ± 0.6 (n=10); NMI 23.3 ± 1.0 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171032__STRICT_REPRO__YALEB__PCASC_D38__2debde8e`
- PCA-SC × USPS: ACC 56.9 ± 2.1 (n=3); NMI 65.0 ± 1.2 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171122__STRICT_REPRO__USPS__PCASC_D10__ef12dd83`
- LDA-KM × YaleB: ACC 9.6 ± 0.8 (n=10); NMI 13.5 ± 1.3 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171037__STRICT_REPRO__YALEB__LDAKM_D37__ab5c8123`
- LDA-KM × USPS: ACC 52.9 ± 2.1 (n=3); NMI 57.4 ± 4.8 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171127__STRICT_REPRO__USPS__LDAKM_D9__4e9e3c66`
- LLC × YaleB: ACC 25.7 ± 1.1 (n=10); NMI 32.9 ± 0.7 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_171117__STRICT_REPRO__YALEB__LLC__3fe07e59`
- LLC × USPS: ACC 58.3 ± 2.7 (n=3); NMI 66.2 ± 2.5 (n=3); budget_limited_n=3_paper_protocol_is_50; `20261021_171131__STRICT_REPRO__USPS__LLC__f27a8b6a`
- SSC E8 × YaleB: ACC 17.4 ± 1.1 (n=10); NMI 26.0 ± 1.1 (n=10); budget_limited_n=10_paper_protocol_is_50; `20261021_170328__STRICT_REPRO__YALEB__SSC_E8_G1__333d3583`
- SSC E8 × USPS: ACC 62.1 ± 3.8 (n=5); NMI 75.4 ± 3.0 (n=5); budget_limited_n=5_paper_protocol_is_50; `20261021_170415__STRICT_REPRO__USPS__SSC_E8_G1__e36daae7`

## 仍然不是论文复现的原因

- 论文协议是每个数据集 50 次随机聚类。YaleB 实际 n=10，USPS 实际 n≤5。INCOMPLETE 只写实际 n，绝不补成 50。
- ORL `att92` 是 AT&T 92×112 原包缩到 32×32（双线性插值是假设），不是 Olivetti，也未宣称 PAPER_PROTOCOL_MATCHED。
- JAFFE 是已核实 Zenodo zip，不是论文未公开预处理副本。
- YaleB `cropped2414` 计数 2414 与论文一致，不声称与邓蔡 `YaleB_32x32.mat` 逐像素同一。
- PCA 维数步长 `{10,20,…,150}` 是假设。矩阵格用预指定维数 min(50,K,n−1,d)，**不用网格上的最高 ACC**。
- LDA 秩 ≤ K−1（Ding–Li），网格到不了 150。
- SSC γ 网格 `{1e-6,1e-3,1,1e3,1e6}` 已记录。矩阵格用预指定 γ=1。不按 ACC 选 γ，也不把原始式 (8) 目标跨 γ 互比。未收敛 IRLS 保持未收敛。
- 历史 Track A / Round 2 数字没有抄进本矩阵。
- LDA-SC（ORL/JAFFE n=10）已跑，标 APPROXIMATE，不计入忠实复现。YaleB/USPS 的 LDA-SC 为 NOT_REPRODUCED（可选近似格，未跑）。

## 阻塞

- SPLS: Section 3 not obtained; `baselines/spls/spls.py` raises NotImplementedError; no substitute shrinking.
- AR: official host unavailable; unofficial Zenodo dump not used; 840/120 subset not invented.
- MSRA50: no 1799×12×1024 archive; other MSRA corpora not renamed.
- UMIST 564: not obtained. precropped575 (n=575, 565 unique pixels) is extra, labeled not-564.
- Paper BinAlpha 26×30: not identified. letters26x30_seed0 is UNVERIFIED reconstruction only.
- Shared F mismatch: max_abs_diff=0.0.

## Shared F

同一 `SpectralGraphConfig` 下 SC 的 F 必须等于 SSC 的 F。ORL att92 及其余忠实数据集的 `embedding_F.npy` 比较见下。

```json
{
  "note": "SC F must equal SSC F under the same SpectralGraphConfig. Compared from saved embedding_F.npy.",
  "pairs": {
    "ORL:att92": {
      "sc_run": "20261021_170316__STRICT_REPRO__ORL__SC_EQ4__19517850",
      "e8_run": "20261021_170317__STRICT_REPRO__ORL__SSC_E8_G1__68341141",
      "status": "compared",
      "equal_exact": true,
      "equal_atol_1e-12": true,
      "max_abs_diff": 0.0,
      "shape": [
        400,
        40
      ]
    },
    "JAFFE:zenodo": {
      "sc_run": "20261021_170322__STRICT_REPRO__JAFFE__SC_EQ4__91b67b99",
      "e8_run": "20261021_170323__STRICT_REPRO__JAFFE__SSC_E8_G1__2d4a870b",
      "status": "compared",
      "equal_exact": true,
      "equal_atol_1e-12": true,
      "max_abs_diff": 0.0,
      "shape": [
        213,
        10
      ]
    },
    "YaleB:cropped2414": {
      "sc_run": "20261021_170327__STRICT_REPRO__YALEB__SC_EQ4__f8323013",
      "e8_run": "20261021_170328__STRICT_REPRO__YALEB__SSC_E8_G1__333d3583",
      "status": "compared",
      "equal_exact": false,
      "equal_atol_1e-12": true,
      "max_abs_diff": 1.3292839051715077e-13,
      "shape": [
        2414,
        38
      ]
    },
    "USPS:libsvm": {
      "sc_run": "20261021_170412__STRICT_REPRO__USPS__SC_EQ4__19529e79",
      "e8_run": "20261021_170415__STRICT_REPRO__USPS__SSC_E8_G1__e36daae7",
      "status": "compared",
      "equal_exact": false,
      "equal_atol_1e-12": true,
      "max_abs_diff": 4.5102810375396984e-15,
      "shape": [
        9298,
        10
      ]
    }
  },
  "sc_run": "20261021_170316__STRICT_REPRO__ORL__SC_EQ4__19517850",
  "e8_run": "20261021_170317__STRICT_REPRO__ORL__SSC_E8_G1__68341141",
  "status": "compared",
  "equal_exact": true,
  "equal_atol_1e-12": true,
  "max_abs_diff": 0.0,
  "shape": [
    400,
    40
  ],
  "all_equal_atol_1e-12": true
}
```

产物：`results/reproduction_full_matrix.csv`、`results/reproduction_full_matrix.md`、`results/strict_repro/`、`runs/strict_repro/`。
未 git commit / push。

