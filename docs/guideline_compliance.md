# 课程要求对照

来源是 `3314 GP Guidelines.pages` 解压后的正文，以及 NeurIPS 2026 模板源文件。组员姓名在这些材料里不存在。组别 Group 23 只从阶段计划中的仓库名 `COMP-3314-G23` 推断，需要人工确认。本文件不给评分权重。

## 已读到的要求

### 选题与分析

- 选择并研读一篇与课程主题相关的机器学习论文，优先来自 ICML、ICLR、NeurIPS、AAAI、CVPR、ACL、JMLR、Machine Learning、TMLR，以及 IEEE TNNLS、TPAMI、TIP、TCSVT。不确定时先问教师或助教。
- 说明问题表述、动机、方法和主要贡献。
- 把方法连接到课程概念。
- 讨论论文中的实验设置和结果，以及哪些证据支持其结论。
- 批判分析假设、优点、局限，以及可能的改进或扩展。
- 本组论文是 Chang 等人，AAAI 2015，*A Convex Formulation for Spectral Shrunk Clustering*。AAAI 在指南的 AI/applied 会议列表中。

### 书面报告

指南里有两处并列的页数说法，这里都照录：

1. Deliverables：Written Report（3–4 pages, prepared in LaTeX），并列出建议内容：问题与动机、方法与课程概念、实验设置与结果的讨论、批判分析、自己的见解或扩展；若做复现，还要写实现范围、与原文结果的比较、遇到的困难，以及代码仓库链接。引用要清楚，论文中的图表和本组自己的结果要分开标注。
2. Report Submission：No hard requirements on the template and page limit, but a suggested template will be in NeurIPS style。紧接着又写 Maximum 4 pages main text (references and appendix excluded)。使用 preprint 选项，即 `\usepackage[preprint]{neurips_2026}`，并列出组员姓名和单位。只收 PDF。文件名 `Group_xx`。若有复现代码，在报告中给出公开 GitHub 链接，不必上传代码包。

本阶段采用的读法：3–4 页 LaTeX 是建议篇幅；同一节明确写了没有硬性模板和页数限制。相邻的 “Maximum 4 pages main text” 一并记录，留待写报告时由课程组确认，这里不把它改写成扣分规则。NeurIPS 模板自身的 9 页主会限制是会议说明，不是这门课的页数上限。

报告截止：2026-11-29 23:59（作业打开时间为 2026-10-13 00:00，Due 显示 Sunday, 29 November 2026, 11:59 PM）。指南写明报告截止晚于幻灯片，是为了留时间打磨报告。

组员姓名和单位：**材料中没有，必须确认后才能写入报告。** 不要编造姓名、邮箱或基金号。

### 可选复现加分

- 可以复现论文中的数值、图或实验，完整或部分都可以。
- 需要说明工作范围，并与论文结果比较，讨论差异和困难。
- 在没有公开官方代码时从零实现，会在加分评估里得到额外考虑。本目录没有官方代码。
- 若提交代码，放在公开 GitHub 仓库，包含 `README.md`（论文信息、环境、运行方法、复现结果），并区分自己的代码和复用代码。
- 加分文字是：up to 10 additional percentage points, assessed separately from the base score。这是单独评估的最多 10 个百分点数，不是基础分内部的权重。

### 展示

- 每组 9 分钟讲解加 3 分钟问答，成员都要参加。
- 内容包括论文概览、方法与课程概念、证据与结果、批判分析、小组收获；若做了复现，在时间内简要报告做法、结果、比较和教训。
- 幻灯片截止：2026-11-15 23:59（打开时间 2026-10-13 00:00）。文件名 `Group_xx`。截止后不能修改。
- **本阶段不制作幻灯片。**

### 评分表里读到的文字

表头是 Component、Weight、Description。读到的组件和说明如下。Weight 列的数字没有可靠读出，所以这里不写百分比。

| 组件 | 说明（来自表格字符串） |
| --- | --- |
| Paper Understanding | Accuracy and depth in explaining the problem, methods, contributions, and connections to course topics |
| Critical Analysis & Insight | Thoughtful interpretation of the paper's evidence, evaluation of assumptions and limitations, and well-supported insights or proposed extensions |
| Written Report | Clarity, organization, coherence, and appropriate use of figures and citations |
| Presentation & Q&A | Clarity, structure, effective use of visuals, and quality of responses during Q&A |

字符串前面的 `f`、`N`、`Q` 是 protobuf 长度字节，不是正文。

### 其他日程与链接（指南原文中的 URL）

- 小组：3–4 人。组建截止 2026-09-17 23:55。逾期随机分组。
- 选题：约 2026-09-23 至 2026-09-28 23:59，先到先得，各组论文不重复。
- GPU 农场说明：`https://ai.hku.hk/research/major-facilities?view=article&id=130&catid=24`
- 小组选择：`https://moodle.hku.hk/mod/choicegroup/view.php?id=4279779`
- NeurIPS 2026 Call for Papers：`https://neurips.cc/Conferences/2026/CallForPapers`
- 另外两个 Moodle URL 和两个作业链接也在文件里（`view.php?id=4303930`、`4324469`、`4324470`、`4324471`）。它们分别对应指南中的表格/日程/两次提交，具体哪一个 id 对应哪一次提交要以 Moodle 页面为准。

## 本阶段做到和没做到的事

| 要求 | 状态 |
| --- | --- |
| 选定 AAAI 2015 SSC 论文并核对公式 | 已写 `docs/ssc_mathematical_audit.md` |
| 从零实现 SSC，标签不参与学习 | 已实现于 `SSC_method/` |
| ACC（匈牙利一对一）和几何平均 NMI | 已实现于 `benchmarks/metrics/`（共享，不是数据集），并有小列联表测试 |
| 复现差异记录 | 已写 `docs/reproduction_deviations.md`（方法差异；还没有实验数字） |
| 书面报告、checklist、PDF | 未写。另一阶段负责 |
| 幻灯片 | 未做 |
| 公开 GitHub、README 中的运行结果 | 代码 README 已有；仓库发布和实验结果不在本阶段 |
| 组员姓名与单位 | 待确认 |
| 评分权重 | 未从指南读出，不填写 |
