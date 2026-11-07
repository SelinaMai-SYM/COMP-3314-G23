# 第一轮数据集回收（2026-10-20）

检查日期都是 2026-10-20。下面的 HTTP 状态来自当天的 `urllib` HEAD 或 `curl -sI -L` / `curl -L`，User-Agent 为 `COMP3314-SSC-dataset-recovery/1.0`。没有编造 URL、校验和或时间戳。旧文件 `benchmarks/orl/data/olivettifaces.mat`（SHA-256 `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794`）和 `benchmarks/yaleb/data/YaleB_32x32.mat`（SHA-256 `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99`）没有被覆盖。新图像都在各自的 `benchmarks/<name>/data/` 下面，`data/.gitignore` 的 `*` 已忽略它们（`git check-ignore -v` 确认）。

`load_dataset("ORL")` 仍返回 Olivetti 64×64 再双线性缩到 32×32。`load_dataset("YaleB")` 仍返回邓蔡矩阵。`load_dataset("UMIST")`、`load_dataset("AR")`、`load_dataset("BinAlpha")`、`load_dataset("MSRA50")` 仍抛出 `DatasetUnavailable`。

## 每个数据集的决定

| 数据集 | 决定 | 路径 | SHA-256 | n | 类 | 尺寸 |
| --- | --- | --- | --- | --- | --- | --- |
| ORL / AT&T 92×112 | obtained | `benchmarks/orl/data/att92/att_faces.zip` | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` | 400 | 40 | PGM 宽 92、高 112；数组 `(400, 112, 92)` uint8，像素 0..251。32×32 三套插值见 `manifest_att92.yaml` |
| YaleB 裁剪原图 | obtained | `benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` | zip 内 2452 张 PGM、38 个受试者文件夹；去掉文件名含 Ambient 的 38 张后为 2414，且这 2414 张全是 `(192, 168)` | 38 | 非环境光图像头为宽 168、高 192。不是 `YaleB_32x32.mat` 的逐像素同一版本 |
| AR | unavailable | 无文件 | 无 | 未测到。没有构造 840 张子集 | 未测到 | 未测到 |
| UMIST 564 张目标 | unavailable（就 564 这个目标而言） | 见下一行的两个档案，都不能当作 564 | 见下 | 页面写 564；读到的文件不是 564 | 20（两个档案都是） | 见下 |
| UMIST 未裁剪 tar | approximate | `benchmarks/umist/data/wayback_sheffield/face_wayback_20050403.tar.gz` | `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` | 1012 个不重复 PGM（tar 里 `1t/1t052.pgm` 重复一次，成员数 1013） | 20 | 122 种形状，最常见 `(196, 170)` 有 71 张。像素 0..238。没有堆成单一矩阵 |
| UMIST 预裁剪 tar | approximate | `benchmarks/umist/data/wayback_sheffield/cropped_wayback_20070805.tar.gz` | `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` | 575 张 PGM，其中 565 个像素数组互不相同 | 20 | 全部 `(112, 92)`，像素 0..238 |
| UMIST Figshare mat | approximate | `benchmarks/umist/data/figshare_umist_cropped/umist_cropped.mat` | `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` | 575 个切片，565 个互不相同 | 20 | 每个 cell 为 `(112, 92, n_i)`。与上一行 tar 的像素哈希交集为 0（转置后仍为 0） |
| BinAlpha | unavailable | 无文件 | 无 | 未得到 26×30。没有用 Binary Alphadigits 顶上 | 未测到 | 未测到 |
| MSRA50 | unavailable | 无文件 | 无 | 未得到 1799 / 12。没有下载 MSRA-B、MSRA10K、MSRA-TD500 | 未测到 | 未测到 |

## ORL / AT&T

剑桥目录页列出的 `att_faces.zip` 与 `orl_faces.zip` 都是 3769022 字节。两次 GET 的 SHA-256 相同，所以只保留 `att_faces.zip`。解压后 400 个 PGM、40 个目录、每个 10 张。README 写明 92×112、8-bit。用 PIL 打开：`size` 为 `(92, 112)`（宽、高），数组为 `(112, 92)`，没有转置。全部图像像素最小 0、最大 251。边缘均值低于中心（上 8 行均值约 80.5，中心 32×32 窗口均值约 146.5），只说明存储顺序就是 PGM 行序，不断言和 Olivetti 64×64 是同一批像素。

32×32 uint8 数组在 `benchmarks/orl/data/att92/processed/`：

| 插值 | 文件 | 像素范围 | SHA-256 |
| --- | --- | --- | --- |
| nearest | `orl_att92_32x32_nearest_uint8.npy` | 0..244 | `d056a67cd3850f3c5cdf726c35247d0db11f41d45bfd11f4a5ee4da26f0fe2ea` |
| bilinear | `orl_att92_32x32_bilinear_uint8.npy` | 14..223 | `db8ed7a2db8b65aba8d34c9387420c014834d39cef5d27f6b994181de87a5f7d` |
| bicubic | `orl_att92_32x32_bicubic_uint8.npy` | 9..227 | `2e70df62a253d4f42b45dbb16b44ec0de1c832f5a1775fb398a77cbf4f058683` |

原生栈 `orl_att92_native_uint8.npy` 的 SHA-256 是 `c8559063d2dde31cdd1746f2038431d995013c96eaff31ef1aaa37f8053066fa`，形状 `(400, 112, 92)`。加载器把所选 32×32 数组除以 255 后按 C 序拉直。`version="att92"` 与 `version="att92_bilinear"` 都用双线性。

zip 内 README：使用这些图像时请注明 Olivetti Research Laboratory。剑桥 HTML 页则写请注明 AT&T Laboratories Cambridge，页脚为 Copyright 2002 AT&T Laboratories Cambridge。

| URL | 机构 | HTTP 或错误 | 得到文件？ | 许可 | 预处理 | 决定 |
| --- | --- | --- | --- | --- | --- | --- |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.zip` | 剑桥大学计算机实验室，托管 AT&T Laboratories Cambridge 档案 | 先用 Python `urllib` HEAD，SSL `CERTIFICATE_VERIFY_FAILED`，没有 HTTP 状态。随后 `curl -I` 与 GET 均为 HTTP 200，`Content-Type: application/zip`，`Content-Length: 3769022` | 是。SHA-256 `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec`。400 张，40 类，`(112, 92)` | 见上 | 三套 32×32 | obtained |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/orl_faces.zip` | 同上 | `urllib` HEAD 同样 SSL 失败。`curl -I` 与 GET 为 HTTP 200，长度 3769022 | 下载过，SHA-256 与 `att_faces.zip` 相同，因此没有另存第二份 | 同上 | 未再处理 | 与上一文件相同 |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/pub/data/att_faces.tar.Z` | 同上 | 只做了 `urllib` HEAD，SSL `CERTIFICATE_VERIFY_FAILED`。没有再用 curl 重试，没有 HTTP 状态，没有保存 | 否 | 页面称这是同一数据库的 tar | 无 | 未取得该压缩格式 |
| `https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html` | 同上 | `urllib` HEAD SSL 失败。`curl` HEAD 与 GET 为 HTTP 200，`text/html`，6036 字节 | 页面，不是图像包 | 请注明 AT&T Laboratories Cambridge | 无 | 说明页 |
| `http://www.cl.cam.ac.uk/Research/DTG/attarchive/pub/data/att_faces.zip` | 同上 | `urllib` 在跳到 HTTPS 后 SSL 失败。`curl -I -L`：HTTP 302 到 `https://www.cl.cam.ac.uk/Research/DTG/attarchive/pub/data/att_faces.zip`，再 HTTP 301 到小写路径，最后 HTTP 200，长度 3769022 | 没有单独再存一份；最终 URL 就是已保存的 zip | 同上 | 无 | 与已保存 zip 相同 |
| `https://cam-orl.co.uk/facedatabase.html` | cam-orl.co.uk（页面标题仍是 AT&T Database of Faces） | `curl` HEAD 与 GET 均为 HTTP 200，`text/html` | 页面。下载链接是已失效的 `ftp://ftp.uk.research.att.com` 形式，没有再请求该 FTP | 请注明 AT&T Laboratories Cambridge；Copyright 2001 | 无 | 说明页，不是新的图像包 |

## Extended Yale B 裁剪原图

当天这些现网地址都不是可用的 zip：

| URL | 机构 | HTTP 或错误 | 得到文件？ | 说明 |
| --- | --- | --- | --- | --- |
| `http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` | UCSD | `urllib` 与 `curl` 都是 HTTP 404，`text/html` | 否 | 官方裁剪 zip |
| `https://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` | UCSD | HTTP 404 | 否 | 同上的 HTTPS |
| `http://vision.ucsd.edu/~leekc/ExtYaleDatabase/CroppedYaleBZip/CroppedYale.zip` | UCSD | `urllib` HTTP 404 | 否 | 旧路径 |
| `http://vision.ucsd.edu/~iskwak/ExtYaleDatabase/CroppedYaleBZip/CroppedYale.zip` | UCSD | `urllib` HTTP 404 | 否 | 旧路径 |
| `http://vision.ucsd.edu/~leekc/ExtYaleDatabase/ExtYaleB.html` | UCSD | `curl` HTTP 404 | 否 | 说明页，不是 zip |
| `http://vision.ucsd.edu/~iskwak/ExtYaleDatabase/ExtYaleB.html` | UCSD | `curl` HTTP 404 | 否 | 说明页 |
| `https://vision.ucsd.edu/datasets/extended-yale-face-database-b-b` | UCSD | `urllib` HEAD SSL 失败。`curl` HEAD 与 GET 为 HTTP 200，HTML 31820 字节 | 页面 | 正文只说 Extended Yale B 有 16128 张、28 人，并链接到下面的 datarepo。没有给出仍有效的 CroppedYale.zip |
| `https://datarepo.eng.ucsd.edu/visiondata/iskwak/public_html/ExtYaleDatabase/ExtYaleB.html` | UCSD Jacobs / datarepo | GET HTTP 404，Apache 404 正文 | 否 | 现网页上的那个链接 |
| `https://datarepo.eng.ucsd.edu/visiondata/iskwak/public_html/ExtYaleDatabase/CroppedYaleBZip/CroppedYale.zip` | UCSD datarepo | HTTP 404 | 否 | 把旧 `~iskwak` 路径映射到 datarepo 后的尝试 |
| `https://datarepo.eng.ucsd.edu/visiondata/iskwak/public_html/ExtYaleDatabase/` | UCSD datarepo | HTTP 404 | 否 | 目录 |
| `https://datarepo.eng.ucsd.edu/visiondata/` | UCSD datarepo | HTTP 404 | 否 | 目录 |
| `http://vision.caltech.edu/~greg/ee148_spring2008/CroppedYale.zip` | Caltech | `urllib` HEAD SSL 失败。`curl`：HTTP 301 到 `https://www.vision.caltech.edu/~greg/ee148_spring2008/CroppedYale.zip`，随后 HTTP 404，`server: GitHub.com` | 否 | 课程镜像已不在 |
| `https://vision.caltech.edu/~greg/ee148_spring2008/CroppedYale.zip` | Caltech | 同样 301 后 HTTP 404 | 否 | 同上 |
| `http://luthuli.cs.uiuc.edu/~daf/courses/CV23/Assignments/assignment3/croppedyale.zip` | 伊利诺伊大学厄巴纳-香槟分校 | HEAD 与 GET 均为 HTTP 200，`application/zip`，6132444 字节 | 下载到 `/tmp`，没有放进仓库。SHA-256 `f548d2ae451dece41657a0840769ec4c69eca9bb5981ee1755730057a3d7001c` | 260 个非 `__MACOSX` 的 PGM，只有 yaleB01、yaleB02、yaleB05、yaleB07 四个目录。不是 2414 / 38 |
| `https://www.cs.yale.edu/cvc/projects/yalefacesB/yalefacesB.html` | 耶鲁大学 | `urllib` SSL 失败。`curl` HEAD 与 GET 为 HTTP 200，9088 字节 | 页面 | 这是原始 Yale B（10 人），不是 38 人裁剪集。页面写每个 `*.tar.gz` 约 11MB，共 90 个文件。没有下载这约 1GB |
| `ftp://plucky.cs.yale.edu/CVC/pub/images/yalefacesB/TarSets/` | 耶鲁大学 | `curl` 退出码含义为 `(56) response reading failed`，写出的 HTTP 码是 000 | 否 | 上一页给出的原始未裁剪包位置 |
| `https://academictorrents.com/details/aad8bf8e6ee5d8a3bf46c7ab5adfacdd8ad36247` | Academic Torrents | HTTP 200，`text/html` | 只保存了目录页，没有下 torrent。页面写 CroppedYale.zip 为 58.49MB | 说明页把内容说成 28 人、16128 张，和裁剪集的常见 38 人计数不一致，因此没有把它当作已核对的图像包 |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` | 浙江大学 | HEAD 与 GET 均为 HTTP 200 | 页面 | 邓蔡写明 YaleB 的 32×32 是把 UCSD 裁剪图再缩小的，并链接已 404 的 `ExtYaleB.html`。没有新的 PGM zip |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/YaleB/` | 浙江大学 | HTTP 403 | 否 | 目录被拒绝。已有的 `YaleB_32x32.mat` 未改 |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` | 浙江大学 | HEAD 与 GET 均为 HTTP 200 | 页面 | 没有 MSRA50 或 BinAlpha 文件链接 |

Internet Archive CDX（HTTP 200）列出 `http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip` 的 status 200 捕获，长度字段约 58MB。`~leekc/.../CroppedYale.zip` 的 CDX 结果是空数组。

实际保存的是：

`https://web.archive.org/web/20220127084451id_/http://vision.ucsd.edu/extyaleb/CroppedYaleBZip/CroppedYale.zip`

`curl` HEAD 与 GET 都是 HTTP 200，`application/zip`。HEAD 的 `Content-Length` 与 GET 的字节数都是 58493820。`unzip -t` 无错误。SHA-256 `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573`。

同一 `id_` 形式的 2016-09-09 捕获也做了 HEAD：HTTP 200，`Content-Length: 58493820`。没有再下载第二份。

2015-01-10 的 `ExtYaleB.html` Wayback 副本（HTTP 200）把 “Cropped Images” 指到上面的 UCSD zip，并写研究使用、引用 Georghiades 等 PAMI 2001；若发表裁剪图实验，同时引用 Lee 等 PAMI 2005。耶鲁原库页面另写：未经耶鲁大学许可，不能把图像并进另一个公开再分发的数据库。

核对结果：38 个受试者目录，没有 yaleB14。PGM 2452 张。其中文件名含 Ambient 的 38 张：10 张是 `(192, 168)`，28 张是 `(480, 640)`。其余 2414 张全部是 `(192, 168)`，uint8，像素 0..255。另有 18 个 `.pgm.bad`，没有算进 2414。按受试者编号排序后的每类张数是 64×10，然后 60、59、60、63、62、63、63，其余为 64。这与 `benchmarks/yaleb/manifest.yaml` 里邓蔡 `gnd` 的直方图相同。没有做逐像素对齐，所以不声称和 `YaleB_32x32.mat` 是同一矩阵。

2414 张非环境光图像另存了三套 32×32 uint8，加载时除以 255。`version="cropped2414"` 用双线性。SHA-256 写在 `benchmarks/yaleb/manifest_cropped.yaml`。

## AR Face Database

没有绕过登录，也没有保存图像，更没有编造 840 张子集。

| URL | 机构 | HTTP 或错误 | 得到文件？ | 许可 | 决定 |
| --- | --- | --- | --- | --- | --- |
| `http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | 俄亥俄州立大学 | HEAD 与 GET 都是 HTTP 503，正文为 nginx “503 Service Temporarily Unavailable” | 否 | 未读到当天页面。既有清单记录该库需大学邮箱申请密码，且禁止再分发 | unavailable |
| `https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` | 俄亥俄州立大学 | `curl`：`SSL certificate problem: certificate has expired`，HTTP 码 000。没有用 `-k` 跳过证书 | 否 | 未知 | unavailable |
| `https://engineering.purdue.edu/~aleix/aleix_face_DB.html` | 普渡大学 | HTTP 404 | 否 | 未知 | unavailable |
| `https://engineering.purdue.edu/~aleix/ARdatabase.html` | 普渡大学 | HTTP 404 | 否 | 未知 | unavailable |
| `http://rvl.ecn.purdue.edu/~aleix/aleix_face_DB.html` | 普渡大学 RVL | HTTP 301 到上面的 `engineering.purdue.edu` 地址，随后 HTTP 404 | 否 | 未知 | unavailable |
| `http://www.cat.uab.cat/Public/Publications/1998/MaB1998/` | 巴塞罗那自治大学 CVC | GET HTTP 200，正文只有 “Unable to connect to mySQL server. Administrator has been warned.” | 否，65 字节错误页 | 未知 | 不是数据库 |
| `https://tsapps.nist.gov/BDbC/Search/Details/301` | NIST | HTTP 404 | 否 | 目录项，即使打开也不是图像 | unavailable |
| `https://doi.org/10.57702/q1qmqyrd` | TIB / DOI | HEAD：HTTP 302 到 `https://service.tib.eu/ldmservice/dataset/3df8623c-9ddc-40e5-936d-3f0d4960a944`，该地址 HTTP 200，`text/html` | 没有下到图像 | 未知 | 元数据跳转 |
| `https://service.tib.eu/ldmservice/dataset/ar-database` | TIB | HEAD HTTP 200。GET HTTP 200，正文是 Anubis “Making sure you're not a bot” 的 JavaScript 质询，不是图像 | 否 | 未知 | 没有绕过质询 |

CVC 技术报告 PDF 的检索结果写获取方式是发邮件。当天没有可用的直接下载，也没有提交申请表。决定：unavailable。

## UMIST / Sheffield

目标是 564 张、20 人。计数不同的档案没有当成精确集。

| URL | 机构 | HTTP 或错误 | 得到文件？ | 核对 | 决定 |
| --- | --- | --- | --- | --- | --- |
| `http://eprints.lincoln.ac.uk/id/eprint/16081/` | 林肯大学 | HTTP 202，`x-amzn-waf-action: challenge`，`Content-Length: 0` | 否 | 无 | 未取得 |
| `https://eprints.lincoln.ac.uk/id/eprint/16081/` | 林肯大学 | HTTP 202，同样的 WAF challenge | 否 | 无 | 未取得 |
| `http://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` | 林肯大学 | HTTP 202，WAF challenge | 否 | 无 | 未取得 |
| `https://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` | 林肯大学 | HTTP 202，WAF challenge | 否 | 无 | 未取得 |
| `https://web.archive.org/cdx/search/cdx?url=eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz&output=json&fl=timestamp,statuscode,length,original&limit=15` | Internet Archive | HTTP 200，正文 `[]` | 否 | 该 URL 没有 status 200 捕获 | 未取得 |
| `http://images.ee.umist.ac.uk/danny/database.html` | UMIST | HTTP 502，`Content-Length: 0` | 否 | 无 | 现网不可用 |
| `http://images.ee.umist.ac.uk/danny/face.tar.gz` | UMIST | HTTP 502 | 否 | 无 | 现网不可用 |
| `http://images.ee.umist.ac.uk/danny/cropped.tar.gz` | UMIST | HTTP 502 | 否 | 无 | 现网不可用 |
| `https://www.sheffield.ac.uk/eee/research/iel/research/face` | 谢菲尔德大学 | HTTP 301 到 `https://sheffield.ac.uk/eee/research/iel/research/face`，随后 HTTP 404 | 否 | 无 | 未取得 |
| `https://web.archive.org/web/20010405074800id_/http://images.ee.umist.ac.uk/danny/database.html` | Internet Archive，原页为 UMIST | HTTP 200 | 页面 | 页文写 564 张、20 人，PGM，约 220×220。只允许在书面许可下发表受试者 1a。下载链接为相对路径 `face.tar.gz`（约 29Mb）和 `cropped.tar.gz`（约 4.5Mb） | 说明页 |
| `https://web.archive.org/web/20050403232828id_/http://images.ee.umist.ac.uk/danny/face.tar.gz` | Internet Archive / UMIST | HEAD HTTP 200，`Content-Length: 29385054`，`Content-Type: application/x-tar`。GET HTTP 200，29385054 字节。`file` 识别为 gzip，原名 `face.tar`，1997-07-08 | 是。SHA-256 `df58ad9a38573624ab75be66d7d47243f674214cc0cb68d8a619247e1fd0c8fb` | 1012 个不重复 PGM，20 个目录，122 种形状。不是 564 | approximate，不当作精确集 |
| `https://web.archive.org/web/20070805190146id_/http://images.ee.umist.ac.uk/danny/cropped.tar.gz` | Internet Archive / UMIST | HEAD HTTP 200，`Content-Length: 4506480`。GET HTTP 200，4506480 字节。gzip，原名 `cropped.tar`，1998-10-16 | 是。SHA-256 `c1f7f6ead672c9861428f4a4366c73e3fcc9ef4654a1bc0b880f2257a978dff4` | 575 张，全部 `(112, 92)`，像素 0..238，565 个互异像素数组，20 人 | approximate，不是 564 |
| `https://cs.nyu.edu/~roweis/data.html` | 纽约大学 | HTTP 403，`text/html` | 否 | 无 | 现网拒绝 |
| `http://www.cs.nyu.edu/~roweis/data.html` | 纽约大学 | HTTP 301 到 `https://www.cs.nyu.edu/~roweis/data.html`，再 301 到 `https://cs.nyu.edu/~roweis/data.html`，最后 HTTP 403 | 否 | 无 | 现网拒绝 |
| `https://cs.nyu.edu/~roweis/data/umist_cropped.mat` | 纽约大学 | HTTP 403 | 否 | 无 | 未下载 |
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data.html` | Internet Archive / 纽约大学 | HTTP 200 | 页面 | 页文写 UMist Faces 为 575 张、20 人、112×92，由 Daniel Graham 手工裁剪，并链接 `umist_cropped.mat` 与 `umist_uncropped.mat`。没有把这页上的 mat 当成 564 张原集去下载 | 说明页；575 与已保存的 cropped tar 计数一致，但是另一个文件 |
| `https://api.figshare.com/v2/articles/33130868` | Figshare | HTTP 200 | JSON | 标题 “UMIST Dataset”，大小 5927440，文件名 `umist_cropped.mat`，API 给出的 `supplied_md5` 为 `62bbcdd946c62a2b112d0062aa279caa`，许可 CC BY 4.0。描述只有 “UMIST Dataset” | 元数据 |
| `https://ndownloader.figshare.com/files/67153214` | Figshare | HEAD 被 302 到一条 10 秒过期的 S3 预签名 URL，该 HEAD 得到 HTTP 403。随后不经单独 HEAD、直接 GET 同一 Figshare URL：HTTP 200，5927440 字节 | 是。SHA-256 `ddfa985c15c4f5924be47201416abe01416bdf38b19aca6baecf59d039f51361` | 20 个 cell，共 575 个 `(112, 92)` 切片，565 个互异。与 cropped tar 的像素哈希交集为 0，转置后仍为 0 | approximate，不是 564，也不是那份 tar 的同一像素 |

CDX 查询 `images.ee.umist.ac.uk/danny/database.html`、`face.tar.gz`、`cropped.tar.gz` 以及 Roweis `data.html` 都返回 HTTP 200 的 JSON，用来选择上面的时间戳。2000 年前后的 `face.tar.gz` 捕获长度只有约 1MB，没有下载，避免把不完整对象当成数据库。

`version="precropped575"` 读取 575 张裁剪图，除以 255，不缩放。`version="figshare575"` 读取 Figshare mat。两者的元数据都写明 `not_exact_564`。`version="uncropped1012"` 仍然抛出 `DatasetUnavailable`，因为形状不统一，不能编成一个 `(n, d)` 矩阵。

## BinAlpha

论文写的是 26 个字母、每个字母随机 30 张，没有给出种子或 URL。没有找到可装入的 26×30 文件，也没有用 36 类的 Binary Alphadigits 代替。

| URL | 机构 | HTTP 或错误 | 得到文件？ | 说明 | 决定 |
| --- | --- | --- | --- | --- | --- |
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data.html` | 纽约大学，经 Internet Archive | HTTP 200 | 页面 | “Binary Alphadigits”：0–9 与大写 A–Z，每类 39 张，20×16。这是 36 类，不是 26×30 | 不替代 |
| `https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | 纽约大学 | HTTP 403 | 否 | 现网拒绝 | 未下载 |
| `https://web.archive.org/web/20240719052709id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | Internet Archive | HTTP 302 到 `https://web.archive.org/web/20240616024002id_/https://cs.nyu.edu/~roweis/data/binaryalphadigs.mat` | 否 | 后续 HEAD 为 HTTP 200，`Content-Length: 532304`，`Content-Type: text/plain`。只做了 HEAD，没有保存，也没有当 mat 装入 | 不替代 |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` | 浙江大学 | HTTP 200 | 页面 | 没有 BinAlpha 链接 | unavailable |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` | 浙江大学 | HTTP 200 | 页面 | 只有 Yale、ORL、Extended Yale B 的 mat，没有 BinAlpha | unavailable |

决定：unavailable。

## MSRA50

没有找到 1799 张、12 类的文件。邓蔡人脸页和数据页都没有这个名字。没有下载 MSRA-TD500、MSRA-B 或 MSRA10K。清华 TUNA 的 PyPI 镜像没有当作数据集去请求。

检索工具曾把 `https://people.sc.fsu.edu/~jburkardt/octave_src/exm/harvard500.mat` 的响应体存下来。那是名为 Harvard500 的 MATLAB 示例，不是 MSRA50。这次没有记录到单独的 curl HTTP 状态，文件没有保存，也不进入加载器。

决定：unavailable。

## 加载

在 `v1` 目录：

```python
from benchmarks import load_dataset

load_dataset("ORL")                         # Olivetti，(400, 1024)
load_dataset("ORL", version="att92")        # AT&T，双线性 32x32
load_dataset("ORL", version="att92_nearest")
load_dataset("ORL", version="att92_bicubic")
load_dataset("YaleB")                       # 邓蔡 mat
load_dataset("YaleB", version="cropped2414")
load_dataset("UMIST", version="precropped575")  # 575，不是 564
```

无版本的 `load_dataset("UMIST")`、`load_dataset("AR")`、`load_dataset("BinAlpha")`、`load_dataset("MSRA50")` 仍抛出 `DatasetUnavailable`。
