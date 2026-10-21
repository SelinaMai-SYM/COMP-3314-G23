# Task 1 资源获取矩阵（2026-10-21）

工作区：`v1/`。User-Agent：`COMP3314-SSC-dataset-recovery/3.0`。HTTP 原始记录：[task1_http_log.json](task1_http_log.json)。本轮先按 [round2_source_of_truth.md](round2_source_of_truth.md) **重算磁盘 SHA-256 与样本数**；哈希仍匹配的档案 **没有重下**（JAFFE zip、`att_faces.zip`、CroppedYale zip、USPS bz2、`olivettifaces.mat`、`YaleB_32x32.mat`、`binaryalphadigs.mat`、两份 UMIST tar、Figshare UMIST mat）。

状态词只用：`COMPLETE_VERIFIED` / `COMPLETE_WITH_UNSPECIFIED_SETTINGS` / `PARTIAL_VERIFIED` / `CANDIDATE_ONLY` / `BLOCKED_ACCESS` / `BLOCKED_MISSING_METHOD` / `NOT_FOUND`。

代码来源只用：`OFFICIAL_AUTHOR_CODE` / `VERIFIED_AUTHOR_DISTRIBUTION` / `THIRD_PARTY_CODE` / `PAPER_BASED_REIMPLEMENTATION` / `CODE_NOT_FOUND`。第三方算法源码若取得会进 `vendor/`，**不**混进 `fit_predict`。本轮 **没有** 克隆任何第三方算法仓库。sklearn 是库，不是作者代码。

清华 TUNA / PyPI **不是**数据集源，本轮未请求。未绕过 paywall。未下载 Zenodo `19683234`（非 Martinez 官方，官方禁止再分发）。未编造 AR 840 子集，未从 575 张 UMIST 任意删图凑 564。未用 MSRA-B / MSRA10K / MSRA-TD500 顶名。

没有一个数据集达到 `COMPLETE_VERIFIED`（论文协议里插值、子集规则或缩放核仍有未写项）。

## 数据集

| 数据集 | 矩阵状态 | obtained | verified | exact (论文样本集) | source | missing |
| --- | --- | --- | --- | --- | --- | --- |
| ORL `att92` | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y：400 PGM / 40 人 × 10，`(112,92)` | 计数 400/40 相符 | 剑桥 `att_faces.zip`，HEAD 200 未重下 | 插值未写 |
| ORL 默认 Olivetti | `PARTIAL_VERIFIED` | Y | Y：对 figshare/sklearn mat | N：64×64 不是 92×112 | `olivettifaces.mat` | 不是 original-source |
| JAFFE | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y：213 TIFF / 10 人 | Y：计数 | Zenodo 14974867 `jaffe.zip` | 插值未写 |
| YaleB `cropped2414` | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y：2452 PGM − 38 Ambient = 2414 / 38 | 计数相符 | Wayback UCSD `CroppedYale.zip` | 插值未写；现网 404 |
| YaleB 邓蔡 mat | `PARTIAL_VERIFIED` | Y | Y：2414×1024 | 计数相符，像素≠cropped | 邓蔡 `YaleB_32x32.mat` HEAD 200 | 缩放核未知 |
| USPS | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Y | Y：7291+2007=9298 / 10 / 256 | 计数相符 | LIBSVM `usps.bz2` + `usps.t.bz2` | 发布已是 16×16 |
| AR 官方图像 | `BLOCKED_ACCESS` | N | N | N | 官方申请页 HTTP **503**；HTTPS curl **60**（证书）；普渡 404/502 | 密码分发；禁再分发 |
| AR 840/120 | `NOT_FOUND` | N | N | N | 2012 Wayback 官方页 **无 840**；同组 arXiv:1411.6241 写 840×768 仍无名单 | 未写哪 840 张；未编造 |
| UMIST 564 | `CANDIDATE_ONLY` | 档案 Y，564 N | 对 1012/575 档案 Y | N：565≠564 | 2001 页写 564，同时链 4.5Mb `cropped.tar.gz`=本机 575 | 无证据充分的 564 规则 |
| BinAlpha 论文 26×30 | `NOT_FOUND` | 父集 Y | 父集 36×39 Y | N | Roweis Wayback `binaryalphadigs.mat` | 无 Chang 使用证据/种子 |
| BinAlpha `letters26x30_seed0` | `CANDIDATE_ONLY` | reconstruction | UNVERIFIED | N | 本仓库 seed 0 | 不当论文集 |
| MSRA50 1799/12/1024 | `NOT_FOUND` | N | N | N | 同组文引 He 2004；邓蔡页无文件；GitHub 仓库搜索 0 | 无真实文件 |

### 已核验档案（本轮重算，未覆盖）

| 文件 | 字节 | SHA-256 | 样本 |
| --- | --- | --- | --- |
| `benchmarks/orl/data/att92/att_faces.zip` | 3769022 | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` | 400 PGM，40 人 |
| `benchmarks/orl/data/olivettifaces.mat` | 4260520 | `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794` | 加载 `(400,1024)` |
| `benchmarks/jaffe/data/jaffe.zip` | 12290558 | `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b` | 213 TIFF |
| `benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` | 58493820 | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` | 2452 PGM / 2414 非 Ambient |
| `benchmarks/yaleb/data/YaleB_32x32.mat` | 2214688 | `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99` | 加载 `(2414,1024)` |
| `benchmarks/usps/data/usps.bz2` | 6579383 | `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` | 与 `.t.bz2` 合计 9298 |
| `benchmarks/usps/data/usps.t.bz2` | 1831726 | `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` | 见上 |
| `benchmarks/binalpha/data/binaryalphadigs.mat` | 532304 | `3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7` | 36×39=1404 |
| `benchmarks/umist/data/wayback_sheffield/face_wayback_20050403.tar.gz` | 29385054 | `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` | 1012 不重复 PGM |
| `benchmarks/umist/data/wayback_sheffield/cropped_wayback_20070805.tar.gz` | 4506480 | `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` | 575 PGM，565 互异像素 |
| `benchmarks/umist/data/figshare_umist_cropped/umist_cropped.mat` | 5927440 | `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` | 575，非 564 |

处理阵列哈希（本地产物，路径在 `data/*/processed/`）与 Round 2 README 一致，见各包 README。

### 本轮新保存（非图像库）

| 文件 | 字节 | SHA-256 | 许可/身份 |
| --- | --- | --- | --- |
| `SSC_method/resources/Chang_et_al_2015_SSC_AAAI.pdf` | 851255 | `970ee4e65fd73aca46b3f983098f87105fb7e45726b767ec7925c9188646dfaf` | AAAI OA；与仓库外 `9736-45063-1-PB.pdf` 同一哈希 |
| `SSC_method/resources/Chang_et_al_2014_SSC_arxiv_1411.6308.pdf` | 233802 | `b4bb9f8984db89ee5c17a2c2200a6764085d81d3da5fc26b2c144e2202262e39` | arXiv OA 预印本 |
| `baselines/llc/resources/Wu_Schoelkopf_2006_NIPS_LLC.pdf` | 127718 | `17828ebae410aca05c026767bffb2befec09a5edfe4232c770c2782a904c12c3` | NeurIPS OA |
| `baselines/lda_kmeans/resources/Ding_Li_2007_ICML_LDA_Kmeans.pdf` | 219382 | `6b643ed6605daca3aaeaf1423572836a783f90df0ee0f4a5aec32c13784b342a` | 作者页 OA PDF（非 ACM paywall） |
| `benchmarks/ar/resources/Martinez_Benavente_1998_CVC_TR24.pdf` | 306151 | `9dfb1d979781d48f5a2de1b7c277a59dc71ffcb768da60f20e562d689418951b` | CVC TR；**不是**图像 |
| `benchmarks/ar/resources/ARdatabase_wayback_20120501.html` | 19396 | `fea9bd20c825f94f9abd8862be63f7261cd533c43085149af0179d784a4344d8` | 官方条款页 Wayback `id_` GET **200** |
| `benchmarks/umist/resources/database_wayback_20010405.html` | 3878 | `a8a91fbea393f524e3275acad9356512145547217c18f446eb08eae849cb263a` | 写 564 并链 4.5Mb cropped tar |
| `benchmarks/msra50/resources/Chang_Nie_Yang_Huang_2014_arxiv_1411.6241v1.pdf` | 463461 | `d3d00b0fa2eeff938d65800a3a7e4d1b08987de73932e9bd04de801e708badb2` | 同组 OA；表列 MSRA50 1799/12/1024。`arxiv.org/pdf/1411.6241.pdf` 当天 **404** |

## 基线 / SSC

| 方法 | 矩阵状态 | paper | code | implemented | gaps |
| --- | --- | --- | --- | --- | --- |
| SSC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | AAAI OA + arXiv 已存 | `CODE_NOT_FOUND`（GitHub 仓库搜索 `spectral shrunk clustering` `total_count=0`；xiaojun.ai 无 2015 代码） | `PAPER_BASED_REIMPLEMENTATION`（E8/E13） | 无作者二进制；图带宽/对称化为假设 |
| K-means | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Chang Setup OA | `THIRD_PARTY_CODE` sklearn Lloyd；`CODE_NOT_FOUND` 作者码 | 包装 `fit_predict` | 50 次在协议层 |
| SC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Eq. (4) OA | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | δ、union kNN |
| PCA-KM | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | 名称+Setup OA | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | 维数步长 10 |
| PCA-SC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | 名称+Eq. (4) | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | 同上 |
| LDA-KM | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | Ding–Li 作者 PDF GET **200** | `CODE_NOT_FOUND`；ACM PDF **403** | `PAPER_BASED_REIMPLEMENTATION` | `sw_reg` / `max_iter` |
| LDA-SC | `BLOCKED_MISSING_METHOD` | Chang **只给名称** | `CODE_NOT_FOUND` | 仅 `APPROXIMATE` 两解释 | **不进忠实主表** |
| LLC | `COMPLETE_WITH_UNSPECIFIED_SETTINGS` | NIPS 2006 OA GET **200** | `CODE_NOT_FOUND` | `PAPER_BASED_REIMPLEMENTATION` | Yang 2010 未混入；k=5 是比较协议 |
| SPLS / SLPS | `BLOCKED_MISSING_METHOD` | Hou et al. IPM 2013 DOI `10.1016/j.ipm.2013.01.004`；Unpaywall/OpenAlex **closed**；arXiv `totalResults=0`；作者 `[PDF]`=Elsevier DOI | `CODE_NOT_FOUND`（Hou GitHub 无 SLPS；`PublicationCode` 空仓） | `NotImplementedError` | **未读到第 3 节**；无方程则不实现 |

## 缺口检索（真实 HTTP）

未 GET Zenodo `ARDB_Full.zip`。未破解 Elsevier。

| 目标 | URL | HTTP | 结果 |
| --- | --- | --- | --- |
| AR 官方 | `http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | **503** | 无图像 |
| AR 官方 HTTPS | `https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | curl **60** | 证书失败，未 `-k` |
| AR 普渡 | `engineering.purdue.edu/~aleix/ARdatabase.html` 等 | **404** | — |
| AR RVL | `http://rvl1.ecn.purdue.edu/ARdatabase/ARdatabase.html` | **502** | — |
| AR Wayback CDX | OSU 页 | **200**，有 2012–2016 捕获 | GET 了 20120501 HTML；正文 126 人、需密码、**禁止再分发**、**无 840** |
| AR CVC TR | `.../MaB1998/CVCReport24.pdf` | **200** | 技术报告，无图像包 |
| AR Zenodo 19683234 | 记录页 | **200**（元数据） | **拒下** |
| MSRA 邓蔡 | `data.html` / `FaceData.html` / `MLData.html` | **200** | 正文无 MSRA / MSRA50 / BinAlpha 文件 |
| MSRA GitHub | `search/repositories?q=MSRA50+mat` | **200** | `total_count=0` |
| UMIST 现网 | `images.ee.umist.ac.uk` | **502**；Sheffield **404**；Lincoln **202** WAF | 未重下已有 tar |
| UMIST 2001 页 | Wayback `id_` | **200** | 「564 images of 20 people」且 cropped tar 4.5Mb = 本机 575 文件 |
| SPLS Unpaywall | `api.unpaywall.org/v2/10.1016/j.ipm.2013.01.004` | **200** | `is_oa=false`, `oa_status=closed`, `oa_locations=[]` |
| SPLS OpenAlex | 同 DOI | **200** | `is_oa=false`, `oa_url=null`, `any_repository_has_fulltext=false` |
| SPLS S2 | 同 DOI | **200** | `isOpenAccess=false`, `CLOSED` |
| SPLS arXiv | export query | **200** | `totalResults=0` |
| SPLS HKU Find | Find@HKUL | **200** 目录壳 | 本会话无已登录 PDF |
| SPLS HKU Hub | Scholars Hub | **403** | — |
| SSC 作者页 | `https://www.xiaojun.ai/` | **200** | 无 2015 代码 |
| SSC GitHub | `search/repositories?q=spectral+shrunk+clustering` | **200** | `total_count=0` |
| AAAI SSC PDF | ojs download | **200** | 已存 |
| NIPS LLC PDF | proceedings.neurips.cc | **200** | 已存 |
| Ding–Li 作者 PDF | ranger.uta.edu | **200** | 已存 |
| Ding–Li ACM | `dl.acm.org/doi/pdf/10.1145/1273496.1273562` | **403** | 未绕过 |
| 同组 1411.6241 | `/pdf/1411.6241.pdf` **404**；`/pdf/1411.6241v1.pdf` **200** | 已存 v1 |

加载器抽查（本轮）：`ORL` `(400,1024)`；`ORL att92` `(400,1024)` 原图 `[112,92]`；`JAFFE` `(213,676)`；`YaleB` / `cropped2414` `(2414,1024)`；`USPS` `(9298,256)`；`AR` / `UMIST` / `BinAlpha` / `MSRA50` 默认仍 `DatasetUnavailable`；`UMIST precropped575` n=575、`unique_pixel_arrays=565`。
