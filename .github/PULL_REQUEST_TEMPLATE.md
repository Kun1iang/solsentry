## 变更说明

<!-- 这个 PR 解决什么问题？关联的 issue：Closes #... -->

## 变更类型

- [ ] feat：新功能 / 新规则
- [ ] fix：缺陷 / 误报
- [ ] docs：文档
- [ ] test：测试
- [ ] chore：CI / 构建 / 发布

## 规则变更检查（如适用）

- [ ] 新增 vulnerable 样例
- [ ] 新增 clean 反例
- [ ] 覆盖命中 / 未命中 / 抑制
- [ ] 更新 `docs/rules.md`
- [ ] 更新 `CHANGELOG.md`

## 验证

```text
# 粘贴实际命令与输出
python -m unittest discover -s tests -v
```

## 评审清单

- [ ] 只解决一个 issue
- [ ] 没有引入运行时第三方依赖
- [ ] 没有提交密钥、真实地址或未脱敏数据
- [ ] 文档与代码一致
- [ ] 报告格式仍可解析（JSON / SARIF）
