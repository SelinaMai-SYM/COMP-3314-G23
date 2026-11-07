# Strict URL 资源获取（Task 1）

日期：2026-10-21。工作区：`v1/`。起点 `git rev-parse HEAD` = `47c0f835ef69afa560b891524da894ab4b39bad2`。User-Agent：`COMP3314-SSC-strict-url-repro/1.0`。HTTP 记录：[strict_http_logs/task1_strict_url.json](strict_http_logs/task1_strict_url.json)、[strict_http_logs/task1_requests.log](strict_http_logs/task1_requests.log)。

本轮 **只使用计划** [`strict_url_repro_c525e30e.plan.md`](/Users/grantwright/.cursor/plans/strict_url_repro_c525e30e.plan.md) **给出的 URL**，以及授权页上的精确文件链接。未发明主机。未改 `method_extension/`。未重写 `report/`。未 git commit / push。未跑 72 格聚类。受限图像 gitignore，未自动提交。

字段：路径、大小、SHA256、MD5、样本数、许可、状态。

## 总表

| 资源 | 路径 | 大小 | SHA-256 | MD5 | 样本数 | 许可 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AR 第三方 zip | `benchmarks/ar/data/ARDB_Full.zip` | 120587997 | `32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438` | `bb97bd9237680744c0c7268624696263`（与 Zenodo 公布值一致） | 100 身份；2599 张 `1..26.bmp`；另 1 张 `s7/22 - Copy.bmp` | 上传者声称 CC-BY-4.0；**不是**官方 Martinez 许可 | `SOURCE_RECOVERED_SUBSET_UNVERIFIED` |
| UMIST cropped tar | `benchmarks/umist/data/wayback_sheffield/cropped_wayback_20070805.tar.gz` | 4506480 | `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` | `da0ae0037ef9d6f3d58deaac6c4cb412` | 575 PGM / 565 互异字节=像素 | 2001 页限制发表 | 575 已核验；**不是**论文 564 |
| UMIST uncropped tar | `benchmarks/umist/data/wayback_sheffield/face_wayback_20050403.tar.gz` | 29385054 | `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` | `11011ab5dded043f5e4331711c2407c8` | 1013 成员 / 1012 不重复名 | 同上 | 不是 564 |
| UMIST Roweis mat | `benchmarks/umist/data/roweis_umist_cropped/umist_cropped.mat`（与 Figshare 副本逐字节相同） | 5927440 | `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` | `62bbcdd946c62a2b112d0062aa279caa` | 575 | Figshare 报 CC BY 4.0（该 mat，不是 Graham 发行） | 575；**不是** 564 |
| BinAlpha 父集 | `benchmarks/binalpha/data/binaryalphadigs.mat` | 532304 | `3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7` | `194c4c91d95f1457bbd5829e75373b96` | 36×39=1404 | mat 内无许可证 | 父集已核验；不是论文 BinAlpha |
| BinAlpha 候选 | 索引 `benchmarks/binalpha/reconstructions/letters26x30_seed0.json`；指针 `.../CANDIDATE_BIN_ALPHA.json` | （派生） | 父集同上 | 父集同上 | 780×320，seed **0** | 同上 | `CANDIDATE_BIN_ALPHA`；默认加载器 **不** 称 EXACT |
| JAFFE | `benchmarks/jaffe/data/jaffe.zip` | 12290558 | `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b` | `fe13f3302eb9968ef04367456f665436` | 213 TIFF | 非商业、禁再分发 | SHA 匹配，未重下 |
| ORL att92 | `benchmarks/orl/data/att92/att_faces.zip` | 3769022 | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` | `ea6281c63bb2e68a64c046957a749086` | 400 PGM / 40 人 | AT&T / 剑桥科研使用 | SHA 匹配，未重下 |
| YaleB cropped | `benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` | 58493820 | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` | `4447b8e69c0c2f7479f67f2481efe13f` | 2452 PGM / 2414 非 Ambient | 研究使用；限制再分发 | SHA 匹配，未重下 |
| USPS | `benchmarks/usps/data/usps.bz2` + `usps.t.bz2` | 6579383 + 1831726 | `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` / `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` | `ec16c51db3855ca6c91edd34d0e9b197` / `8ea070ee2aca1ac39742fdd1ef5ed118` | 9298 | 压缩包内无许可证 | SHA 匹配，未重下 |
| MSRA50 图像 | （无文件） | — | — | — | — | — | `BLOCKED_DATA_NOT_OBTAINED` |
| SPLS 第 3 节 | （无 PDF） | — | — | — | — | Elsevier 闭源 | `BLOCKED_MISSING_FULL_METHOD` |

没有数据集被标成论文协议 EXACT。

## AR（第三方 Zenodo，不是官方 Martinez）

**下载：是。** 授权页 https://zenodo.org/records/19683234 。文件 URL 取自该记录 API，未另造主机：`https://zenodo.org/api/records/19683234/files/ARDB_Full.zip/content`。

| 项 | 值 |
| --- | --- |
| HTTP GET | **200**；`Content-Type: application/octet-stream`；`filename=ARDB_Full.zip` |
| 是否 HTML | **否**。文件头 `PK\x03\x04` |
| 大小 | 120587997（约 120.6 MB，与 API / HEAD 一致） |
| 公布 MD5 | `bb97bd9237680744c0c7268624696263` |
| 本机 MD5 | `bb97bd9237680744c0c7268624696263` → **匹配** |
| 本机 SHA-256 | `32e69e8801313256b103942309e10badbd283183a44494d843e6866d22d4d438` |
| 上传者 | Manu shree（ORCID `0009-0007-8493-5282`），文稿 “MAS Machine…”。**不是** Aleix Martinez / OSU |
| 声称许可 | CC-BY-4.0（上传者填写）。官方 AR 条款禁止再分发。本仓库 **不把该 zip 叫作官方 AR** |

### 身份与命名（对照官方 `M-xx-yy.raw` / `F-xx-yy.raw`）

官方 2012 页：男 `M-xx-yy.raw`，女 `F-xx-yy.raw`；126 人（70 男 56 女）；`yy` 1–26 为表情/光照/遮挡；图像 768×576 RAW。

本 zip：

- 顶层 `ARDB_Full/s1` … `s100`（**100** 个身份，连续 1–100）。
- 有效 BMP：**2600** 张 magic `BM`，全部 **120×165**、24 bit。
- 文件名是 `1.bmp`…`26.bmp`，**零条** 匹配官方 `M-`/`F-` RAW 模式。
- `s7` 缺 `26.bmp`，多 `22 - Copy.bmp`。另有 `__MACOSX` AppleDouble 与 `.DS_Store`。
- zip 内 **无** README / PDF / 840 / 120 规则。

**身份数：100。** 不是论文的 120。不是官方 126。

### 840/120 子集

论文（本地 UTS 署名 AAAI PDF）只写 “840 faces of 120 different people”，未写哪 840 张。归档文档不存在，因此 **没有可辩护的每人 7 张规则**。未构造 840 子集。

状态：**`SOURCE_RECOVERED_SUBSET_UNVERIFIED`**（Zenodo 工件 MD5 真，官方身份/命名/840 规则未核实）。默认 `load_dataset("AR")` 仍 `DatasetUnavailable`，不称 EXACT。原始 zip gitignore，未提交。

## UMIST（先核本地；564 未取得）

本地两份 Wayback tar 与 `umist_cropped.mat` **均在**，SHA 与 README 一致，**未重下 tar**。

计划中的两条 Wayback tar（仅作已核验本地档案的出处，本轮未再 GET）：

- `https://web.archive.org/web/20050403232828id_/http://images.ee.umist.ac.uk/danny/face.tar.gz`
- `https://web.archive.org/web/20070805190146id_/http://images.ee.umist.ac.uk/danny/cropped.tar.gz`

Roweis 页 https://cs.nyu.edu/home/people/in_memoriam/roweis/data.html GET **200**。页上 href `data/umist_cropped.mat` 解析为：

`https://cs.nyu.edu/home/people/in_memoriam/roweis/data/umist_cropped.mat`

对该 URL GET **200**、5927440 字节。与本地 Figshare `umist_cropped.mat` **逐字节相同**（同一 SHA-256 / MD5）。

### 575 vs 564；重复字节 vs 像素

裁剪 tar 本轮重算：

| 量 | 值 |
| --- | --- |
| PGM 成员 / 唯一文件名 | 575 / 575 |
| 唯一字节数组 | 565 |
| 唯一像素数组 | 565 |
| 字节重复组 = 像素重复组 | 是（10 组，均在 `1b/face`：`1b014.pgm=final00.pgm` … `1b072.pgm=final09.pgm`） |

去掉 10 张像素/字节副本得到 **565，不是 564**。从 575 个文件名到 564 还要再删 11 张；从 565 个互异像素还要再删 1 张。**没有证据，未删。** 未裁剪 tar：1012 不重复名（`1t/1t052.pgm` 存两次，字节相同）。

**UMIST 564 状态：未取得。** 575 与论文 564 分开。默认 `load_dataset("UMIST")` 仍不可用。

## BinAlpha（候选，不是历史同一）

本地 `binaryalphadigs.mat` 存在且 SHA 匹配，**未重下**。计划 URL HEAD **200**、532304 字节：

`https://cs.nyu.edu/home/people/in_memoriam/roweis/data/binaryalphadigs.mat`

规则（已保存索引，固定种子 **0**）：丢掉 `0`–`9`；对 `A`–`Z` 用 `numpy.random.RandomState(0).choice(39, size=30, replace=False)` 再排序。形状 **780×320**。

| 项 | 值 |
| --- | --- |
| 候选路径 | `version="CANDIDATE_BIN_ALPHA"` |
| 索引 | `benchmarks/binalpha/reconstructions/letters26x30_seed0.json` |
| 指针 | `benchmarks/binalpha/reconstructions/CANDIDATE_BIN_ALPHA.json` |
| 种子 | **0**（仓库重建种子，不是 Chang 的种子） |
| 身份标签 | `CANDIDATE_BIN_ALPHA`（不是历史逐样本同一） |

默认 `load_dataset("BinAlpha")` 仍抛 `DatasetUnavailable`，**不**声称 EXACT。

## MSRA50

计划 **无下载 URL**。只查了本地与 UTS 文献 PDF：

- 本地 `benchmarks/msra50/data/`：**无** 1799×12×1024 文件。
- 本地 UTS 署名 AAAI 2015 PDF `SSC_method/resources/Chang_et_al_2015_SSC_AAAI.pdf`（Xiaojun Chang，University of Technology Sydney）：“The MSRA50 dataset contains 1799 images from 12 different classes.” 无 URL、无矩阵文件。
- 本地同组 OA `benchmarks/msra50/resources/Chang_Nie_Yang_Huang_2014_arxiv_1411.6241v1.pdf`：表列 MSRA50 **1024 × 1799 × 12**，正文引 He et al. 2004。仍不是数据文件。

未用其它 MSRA 集合。状态：**`BLOCKED_DATA_NOT_OBTAINED`**。

## JAFFE / ORL att92 / YaleB cropped / USPS

本轮 **只复核 SHA-256，未重下**。全部与既有 README 一致（见总表）。实验须写 dataset version + checksum。

## SPLS

本地 `baselines/spls/resources/`：**无 PDF**。ScienceDirect：

- DOI `https://doi.org/10.1016/j.ipm.2013.01.004` → linkinghub HTML 2671 字节，不是第 3 节。
- `https://www.sciencedirect.com/science/article/abs/pii/S0306457313000095` HEAD **403**，`cf-mitigated: challenge`（需交互登录/挑战）。
- 全文 PII 同样 **403**。

**未绕过。** 未从摘要实现。`fit_predict` 仍 `NotImplementedError`。状态：**`BLOCKED_MISSING_FULL_METHOD`**。

## 加载器（默认名不升格）

- `load_dataset("AR")` / `("UMIST")` / `("BinAlpha")` / `("MSRA50")`：仍 `DatasetUnavailable`。
- BinAlpha 显式：`CANDIDATE_BIN_ALPHA`（seed 0，780×320）。
- AR 显式 `zenodo_third_party_full`：仍不可用，只说明第三方全集与 UNVERIFIED 子集，不返回论文 840 数组。

## 未做

未发明 URL；未编造 AR 7×120；未从 UMIST 575 任意删 11 张；未下载 CK+/EYaleB（同条 Zenodo 记录有这些文件，计划未授权）；未破解 Elsevier；未 git commit/push；未跑 72 格。
