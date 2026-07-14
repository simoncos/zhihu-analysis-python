# 知乎社交网络分析

## 简介

项目包含基于[zhihu-python](https://github.com/egrcc/zhihu-python)的多线程爬虫，数据I/O（`SQLite`,`csv`），以及基于用户关注网络的分析（使用[networkx](https://networkx.github.io/)作为图算法库）。

注：[本项目所使用的zhihu-python](https://github.com/simoncos/zhihu-analysis-python/tree/master/crawler)已与原版存在差异

## 详细内容

- [Dataset](http://pan.baidu.com/s/1bos5RqR)
- 中文
	- [知乎社交网络分析（上）：基本统计](http://www.jianshu.com/p/60ffb949113f)
	- [知乎社交网络分析（下）：关注网络](http://www.jianshu.com/p/3b2a1895a12d)
- English
	- [Project Report](https://github.com/simoncos/zhihu-analysis-python/tree/master/analysis-report)

## 文件说明

- `crawler`文件夹：爬虫部分，以广度优先策略爬取知乎数据，并以csv格式储存（这一部分代码目前版本有误，爬到的数据文件与`zhihu_database.py`无法衔接，此外存在topic爬漏的问题，待修复）
- `zhihu_schema.sql`：SQLite数据库的schema
- `zhihu_database.py`：将csv中的数据导入至数据库中
- `zhihu_analysis.py`：从数据库中提取数据并进行分析

## 爬虫部分已知问题及（可能）原因

**爬虫部分已年久失修，由于这个project的重点不在于爬虫，所以不打算更新了，还请谨慎入坑:)**

- zhihu-python InsecureRequestWarning | urlib
- topic.py 会爬漏话题标签 | 原因未知

## 未来计划

之后考虑利用已有数据集再做一些分析，比如用户聚类、用户-话题-问题网络之类。

研究方向调研与执行计划见 [`RESEARCH_ROADMAP.md`](RESEARCH_ROADMAP.md) 与 [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md)。

## 新版分析流水线（2026，Python 3）

`analysis/` 包实现了 Phase 0（数据体检）+ 项目一（严谨幂律检验、BFS 采样偏差模拟）：

```bash
pip install -r requirements.txt

# 完整流水线（需要 zhihu.db 放在仓库根目录）
python -m analysis.run_all --db zhihu.db --out results

# 采样偏差模拟（不需要真实数据）
python -m analysis.run_all --bfs-bias --out results

# 无数据时用合成数据库做冒烟测试
python -m analysis.run_all --synth --out /tmp/smoke --gof-sims 20
```

输出：`results/health_check.md`（数据体检）、`results/powerlaw_results.md`（CSN 幂律拟合 + 与对数正态等备择分布的似然比检验）、`results/figures/`（各特征 CCDF 图）、`results/bfs_bias_simulation.md`（采样偏差实验）。
