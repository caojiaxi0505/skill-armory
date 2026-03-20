# 报告格式约定

先把 shortlist 组织成 JSON，再交给 `scripts/render_feishu_report.py` 渲染。

## 顶层必填字段

- `date`：报告日期，格式为 `YYYY-MM-DD`。
- `feed_url`：来源 feed URL。
- `papers`：入选论文数组。只要质量允许，应保持在 3-5 篇。

## 顶层可选字段

- `title`：自定义标题；不传则使用默认标题。
- `lead`：一小段对当天重点的总结。
- `notable_mentions`：0-3 篇备选论文及其简短理由。

## 论文对象

每篇入选论文应包含：

- `title`：论文原始标题。
- `url` 或 `abs_url`：arXiv 摘要页链接。
- `authors`：作者列表，适度精简即可。
- `categories`：相关 arXiv 分类。
- `why_it_matters`：一句话说明为什么值得读。
- `summary`：两句左右概括核心方法或结果。
- `key_points`：2-3 条短亮点。
- `watch_out`：一句话写清限制、风险或不确定点。
- `recommended_action`：一句话说明读者接下来该做什么。

## 最小示例

```json
{
  "date": "2026-03-20",
  "feed_url": "https://rss.arxiv.org/atom/cs.AI+cs.LG+cs.CL",
  "lead": "今天最值得关注的是能改变模型评估或训练实践的论文，而不是单纯刷榜的工作。",
  "papers": [
    {
      "title": "Example Paper",
      "url": "https://arxiv.org/abs/2603.12345",
      "authors": ["Alice", "Bob"],
      "categories": ["cs.LG", "cs.AI"],
      "why_it_matters": "它提出了一种可能改变近期实验设计的训练策略。",
      "summary": "论文给出了一种新的课程学习方法。摘要显示它在多个任务上具备一致收益。",
      "key_points": [
        "方法变化简单",
        "跨任务收益更可信",
        "适合快速复现"
      ],
      "watch_out": "摘要没有说明额外算力成本，结论仍需谨慎。",
      "recommended_action": "把它加入本周精读列表，并关注后续代码发布。"
    }
  ]
}
```

## 写作规则

- 除非另有要求，最终简报使用简体中文。
- 每个字段都尽量写得具体、有信息密度，避免“很有意思”这类空泛表述。
- 尤其是在只读了摘要的情况下，要把推断写成推断，不要伪装成事实。
- 优先使用“跟进”“精读”“观察”“复现”这类可执行动词。
- 控制整体长度，让整份报告适合在聊天窗口中快速阅读。
