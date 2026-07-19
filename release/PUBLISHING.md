# 发布操作手册：Zenodo + Hugging Face

前置：`zhihu.db` 就位后运行
`python -m analysis.release --db zhihu.db --out release_build`。
产物：`release_build/public/`（5 个 parquet + stats.json，可发布）、
`release_build/private/`（ID 映射，**永不发布**，本地加密备份）。

## 发布前检查清单

> **当前阻断项（2026-07-19）**：旧 `dataset-v0/zhihu.zip` 下载入口仍可访问。
> 根据项目交接记录，该附件包含未脱敏的原始数据库。在它被限制或删除之前，
> 不得宣称匿名数据集已经发布，也不要继续传播该 URL。

- [ ] 核对 stats.json 与 2015 报告记录数一致，回填 DATASHEET/DATASET_CARD 中的 [TODO]
- [ ] 抽样人工检查 users.parquet：确认无 user_url/显示名残留
- [ ] 确认 edges/user_questions 中的 id 均为整数（无原始字符串泄漏）
- [ ] private/ 目录不在任何上传路径中；加入 .gitignore（已配置 release_build/）
- [ ] 用公开文件反向自查：能否用"计数指纹"轻易定位某个名人？在 DATASHEET
      残余风险一节如实记录结论（已做：92.4% 用户五元组唯一，已写入 DATASHEET）
- [ ] **立即限制或删除 GitHub release `dataset-v0` 的 zhihu.zip 附件**（内含原始
      user_url/显示名；不能等到正式发布后再处理，否则匿名化形同虚设）
- [ ] 若百度盘分享仍有效，关闭旧分享链接，README 指向 Zenodo/HF

## Zenodo（正主，出 DOI）

1. zenodo.org 登录（可用 GitHub 账号）→ New upload
2. 上传 `public/` 下所有文件 + DATASHEET.md
3. 元数据：Resource type = Dataset；标题 "Zhihu2015: A 2015 Snapshot of the
   Zhihu Follow Network"；作者、关键词（social network, Zhihu, CQA, graph）；
   License = CC BY 4.0；关联 GitHub 仓库 URL（Related works: IsSupplementTo）
4. 发布 → 获得 versioned DOI + concept DOI（引用格式用 concept DOI）
5. 回填 DOI 到：DATASET_CARD.md、仓库 README、CITATION.cff、论文草稿

## Hugging Face（镜像，负责被发现）

1. `pip install huggingface_hub` → `huggingface-cli login`
2. 创建 dataset repo（建议 `simoncos/zhihu2015`）
3. 上传 `public/` 文件 + 将 DATASET_CARD.md 作为 README.md（YAML 头保留）
   + DATASHEET.md
4. 确认 Dataset Viewer 能预览 parquet；勾选正确的 license 标签

## GitHub 收尾

- README 增加 Dataset 小节：Zenodo DOI badge + HF 链接，替换失效的百度盘链接
- 添加 CITATION.cff（`cffinit` 生成，datatype: dataset）
- 打 tag（如 `dataset-v1.0`）对应 Zenodo 版本

## 版本策略

修订（如接受 takedown 请求、修复导出 bug）→ Zenodo New version（同一
concept DOI 下），HF 同步覆盖并在卡片 Changelog 记录。
