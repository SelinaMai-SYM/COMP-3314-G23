# 基准数据

这份目录只放 Chang 等人 AAAI 2015《A Convex Formulation for Spectral Shrunk Clustering》用到的数据集、加载器和论文协议。没有用合成数据冒充 AR、JAFFE、ORL、UMIST、BinAlpha、MSRA50、YaleB 或 USPS。每个数据集在自己的包里：`ar/`、`jaffe/`、`orl/`、`umist/`、`binalpha/`、`msra50/`、`yaleb/`、`usps/`。共享的 ACC/NMI 在 `metrics/`，论文协议在 `protocols/`。

原始图像和压缩包放在对应包的 `data/` 下，并且被该目录的 `.gitignore` 排除。JAFFE 明确禁止再分发；Extended Yale B 和 AT&T/ORL 也限制公开再发布。这些文件留在本机，供后面的实验读取，不要提交进 git。校验和、来源和许可写在各包的 `manifest.yaml`。换一台机器时运行 `python scripts/download_datasets.py`（在 `v1` 目录下）。JAFFE 的官方 Zenodo 地址在 2026-10-20 对 curl 返回了 HTTP 403；本机文件是从同一地址取得的，SHA-256 已写入清单。脚本发现校验和一致就会跳过，不会重新下载。

## 加载

在 `v1` 目录下：

```python
from benchmarks import load_dataset, DatasetUnavailable
from benchmarks.orl import load_dataset as load_orl

X, y, metadata = load_dataset("ORL")
```

`X` 是 `float64`、形状 `(n, d)`，`y` 是 `int64` 标签。拿不到的数据集会抛出 `DatasetUnavailable`，不返回数组。预处理只有灰度、双线性缩放、拉直和除以 255，没有增强，也没有神经网络嵌入。

2026-10-20 的补回收记在 `docs/repair_round1_dataset_recovery.md`。2026-10-21 Round 2 的 source-of-truth 索引在 `docs/round2_source_of_truth.md`，HTTP 日志在 `docs/round2_missing_resources.md`。Task 1 矩阵与仍缺清单：[docs/resource_acquisition_matrix.md](../docs/resource_acquisition_matrix.md)、[docs/task1_resource_completion.md](../docs/task1_resource_completion.md)。每个数据集的完整说明在各自包的 `README.md`（`orl/`、`jaffe/`、`yaleb/`、`usps/`、`ar/`、`umist/`、`binalpha/`、`msra50/`），不要只看本页摘要。`load_dataset("ORL")` 和 `load_dataset("YaleB")` 仍分别返回 Olivetti 64×64 流程和邓蔡 `YaleB_32x32.mat`。新版本要用显式 `version`。BinAlpha 的 26×30 重建是 `version="letters26x30_seed0"`，默认名仍不可用。

## 状态

| 数据集 | 状态 | n | 类 | 处理后维度 | 来源 | SHA-256 | 许可 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ORL | approximate（默认） | 400 | 40 | 1024（32×32） | figshare 5976027 | `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794` | 默认仍是 Olivetti 64×64→32×32。额外 `version="att92"` 为剑桥 92×112，见 `manifest_att92.yaml` |
| JAFFE | verified | 213 | 10 | 676（26×26） | Zenodo 14974867 | `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b` | 禁止再分发，仅非商业研究 |
| YaleB | approximate（默认） | 2414 | 38 | 1024（已是 32×32） | 邓蔡页面的 `YaleB_32x32.mat` | `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99` | 默认仍是邓蔡 mat。额外 `version="cropped2414"` 见 `manifest_cropped.yaml`，不声称与 mat 逐像素同一 |
| USPS | verified | 9298 | 10 | 256（已是 16×16） | LIBSVM `usps.bz2` 与 `usps.t.bz2` | `usps.bz2` `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f`；`usps.t.bz2` `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` | 公开研究发布，压缩包内无许可证文件 |
| AR | unavailable | 未测到 | 未测到 | 未测到 | 见 `ar/manifest.yaml` 中的失败 URL | unknown | 需要大学邮箱申请和密码 |
| UMIST | unavailable（默认；564 未取得） | 默认未测到。磁盘上有 1012 / 575，不是 564 | 20（额外档案） | 见 `manifest_wayback.yaml` | Wayback / Figshare 额外版本 | 见额外 manifest | 默认 `load_dataset("UMIST")` 仍抛 `DatasetUnavailable`。额外 `precropped575` / `figshare575` 不是论文的 564 |
| BinAlpha | unavailable | 未测到 | 未测到 | 未测到 | 未找到可追溯文件 | unknown | unknown |
| MSRA50 | unavailable | 未测到 | 未测到 | 未测到 | 未找到 1799 张、12 类的文件 | unknown | unknown |

论文声称但本机没有测到的规模（AR 840/120、UMIST 564/20、BinAlpha 26×30、MSRA50 1799/12）没有写成已核实样本数。ORL 是 64×64 Olivetti 再缩到 32×32，不是 92×112 原图的逐样本同一版本。协议里 Track A / Track B、以及 “50 次” 和 “best objective” 同时出现的歧义，写在 `protocols/original_paper.yaml`。带宽、`G` 的初值、K-means 的 `n_init` 和 10 到 150 的步长，论文都没有给出；协议只把前三项中已声明的假设标成 assumption，`n_init` 仍是 unspecified。
