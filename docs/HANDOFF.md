# Session 交接文档（2026-07-15）

> 供后续 session / 协作者快速接手。分支：`claude/legacy-project-analysis-ior8d5`
> （所有工作都已提交推送到该分支，master 未动）。

## 一句话现状

2015 年的知乎关注网络数据集已完成**匿名化发布准备 + 全部实证分析 +
数据集论文草稿**，目标 ICWSM 2027 dataset track（截稿 2027-01-15）；
剩余工作全部依赖仓库所有者的外部操作（Zenodo/HF 发布、删旧数据）或
收尾工程（LaTeX 化）。

## 项目演进脉络（按时间）

1. **调研阶段**：分析老项目 → 文献综述 → 研究方向清单
   （`RESEARCH_ROADMAP.md`）→ 执行计划（`RESEARCH_PLAN.md`）；
2. **方向确定**：用户选定"严谨幂律重访 + 社交/兴趣社区对齐"两个方向，
   否决了与 ZhihuRec 的纵向对比（口径不可比）；
3. **战略调整**：使用情况调查发现数据集十年传播零引用 → 用户决定优先做
   **数据集正式发布 + 数据集论文**（项目零），原项目一的分析成果并入论文;
4. **数据到位**：用户经 GitHub release `dataset-v0` 上传原始 zhihu.db
   （百度盘从本环境不可达）→ 全部真实数据分析完成 → 论文实证部分定稿。

## 关键结论（已写入论文，勿重复计算）

- **分布检验**：7 个序列（5 个画像计数 + 诱导子图出/入度）无一是纯幂律；
  6 个被 GOF bootstrap 直接拒绝；活动类计数与诱导度偏对数正态，
  关注/粉丝数偏截断幂律。推翻 2015 报告"全部显著幂律"的结论；
- **BFS 采样偏差**（模拟，不依赖真实数据）：画像计数分布使入度指数被低估
  约 0.6（BFS 过采高度数节点）；诱导子图度净偏差反而较小；
- **图结构**：诱导子图 26,161 节点 / 313 万边；巨型 SCC 覆盖 98.0%；
  采样平均最短路 2.62；互惠率 14.4%（< Twitter 的 22.1%）；同配性 −0.19；
- **话题层**：68.3% 用户有话题（53 个孤儿 ID 是爬取残留）；前 1% 标签占
  54.5% 记录量；问题级话题覆盖 99.3%（当年担心的爬漏其实很小）；
- **同质性演示实验**：被关注对话题 Jaccard 是随机对的 1.83 倍；
- **匿名化风险量化**：92.4% 用户五元组计数指纹唯一 → 只防随手识别，
  不防持有 2015 年辅助数据的对手（datasheet 已如实披露）；
- **相关工作**：存在 CANE/CENE 1 万用户知乎基准（2016-17）→ 论文定位已
  软化为"最大、文档最全、唯一带问题/话题层"。

## 文件地图

| 路径 | 内容 |
|---|---|
| `RESEARCH_ROADMAP.md` / `RESEARCH_PLAN.md` | 方向清单 / 执行计划（含项目零） |
| `docs/RESEARCH_REVIEW.md` | 详细调研报告（文献综述 + 方法批判 + 使用调查） |
| `docs/HANDOFF.md` | 本文档 |
| `analysis/` | Python 3 流水线：data_io / health_check / powerlaw_fit / bfs_bias / characterize / release / synth_db / run_all |
| `results/` | 真实数据结果：health_check.md、powerlaw_results.{md,csv}、characterization.json、bfs_bias_simulation.{md,csv}、figures/（7 张 CCDF） |
| `paper/zhihu2015_dataset_paper.md` | 论文草稿（markdown，实证部分定稿） |
| `release/` | DATASHEET.md、DATASET_CARD.md（HF）、PUBLISHING.md（发布手册+检查清单） |
| `release_build/`（**不在 git**） | public/（匿名化 5 parquet + stats.json，待发布）；private/（ID 映射，永不发布） |

## 数据位置（重要）

- 原始 `zhihu.db`（722MB）：本 session 的 scratchpad 内（容器回收即消失）+
  GitHub release `dataset-v0` 的 zhihu.zip（SHA256=f8775f75…）；
- `release_build/` 在仓库工作目录但被 gitignore——**容器回收后需重新生成**：
  `python -m analysis.release --db zhihu.db --out release_build`（种子固定，
  输出确定性可复现，ID 映射也相同）；
- 复现全部分析：`pip install -r requirements.txt` 后
  `python -m analysis.run_all --db zhihu.db --out results --gof-sims 100`
  （GOF 全跑约 30 分钟）+ `python -m analysis.characterize` +
  `python -m analysis.run_all --bfs-bias`。

## 待办清单（按依赖顺序）

**只有仓库所有者能做：**
1. Zenodo 发布拿 DOI + HuggingFace 上传（按 `release/PUBLISHING.md`，
   发布物 = `release_build/public/`）；
2. **删除 GitHub release `dataset-v0` 的 zhihu.zip**（原始未脱敏数据公开
   可下载，不删则匿名化失效）；确认百度盘旧分享已死/关闭；
3. 核实 ICWSM 2027 dataset track 的双盲细则（icwsm.org 被本环境代理屏蔽）；
4. 审阅论文 §10 伦理声明（承认违反当年 ToS 的表述需作者本人认可）。

**任何 session 可继续：**
5. DOI 回填论文/数据卡/README + 添加 CITATION.cff；
6. 论文转 AAAI 双栏 LaTeX，7 张 CCDF 选 2-3 张，摘要压缩；
7. （论文后）原项目二：社交社区 × 兴趣社区对齐——§6.4 的 1.83× 同质性
   就是它的先导结果，方法设计在 RESEARCH_PLAN.md T2.1–T2.4。

## 环境注意事项

- 本云环境网络白名单较窄：pan.baidu.com、api.openalex.org、
  api.semanticscholar.org、icwsm.org 均被代理 403；github.com、pypi 可用；
- GitHub 操作走 MCP 工具（无 gh CLI）；仓库范围限定 simoncos/zhihu-analysis-python；
- 依赖见 requirements.txt；powerlaw 包本版本 `KS()` 无参调用有 bug，
  代码里已改用 `.D` 属性，勿回退。
