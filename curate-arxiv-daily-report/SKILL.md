---
name: curate-arxiv-daily-report
description: 从 cs.AI+cs.LG+cs.CL 的 arXiv Atom feed 中生成每日论文简报，按研究价值排序，筛选最值得读的 3-5 篇论文，并产出供定时任务推送到飞书的日报 payload。适用于生成 arXiv 每日报告、筛选最新 AI/ML/NLP 论文、总结当天 arXiv feed，或为定时推送生成论文精选内容。
---

# ArXiv 每日精选报告

## 概览

从 arXiv 的 AI/ML/NLP feed 生成每日研究简报。先把 Atom feed 归一化，再按研究价值打分，筛出最强的 3-5 篇候选，并渲染成适合飞书阅读、可交给定时任务使用的日报内容。

默认使用简体中文撰写最终简报，除非用户明确要求其他语言。论文分析必须综合标题、摘要与 PDF 正文内容，必要时再参考分类和作者信息辅助判断；最终排序和入选结论不能只基于摘要或元信息得出。

## 快速开始

1. 获取或接收 `https://rss.arxiv.org/atom/cs.AI+cs.LG+cs.CL` 的 Atom feed。
2. 在可联网时运行 `python3 scripts/parse_arxiv_atom.py --source-url https://rss.arxiv.org/atom/cs.AI+cs.LG+cs.CL --pretty --output results/arxiv-feed-$(date +%F).json`；如果已有保存好的 XML，则使用 `--input`。优先按日期写入文件，避免覆盖历史结果；在自动化环境里，优先使用调度日期作为文件名，而不是直接打印到 terminal，避免长 JSON 占用上下文。
3. 先通览 `arxiv-feed-YYYY-MM-DD.json` 中的 `title` 和 `abstract`，建立初始候选池。
4. 根据分析需要，从候选论文的 `pdf_url` 下载 PDF，并按日期保存到本地目录，例如 `results/pdfs/2026-03-20/`。不要只保留链接而不落盘。
5. 优先使用环境中可用的 `pdf` skill 阅读已下载的 PDF 正文；如果运行环境没有该 skill，就使用等效 PDF 工具读取正文，但不要跳过正文分析。
6. 阅读 `references/evaluation-rubric.md`，按统一标准打分并处理平分情况，筛出最值得读的 3-5 篇论文。
7. 阅读 `references/report-contract.md`，组装结构化日报 payload。
8. 运行 `python3 scripts/render_feishu_report.py --input report.json` 渲染最终消息。
9. 将渲染后的 `title` 和 `markdown` 作为定时任务的标准输入内容。如果当前环境暴露了实际的调度入口或飞书发送工具，就调用它；否则返回 ready-to-send payload，并明确说明这是供定时任务使用的未发送内容。

## 工作流

1. 归一化 feed。
   优先使用 `scripts/parse_arxiv_atom.py` 把 Atom XML 转成结构稳定的 JSON，至少包含 `title`、`abstract`、`authors`、`categories`、`published`、`updated`、`abs_url` 和 `pdf_url`。默认把结果保存为文件，再从文件中继续分析，避免把全量原始数据直接灌进上下文。
2. 先通览，再建立候选池。
   先浏览整个 feed 的标题和摘要，建立初始候选池；不要在还没完成这一轮通览之前，就直接进入逐篇正文分析。
3. 下载 PDF 到本地目录。
   根据候选论文的 `pdf_url` 下载 PDF，并按日期归档保存，便于后续阅读、复查和重跑。不要只保留链接而不落盘。
4. 优先调用 `pdf` skill 阅读 PDF。
   如果运行环境提供 `pdf` skill，优先用它提取和阅读已下载的 PDF 正文；如果没有，再退回到等效 PDF 读取工具。无论使用哪种方式，都要确保分析建立在正文内容之上，而不是只依赖摘要。
5. 结合正文完成分析与评分。
   对进入排序和取舍范围的论文，必须阅读 PDF 正文，并结合标题、摘要与正文内容完成分析和评分。
6. 按价值打分，而不是按热度追逐。
   依据 `references/evaluation-rubric.md` 评分。优先看“是否符合当前研究方向”，再看新颖性、可信度与杠杆价值；惩罚热门但偏离主线的论文、刷榜式增量、表述模糊或价值过窄的工作。
7. 在可能的情况下选择 3-5 篇。
   如果当天质量很强，默认选 5 篇；如果整体质量一般，可以降到 3 或 4 篇。如果连 3 篇都不值得推荐，就坦诚说明当日 feed 偏弱，不要为了凑数加入低价值论文。
8. 保持题材覆盖。
   在质量接近时，尽量覆盖 `cs.AI`、`cs.LG` 和 `cs.CL`。只有当某一方向明显强于其他方向时，才允许结果集中在单一类别。
9. 解释推荐理由。
   对每篇入选论文，都要说明它为什么值得读、核心做了什么、需要注意什么、以及读者下一步应该做什么。
10. 渲染成定时任务可消费内容。
   先按 `references/report-contract.md` 生成结构化 JSON，再用 `scripts/render_feishu_report.py` 渲染。渲染后的结果就是定时推送到飞书时应使用的标准消息体。
11. 不要编造调度或发送接口。
   使用运行环境里真实存在的调度器或飞书发送 connector。如果 connector 缺失，就遵循 `references/delivery-playbook.md`，停在 ready-to-send payload，而不是凭空假设不存在的调度或推送 API。

## 决策规则

1. 优先考虑当前 feed 批次中的最新论文。
2. 优先选择方法论或概念层面有明确增量的工作。
3. 优先选择本周内可能影响研究团队“读什么、做什么、跟踪什么”的论文。
4. 除非“同题对比”本身就是报道重点，否则避免同时选择多篇高度相似的论文。
5. 对不确定判断要明确标记为推断，不要写成事实。
6. 每条推荐都要附上准确的 arXiv 摘要页链接。

## 参考文件

按需读取：

- `references/evaluation-rubric.md`：评分维度、阈值和 tie-break 规则。
- `references/report-contract.md`：结构化报告 schema 和写作约束。
- `references/delivery-playbook.md`：定时推送到飞书的方式和失败兜底规则。
- 环境里如果存在 `pdf` skill，优先使用它完成 PDF 正文读取与提取；如果不存在，再使用等效 PDF 工具。

## 质量要求

1. 简报必须足够短，适合在聊天窗口中快速浏览。
2. 优先写对决策有帮助的话，避免空泛赞美。
3. 要区分“标题、摘要或 PDF 正文中明确写了什么”和“你基于这些内容做出的推断”。
4. 除非工具明确返回成功，否则不要声称定时任务已经成功推送到飞书。
