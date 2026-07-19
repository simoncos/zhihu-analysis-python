# 知乎社交网络分析 / Zhihu2015

本仓库保存 2015 年课程项目及其 2026 年现代化研究工作。当前 canonical
integration branch 是 `codex/canonical-integration`：它整合了原始 Python 2
代码、Python 3 数据分析流水线、2015-2026 文献综述、专家发现实验、数据集论文
草稿和匿名化发布工具。

## 项目定位

2015 年项目从单一种子用户出发，以两层 BFS 采集知乎公开关系数据，形成五张
SQLite 表：`User`、`Following`、`Question`、`UserQuestion`、`UserTopic`。
恢复出的数据库包含约 2.6 万名完整画像用户、461 万条关注边、224 万个问题和
541 万条用户-话题记录。

这个快照不能代表今天的知乎，也不是全站随机样本；它的主要价值是作为商业化和
生成式 AI 之前、同时包含关注图与话题活动层的历史数据。

原始材料：

- [2015 英文项目报告](analysis-report/Social%20Network%20Analysis%20of%20Zhihu.pdf)
- [2015 演示文稿](analysis-report/Social%20Network%20Analysis%20of%20Zhihu_slides.pdf)
- [2015-2026 文献综述](analysis-report/literature-review-2026.md)
- [研究路线图](RESEARCH_ROADMAP.md)与[执行计划](RESEARCH_PLAN.md)
- [canonical 交接文档](docs/HANDOFF.md)

## 数据治理状态

匿名化数据集尚未正式发布。原始数据库包含可识别的用户 URL/名称，不应继续公开
传播或作为 README 中的下载入口。发布前必须执行
[`release/PUBLISHING.md`](release/PUBLISHING.md) 的隐私检查，移除旧的未脱敏
release 资产，再发布 `analysis.release` 生成的 `release_build/public/`；
`release_build/private/` 永不上传。

## Python 3 分析流水线

核心环境：

```bash
python -m pip install -r requirements.txt
```

无真实数据时，可先运行合成数据库冒烟测试：

```bash
python -m analysis.run_all --synth --out /tmp/zhihu-smoke --gof-sims 5
```

真实数据到位后：

```bash
# 数据体检、Parquet 导出、诱导图构建、七个序列的 CSN/GOF 分析
python -m analysis.run_all --db zhihu.db --out results --gof-sims 100

# 图结构、90-9-1 集中度、话题层和关注边话题同质性
python -m analysis.characterize --parquet results/parquet --out results

# 不依赖真实数据的两层 BFS 采样偏差模拟
python -m analysis.run_all --bfs-bias --out results
```

`analysis/powerlaw_fit.py` 会分别检验纯幂律与各备择分布，并直接比较截断幂律和
对数正态；只有直接比较显著时才命名胜出模型。已提交结果的来源和重跑要求见
[`results/README.md`](results/README.md)。

## 专家发现实验

文献综述 branch 新增了四代方法对比：PageRank/HITS、DeepWalk、GraphSAGE 和
异质 GraphSAGE。它是独立的可选实验，使用额外依赖：

```bash
python -m pip install -r requirements-expert.txt
python expert_finding_analysis.py zhihu.db --out expert_results
```

当前提交结果来自一次固定划分，适合作为先导结果，不应在补齐多随机种子、置信
区间和公平基线前写成最终论文结论。结果保存在
[`analysis-report/expert-finding-results/`](analysis-report/expert-finding-results/)。

## 目录地图

- `analysis/`：canonical Python 3 数据、统计、图分析、偏差模拟与发布代码
- `results/`：真实数据运行产物；不是自动测试结果
- `analysis-report/`：2015 原报告、2026 文献综述及实验归档
- `paper/`：数据集论文草稿
- `release/`：Datasheet、Dataset Card 与发布操作手册
- `crawler/`、`zhihu_analysis.py`、`zhihu_database.py`：2015 Python 2 历史代码
- `tests/`：不依赖真实数据库的核心判定与辅助函数测试

## 历史代码说明

旧 crawler 已年久失修，且存在 CSV 与 `zhihu_database.py` 无法直接衔接、topic
爬漏等已知问题。知乎前端、登录和反爬机制已经彻底变化，本仓库不计划恢复 crawler；
后续工作聚焦已有快照的可复现分析、隐私治理和研究产出。
