# 材料盘点

盘点范围是目录 `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP` 在本阶段开始时实际存在的文件。下面的大小和 SHA-256 来自本机读取，没有补造文件。

## 论文

| 项 | 值 |
| --- | --- |
| 路径 | `9736-45063-1-PB.pdf` |
| 大小 | 851255 字节 |
| SHA-256 | `970ee4e65fd73aca46b3f983098f87105fb7e45726b767ec7925c9188646dfaf` |
| 页数 | 7（Letter，612×792 pt） |
| PDF 信息 | Title: A Convex Formulation for Spectral Shrunk Clustering；Author: Xiaojun Chang, Feiping Nie, Zhigang Ma, Yi Yang and Xiaofang Zhou；Subject: Proceedings, The Twenty-Ninth AAAI Conference on Artificial Intelligence；Creator: TeX；Producer: pdfTeX-1.40.15 |
| 时间 | CreationDate Thu Dec 11 04:46:38 2014 CST；ModDate Wed Feb 25 08:58:45 2015 CST |
| 正文页码 | 2532–2538 |

正文用 `pdftotext -layout` 抽出。公式审计依据的是该文本中的式 (3)–(13)、式 (15)–(18)、式 (19)–(21) 和 Algorithm 1。该目录里没有论文的官方代码、补充材料和数据文件。

## 课程指南

| 项 | 值 |
| --- | --- |
| 路径 | `3314 GP Guidelines.pages` |
| 大小 | 307852 字节 |
| SHA-256 | `3afce521f910608687484fc1cf4d0adae30bfb72dabbadde9bdaa3b62a0d3bf3` |
| 格式 | Apple Pages（Zip）。`Metadata/Properties.plist` 中 `fileFormatVersion` 为 13.2.1，`BuildVersionHistory` 为 Template: Blank (13.2)。文档时间戳 `2026-10-19T19:24:29+0800`。`isMultiPage` 为真 |
| 预览 | 包内 `preview.jpg` 只覆盖第 1 页「1. Project Task」 |

`textutil` 不能把该文件转成文本。可读正文来自对 `Index/*.iwa` 的 Snappy 解压（每块以 `0x00` 加 3 字节小端长度开头），再从 protobuf 里取出可打印字符串。评分表的数字权重没有出现在这些字符串里，表存储里也没有读出 0–100 范围内可靠的 IEEE 双精度权重。组件名称和说明文字在 `Index/Tables/DataList.iwa` 中，见 `docs/guideline_compliance.md`。

## NeurIPS 2026 模板

压缩包：

| 项 | 值 |
| --- | --- |
| 路径 | `Formatting_Instructions_For_NeurIPS_2026.zip` |
| 大小 | 20259 字节 |
| SHA-256 | `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9` |
| 包内文件 | `neurips_2026.tex`（19118 字节）、`checklist.tex`（26167 字节）、`neurips_2026.sty`（13704 字节），时间戳均为 2026-06-23 21:48 |

已解压目录 `Formatting_Instructions_For_NeurIPS_2026/` 中的源文件：

| 文件 | SHA-256 |
| --- | --- |
| `neurips_2026.tex` | `cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797` |
| `neurips_2026.sty` | `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a` |
| `checklist.tex` | `780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6` |

同目录下的 `neurips_2026.aux`、`.log`、`.fls`、`.fdb_latexmk`、`.out`、`.pdf`、`.synctex.gz` 时间戳为 2026-10-19 21:33，不在 zip 内，是本地编译产物。

模板源文件默认是 `\usepackage{neurips_2026}`。`preprint` 选项在 `neurips_2026.tex` 里以注释形式给出：`\usepackage[preprint]{neurips_2026}`。模板自己写的 NeurIPS 主会页数上限（含图最多 9 页）是会议规则，课程指南另有说法，见合规文档。

## 同目录中的其他条目

- `.DS_Store`（6148 字节）：macOS 目录元数据，不是课程材料。
- `v1/`：本阶段开始时已有空目录 `SSC_method/`、`baselines/`、`benchmarks/`、`method_extension/`、`report/`、`results/`、`runs/`。这些空目录不表示基线、实验或报告已经完成。

本目录没有组员名单、组别表格或 Git 元数据。组别 Group 23 只来自阶段计划里的仓库名 `COMP-3314-G23`，指南原文没有写组号。
