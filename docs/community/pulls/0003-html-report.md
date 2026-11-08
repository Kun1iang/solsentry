# PR #3 feat: 独立 HTML 报告与风险评分

- 状态：merged
- 作者：姚坤良
- 评审：维护者自检 + 自动检查
- 合并：2026-10-16
- 关联 issue：#3
- 目标分支：`develop`

## 变更

- 新增 `render_html()`：风险分、等级分布、证据、修复建议、按等级筛选；
- 风险分权重：critical=30、high=12、medium=4、low=1；
- 新增 `docs/assets/scan-report.html` 示例；
- 新增 `tests/test_reports.py` 的 HTML 结构测试。

## 评审意见

- 所有动态文本必须 `html.escape`，尤其是源码证据；
- 空结果要有正常状态；
- 页脚注明“静态分析不能替代人工审计”；
- 不引入外部 CDN 或字体。

## 验证

```text
$ python -m unittest discover -s tests -v
Ran 22 tests in 1.1s
OK
```

## 合并后

合并到 `develop`；生成 1440px 截图用于课程报告。
