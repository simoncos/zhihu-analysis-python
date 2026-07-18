# 项目交接文档（Handoff）

> 更新于 2026-07-17。本文档面向在本地 session 继续本项目的开发者，记录当前状态、环境搭建、已完成工作与待办事项。所有工作在分支 `claude/literature-review-update-9vlyea` 上。

## 1. 当前状态一览

| 事项 | 状态 |
|---|---|
| 文献综述（2015–2026，32 篇引文） | ✅ 完成，`analysis-report/literature-review-2026.md` |
| 工作总结 | ✅ `analysis-report/work-summary-2026.md` |
| 6.6 幂律统计检验 | ✅ 已跑真实数据，**结论：4/5 特征为指数截断幂律**，结果在 `analysis-report/powerlaw-results/` |
| 6.1 异质网络专家发现 | ✅ 首轮实验完成，**结论：Hetero-GraphSAGE 全面最优（ρ=0.871）**，结果在 `analysis-report/expert-finding-results/` |
| 6.4 双重基线结构刻画 | ⚠️ **脚本已提交（`baseline_characterization.py`）但运行未完成**——云端后台进程中断（疑似内存或容器回收），无结果产出。需在本地重跑（见第 4 节） |
| 6.2 / 6.3 / 6.5 | ⬜ 未开始（见第 5 节） |

## 2. 环境搭建（本地）

```bash
git clone https://github.com/simoncos/zhihu-analysis-python.git
cd zhihu-analysis-python
git checkout claude/literature-review-update-9vlyea

# Python 3.11+
pip install powerlaw pandas matplotlib scipy networkx scikit-learn gensim
pip install torch torch_geometric   # 仅 expert_finding_analysis.py 需要；CPU 版即可
```

**数据获取**：数据库不在仓库中，在 GitHub release 里：

```bash
# https://github.com/simoncos/zhihu-analysis-python/releases/tag/dataset-v0
curl -L -o zhihu.zip https://github.com/simoncos/zhihu-analysis-python/releases/download/dataset-v0/zhihu.zip
# sha256: f8775f75b1e3a2f3c96dd876ac0717573fcc0622c7acdc6780f6c41a1a9e711c
unzip zhihu.zip   # -> zhihu.db (722MB, 2015-11 原始数据库)
```

验证数据完整性（应得：User 26161 / Following 4612110 / Question 2245143 / UserQuestion 1655414 / UserTopic 5414129）：

```bash
python3 -c "
import sqlite3; c = sqlite3.connect('zhihu.db')
[print(t, c.execute(f'select count(*) from {t}').fetchone()[0]) for t in ['User','Following','Question','UserQuestion','UserTopic']]"
```

## 3. 已完成实验的复现方式与关键结论

### 6.6 幂律检验（`powerlaw_analysis.py`）

```bash
python powerlaw_analysis.py zhihu.db --out powerlaw_results
```

- **结论**：粉丝/回答/赞同/感谢四项特征均拒绝纯幂律、支持指数截断幂律（最强：answer_num，p≈5×10⁻¹⁴）；唯关注数（出度）与纯幂律相容。证实 2018《数据分析与知识发现》的截断幂律论断可回溯至 2015；修正原报告的目测幂律结论。
- 脚本经合成数据双向验证（纯幂律不误报、截断数据正确识别）。
- 运行时间约几分钟；结果与图已在 `analysis-report/powerlaw-results/`。

### 6.1 专家发现四代对比（`expert_finding_analysis.py`）

```bash
python expert_finding_analysis.py zhihu.db --out expert_results
```

- 任务：仅用网络结构预测 log₁₀(1+赞同数)（标签只用于监督/评估）；60/20/20 划分；指标 Spearman ρ / NDCG@100 / P@100。
- **结论**：Hetero-GraphSAGE（关注图+用户-话题）0.871/0.845/0.60 全面第一；GraphSAGE 0.843 次之；DeepWalk/metapath 嵌入 0.745/0.751；2015 工具箱最弱（PageRank 仅 0.528）。代际排序与"内容+结构增益"均获验证。
- 已知局限（写论文前需处理）：单一种子/划分（应做多种子+置信区间）；赞同数混杂受欢迎度；GNN（监督）vs 工具箱（无监督）的不对称需在表述中明确。
- 云端 CPU 运行约 25 分钟；`--out` 目录会另存两个 `.npy` 嵌入文件（未入库）。

### 6.4 结构刻画（`baseline_characterization.py`）— **待本地重跑**

```bash
python baseline_characterization.py zhihu.db --out baseline_results
```

- 计算内容：关注网络全局拓扑（密度、互惠率、聚类系数、同配性、最大 k-core、WCC/SCC、采样最短路）、贡献集中度（Gini + 1%/9%/90% 份额，检验涂艳等 2022 的"90-9-1"论断）、话题层统计、Lorenz 曲线图。
- **注意**：云端运行时进程中断（无报错日志，疑似内存不足或容器回收）。可疑点是 `networkx` 的 `from_scipy_sparse_array` + `core_number`（313 万边图会构建完整 nx 图对象，内存开销大）。若本地内存有限，可将 k-core 部分改为纯 scipy 迭代剥离实现，或换 `igraph`。其余部分（三角计数、采样 BFS）均为 scipy 稀疏运算，应无问题。
- 跑通后：结果 markdown + `lorenz_curves.png` 复制到 `analysis-report/baseline-results/`，并更新综述 6.4 节（当前 6.4 节仍是"建议"状态）与 `work-summary-2026.md` 路线表。

## 4. 待办路线（按优先级）

1. **重跑 6.4 并写入结果**（上节）。
2. **6.1 增强**：多种子置信区间；按话题分组的专家排序（TUEF 式 per-topic 评测）；HGB 式调优基线说明。
3. **6.3 影响力回溯**（数据独特性最强的方向）：取 2015 年 Net10k/Net50k 头部用户名单（可从 `zhihu.db` 现算），补爬其当前状态（留存/停更/粉丝数），检验早期结构位置对十年后命运的预测力。理论框架：Burtch et al. 2024 的"社交嵌入度缓冲论"+ Zhou & Mi 2024 推拉迁移 + 涂艳等 90-9-1。注意知乎现行反爬与合规。
4. **6.2 三代方法任务扩展**：在链接预测、用户聚类两个任务上复用 6.1 已建的图与嵌入。
5. **6.5 话题图治理**：话题共现图 + LLM 语义聚类（参照 Quora 话题合并研究 Mathew et al. 2020）。
6. **文献侧待办**：CNKI 系统检索（2021 年后知乎商业化/内容质量/流失主题）；核实两处存疑引用（《数据分析与知识发现》2018, 2(4) 的作者名单；ISR 信息流整合论文的卷期页码）；关注"知乎 × 国产 LLM 冲击"是否有新发表（截至本次检索为空白，是 6.4 论证的核心机会）。

## 5. 文件地图

```
├── HANDOFF.md                        # 本文档
├── powerlaw_analysis.py              # 6.6 幂律检验（✅ 已出结果）
├── expert_finding_analysis.py        # 6.1 专家发现四代对比（✅ 已出结果）
├── baseline_characterization.py      # 6.4 结构刻画（⚠️ 待本地重跑）
├── analysis-report/
│   ├── literature-review-2026.md     # 文献综述（6.1/6.6 节含实证结果，6.4 节待更新）
│   ├── work-summary-2026.md          # 工作总结 + 路线表
│   ├── powerlaw-results/             # 6.6 结果表 + 5 张 CCDF 图
│   ├── expert-finding-results/       # 6.1 结果表
│   └── Social Network Analysis of Zhihu.pdf   # 2015 原报告
├── zhihu_schema.sql / zhihu_database.py / zhihu_analysis.py   # 2015 原代码（Python 2）
└── crawler/                          # 2015 爬虫（已失效，README 有说明）
```

## 6. 其他注意事项

- 新脚本均为 Python 3；2015 年的 `zhihu_analysis.py` 是 Python 2，仅作历史参照。
- 综述的引用置信度分三级（三票核验 / 原始来源提取 / 间接来源），见综述第 7 节；投稿前对二、三级引用逐一核对原文。
- 数据集为 BFS 单种子爬取（种子 zhao-che），存在种子偏差；所有结论表述均应限定于"种子邻域快照"或做偏差稳健性分析。
- release 数据仅限研究使用；补爬新数据时注意知乎服务条款与个人信息合规。
