# Task 1：哪些原文资源仍然缺失

日期：2026-10-21。只做资源核验与合法补档。未改 `method_extension/`，未重写 `report/`，未跑 72 格，未 git commit。

结论先说：**仍缺的是论文协议意义上的 AR 840/120、UMIST 564、BinAlpha 26×30、MSRA50 1799/12 文件，以及 Hou et al. IPM 2013 第 3 节全文与所有方法的作者代码。** 已有且哈希仍匹配的档案没有重下。

## 仍然缺失（原文资源）

1. **AR 官方图像包与 840/120 规则**  
   官方申请页 HTTP **503**，HTTPS 证书失败（curl 60，未跳过证书）。普渡镜像 404/502。2012 Wayback 官方页确认：126 人、大学邮箱申请密码、**禁止再分发**、**正文没有 840/120**。CVC TR 24 已合法保存，不是图像。Zenodo 19683234 仍因非 Martinez 来源且与官方禁再分发冲突而 **未下载**。同组 arXiv:1411.6241 写 AR 840×768，仍无图像名单。**没有编造 7×120 子集。**

2. **MSRA50 的 1799×12×1024 真实文件**  
   文献指针仍在（Chang/Nie/Yang 引 He 2004/TPAMI 2005 Laplacianfaces：12 人、每场 64–80、裁 32×32）。邓蔡 `data.html` / `FaceData.html` / `MLData.html` HTTP 200，**无 MSRA50**。GitHub 仓库搜索 `MSRA50 mat` `total_count=0`。未用 MSRA-B/10K/TD500，未用 CSDN/百度网盘非官方包。计数落在 1536–1920 **不等于**已找到文件。

3. **UMIST 论文 564 张**  
   2001 官方页（Wayback GET 200）写 “564 images of 20 people”，并提供 29Mb `face.tar.gz` 与 4.5Mb `cropped.tar.gz`。本机这两份档案哈希与 Round 2 一致：未裁剪 **1012** 不重复 PGM，裁剪 **575** PGM（565 互异像素）。页面自己的 cropped 包就不是 564。去掉 10 张 `1b/final*.pgm` 像素副本得到 **565≠564**。没有证据再删哪 1 张。默认加载器仍不可用。

4. **论文 BinAlpha 26×30**  
   父集 Binary Alphadigits 已在（36×39，SHA 未变）。AAAI/arXiv 仍未写父集、尺寸或种子。`letters26x30_seed0` 仍是 UNVERIFIED reconstruction。

5. **SPLS / SLPS 第 3 节**  
   Unpaywall `is_oa=false` / `oa_status=closed` / `oa_locations=[]`。OpenAlex `oa_url=null`。Semantic Scholar `CLOSED`。arXiv 0 条。作者页 `[PDF]` 仍是 Elsevier DOI。HKU Find@HKUL 仅目录（200），Scholars Hub 403；本会话 **没有** 已登录的 ScienceDirect PDF。`fit_predict` 仍 `NotImplementedError`。**没有从摘要编算法。**

6. **作者代码**  
   SSC：xiaojun.ai HTTP 200，无 2015 实现；GitHub `spectral shrunk clustering` 仓库 **0**。Hou GitHub 无 SLPS（`PublicationCode` 空仓）。Ding–Li / Wu–Schölkopf / Chang 基线均 `CODE_NOT_FOUND`。未把 Elhamifar Sparse Subspace Clustering 或 2016 PSLSR 当成 SSC/SPLS。

## 本轮合法取得（不是上述缺口的填补）

- AAAI SSC PDF（哈希与已有 `9736-45063-1-PB.pdf` 相同）
- arXiv:1411.6308 预印本
- NeurIPS 2006 LLC
- Ding–Li 2007 作者页 PDF（ACM 403，未绕过）
- CVC TR 24 与 AR 官方 Wayback HTML（条款，非图像）
- UMIST 2001 页 HTML
- 同组 arXiv:1411.6241v1（MSRA50 文献指针，不是数据文件）

## 明确拒绝 / 未做

- 未重下哈希匹配的 JAFFE / att_faces / CroppedYale / USPS / olivetti / YaleB mat / binaryalphadigs / UMIST tars
- 未下载 Zenodo `ARDB_Full.zip`
- 未破解 Elsevier
- 未联系作者（计划禁止）
- 未把 TUNA/PyPI 当数据集
- 未实现 SPLS
- 未跑聚类网格
