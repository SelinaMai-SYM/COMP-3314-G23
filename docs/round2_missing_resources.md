# Round 2 缺失资源（HTTP 索引）

日期：2026-10-21。User-Agent：`COMP3314-SSC-dataset-recovery/2.0`。本机 `urllib` 对多数 HTTPS 为 `CERTIFICATE_VERIFY_FAILED`，**不以该 TLS 失败当作源站 HTTP 状态**。下表 HTTP 来自 `curl -sI -L` 或实际 GET。原始记录：[round2_http_log.json](round2_http_log.json)。

各数据集说明见对应 README，不要只读本页。

TUNA / PyPI **不是**数据集源，本轮未请求。

## 仍然缺失的目标

| 目标 | 为何仍缺 | 校验和 |
| --- | --- | --- |
| AR 官方包与 840/120 | 官方 503 / 证书问题；Zenodo 第三方包被拒绝 | 无（未保存图像） |
| UMIST 564 | 已有 1012/575，去掉 10 张像素副本是 565 | 已有档案见 [umist/README.md](../benchmarks/umist/README.md) |
| 论文 BinAlpha 26×30 | 父集已下；无 Chang 使用证据 | 父集 SHA-256 见下 |
| MSRA50 1799/12 文件 | 文献指针存在，无 URL，无文件 | 无 |

## 本轮实际请求

| URL | HTTP | 许可 / 备注 | 保存？ |
| --- | --- | --- | --- |
| `https://cs.nyu.edu/~roweis/data.html` | 403 | 现网页 | 否 |
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data.html` | 200 | Roweis 页：Binary Alphadigits 36×39、20×16；UMIST 575 | 否（页） |
| `https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | HEAD/GET 403 | — | 否 |
| `http://www.cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | GET 403（跳到 HTTPS） | — | 否 |
| `https://web.archive.org/web/20240616024002id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | GET **200**，532304 字节 | mat 内无许可文本 | **是** `benchmarks/binalpha/data/binaryalphadigs.mat` SHA-256 `3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7` |
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | HEAD 200 | 未再 GET（已有上一捕获） | 否 |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` | 200 | 非商业科研；无 MSRA50/BinAlpha 文件 | 否 |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` | 200 | 仅 Yale/ORL/YaleB | 否 |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/YaleB_32x32.mat` | 200，`Content-Length: 2214688` | 邓蔡页条款 | 否（已有文件，未覆盖） |
| `https://zenodo.org/records/19683234` | 200 | 上传者声称 CC-BY-4.0 | 否（元数据） |
| `https://zenodo.org/api/records/19683234` | 200 | 同上；`ARDB_Full.zip` size 120587997，md5 `bb97bd9237680744c0c7268624696263` | 否 |
| `https://zenodo.org/records/19683234/files/ARDB_Full.zip?download=1` | HEAD 200，`Content-Length: 120587997` | **官方 AR 禁再分发**；第三方转载，未 GET 正文 | 否 |
| `https://zenodo.org/api/records/19683234/files/ARDB_Full.zip/content` | HEAD 200，同样 120587997 | 同上 | 否 |
| `http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | 503 | 官方申请页 | 否 |
| `https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | curl 0（TLS） | 未跳过证书 | 否 |
| `https://engineering.purdue.edu/~aleix/ARdatabase.html` | curl 0（TLS） | — | 否 |
| `https://engineering.purdue.edu/~aleix/aleix_face_DB.html` | 404 | — | 否 |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip` | 200 | AT&T/Olivetti 致谢 | 否（已有 zip，未覆盖） |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html` | 200 | 同上 | 否 |
| `https://zenodo.org/records/14974867` | 200 | JAFFE：非商业、禁再分发 | 否 |
| `https://zenodo.org/records/14974867/files/jaffe.zip?download=1` | HEAD 200，`Content-Length: 12290558` | 与本机 zip 大小一致；未覆盖 | 否 |
| `https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.bz2` | 200，6579383 | 公开研究发布；包内无许可文件 | 否（已有） |
| `https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass/usps.t.bz2` | 200 | 同上 | 否（已有） |
| `https://ndownloader.figshare.com/files/5976027` | HEAD 403 | Olivetti mat 已在本地 | 否 |
| `http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` | 404 | — | 否 |
| `https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` | 200 | 研究使用 + Yale 再分发限制 | 否（已有 zip，未覆盖） |
| `https://lear.inrialpes.fr/people/triggs/events/iccv03/cdrom/iccv03/0385_he.pdf` | 200 | He ICCV 2003 | 否（只读文本） |
| `https://people.engr.tamu.edu/rgutier/web_courses/cpsc689_s07/he2005laplacianfaces.pdf` | 200 | He TPAMI 2005 教学副本 | 否 |
| `https://people.engr.tamu.edu/rgutierrez/web_courses/cpsc689_s07/he2005laplacianfaces.pdf` | 404 | 错路径 | 否 |
| `https://arxiv.org/abs/1411.6241` | 200 | 同组文；MSRA50→He 2004 | 否 |
| `https://arxiv.org/pdf/1411.6241.pdf` | 404 | 该 PDF 路径无效 | 否 |
| `http://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` | 202 | WAF | 否 |
| `https://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` | 202 | WAF | 否 |
| `http://images.ee.umist.ac.uk/danny/database.html` | 502 | — | 否 |
| `https://www.sheffield.ac.uk/eee/research/iel/research/face` | 404 | — | 否 |

## 高亮

1. Binary Alphadigits 只能从 Wayback 取得；现网 NYU 403。
2. AR Zenodo 文件在协议上可下（HEAD 200），在许可上不可用。
3. JAFFE 官方 zip 当天 HEAD 已是 200（去年 403），本机校验和未变，未重下。
4. 现网 CroppedYale.zip 仍是 404。
5. 没有请求任何 PyPI / TUNA 数据集 URL。
