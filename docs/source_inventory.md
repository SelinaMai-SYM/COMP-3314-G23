> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Source material inventory

This inventory describes files present in `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP` when the historical stage began. Sizes and SHA-256 values were read from local files; missing files were not invented.

## Paper

| Item | Value |
| --- | --- |
| Path | `9736-45063-1-PB.pdf` |
| Size | 851255 bytes |
| SHA-256 | `970ee4e65fd73aca46b3f983098f87105fb7e45726b767ec7925c9188646dfaf` |
| Pages | 7 (Letter, 612x792 pt) |
| PDF metadata | Title: A Convex Formulation for Spectral Shrunk Clustering; Author: Xiaojun Chang, Feiping Nie, Zhigang Ma, Yi Yang and Xiaofang Zhou; Subject: Proceedings, The Twenty-Ninth AAAI Conference on Artificial Intelligence; Creator: TeX; Producer: pdfTeX-1.40.15 |
| Dates | CreationDate Thu Dec 11 04:46:38 2014 CST; ModDate Wed Feb 25 08:58:45 2015 CST |
| Printed pages | 2532-2538 |

Text was extracted with `pdftotext -layout`. The mathematical audit examined Equations (3)-(13), (15)-(18), (19)-(21), and Algorithm 1 in that text. No official paper code, supplements, or datasets were present in that directory.

## Course guideline

| Item | Value |
| --- | --- |
| Path | `3314 GP Guidelines.pages` |
| Size | 307852 bytes |
| SHA-256 | `3afce521f910608687484fc1cf4d0adae30bfb72dabbadde9bdaa3b62a0d3bf3` |
| Format | Apple Pages (Zip). `Metadata/Properties.plist` recorded fileFormatVersion 13.2.1 and BuildVersionHistory Template: Blank (13.2). Document timestamp: `2026-10-19T19:24:29+0800`; isMultiPage was true. |
| Preview | The embedded `preview.jpg` covered only the first page, “1. Project Task”. |

`textutil` could not convert the document. Readable text came from Snappy decompression of `Index/*.iwa` blocks, each prefixed by `0x00` and a three-byte little-endian length, followed by printable-string extraction from protobuf. Numeric rubric weights were not present in those strings; no reliable IEEE double weights in the range 0-100 were recovered from table storage. Component names and descriptions were in `Index/Tables/DataList.iwa`; see `docs/guideline_compliance.md`.

## NeurIPS 2026 template

Archive:

| Item | Value |
| --- | --- |
| Path | `Formatting_Instructions_For_NeurIPS_2026.zip` |
| Size | 20259 bytes |
| SHA-256 | `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9` |
| Contents | `neurips_2026.tex` (19118 bytes), `checklist.tex` (26167 bytes), `neurips_2026.sty` (13704 bytes), all timestamped 2026-06-23 21:48. |

Source files in the extracted `Formatting_Instructions_For_NeurIPS_2026/` directory:

| File | SHA-256 |
| --- | --- |
| `neurips_2026.tex` | `cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797` |
| `neurips_2026.sty` | `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a` |
| `checklist.tex` | `780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6` |

The adjacent `neurips_2026.aux`, `.log`, `.fls`, `.fdb_latexmk`, `.out`, `.pdf`, and `.synctex.gz` were timestamped 2026-10-19 21:33. They were local build outputs, not archive members.

The template default was `\usepackage{neurips_2026}`; its source showed the commented preprint option `\usepackage[preprint]{neurips_2026}`. Its nine-page main-conference limit, including figures, was a conference rule. The course requirements are documented separately in the compliance note.

## Other adjacent entries

- `.DS_Store` (6148 bytes) was macOS directory metadata, not course material.
- `v1/` initially contained empty `SSC_method/`, `baselines/`, `benchmarks/`, `method_extension/`, `report/`, `results/`, and `runs/` directories. Their existence did not establish completed baselines, experiments, or a report.

There was no member list, group allocation table, or Git metadata in that directory. Group 23 came only from the planned repository name `COMP-3314-G23`; the guideline did not specify the group number.
