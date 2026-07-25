# 执行计划：数据集发布与论文 → 严谨幂律重访 → 社交/兴趣社区对齐

> 承接 RESEARCH_ROADMAP.md 中的方向 A（项目一）与 B（项目二）。
> 两个项目共用 Phase 0 的地基，项目一是项目二的热身。
>
> **2026-07 调整：新增"项目零：数据集正式发布 + 数据集论文"，优先级最高。**
> 理由：使用情况调查显示数据集十年传播无归属（见 docs/RESEARCH_REVIEW.md §6.1）；
> 项目一的全部产出（严谨拟合 + 偏差分析）可以直接作为数据集论文的
> characterization 章节，两者合并为一篇 dataset paper 性价比最高。

## 项目零：数据集发布 + 数据集论文（就绪度：代码硬化已实施，完整验证、隐私治理与 canonical 重跑未完成）

- 发布流水线：`analysis/release.py`（假名化：用户/问题 ID 随机整数化、
  删除显示名；映射表独立安全目录保留不发布）——已实现，修正版待合成数据验证；
- 文档三件套：`release/DATASHEET.md`（Gebru 框架）、`release/DATASET_CARD.md`
  （HF 数据卡）、`release/PUBLISHING.md`（Zenodo+HF 操作手册与发布前检查清单）；
- 论文草稿：`paper/zhihu2015_dataset_paper.md`（目标 ICWSM dataset track；
  旧 inferential headline 已撤下，§6/§7 等待 manifested canonical 重跑）；
- 收尾顺序：先限制/删除旧未脱敏 release 资产 → 私下恢复 `zhihu.db` →
  `release.py` 出 stats → canonical `run_all.py` 与 `characterize.py` 重跑 →
  发布前检查清单 → Zenodo/HF → 投稿。

## Phase 0：数据与环境地基（预计 1~2 天）

**P0.1 私下恢复数据**
- 从维护者本地存档恢复 `zhihu.db`；不要继续传播旧的未脱敏下载入口；
- 按报告核对记录数：User ≈ 26,161，Following ≈ 4.6M，Question ≈ 2.2M，
  UserQuestion ≈ 1.7M，UserTopic ≈ 5.4M。对不上要先查明原因（当年爬漏 topic 的
  已知问题会影响项目二的话题覆盖率，需要量化缺失比例）。

**P0.2 环境与代码迁移**
- Python 3.11+，依赖：`pandas`、`python-igraph`、`powerlaw`、`matplotlib`、
  `scipy`；项目二追加 `sentence-transformers`（bge-large-zh 或同类中文 embedding）、
  `scikit-learn`、`leidenalg`。
- 将 `zhihu_analysis.py` 迁到 Python 3（print 函数、`zip()` 迭代器、`cmp` 排序、
  networkx API 变更），拆成模块：`data_io.py`（SQLite → DataFrame/graph）、
  `stats.py`、`network.py`。
- 一次性把全图导出为中间格式（edges.parquet + user 属性表），后续所有分析不再碰
  SQLite。

**P0.3 数据体检（写成一个 notebook，作为两个项目共享的附录）**
- 去重、自环、悬挂引用（Following 中指向 User 表外的 followee 占比——按报告应
  占绝大多数，只有 2.6 万节点间的诱导子图是"完整观测"的，这是后面一切分析的
  采样框声明）；
- `layer` 字段分布（0/1/2 各多少人）、`is_crawled` 一致性；
- UserTopic 话题字符串的编码/空值/重复检查，统计不同话题标签数量。

## 项目一：严谨幂律重访（预计 1~2 周）

**研究问题**
- RQ1：五个用户特征（followee/follower/answer/agree/thanks）在严格统计检验下
  是否服从幂律？对数正态/截断幂律是否拟合得更好？
- RQ2：BFS 两层雪球采样对这些结论的影响有多大？

**T1.1 区分两种"度"（关键设计，先写清楚再动手）**
- **画像计数**（User 表里的 follower_num 等）：是知乎全站的真实值，不受诱导子图
  影响，但受"哪些用户被采进样本"的偏差影响（BFS 偏向高度数节点）；
- **诱导子图度**（26k 节点间实际观测到的边）：结构完整但只是全网的局部。
- 两者分开分析、分开下结论，这个区分本身就是文章的一个卖点。

**T1.2 CSN 拟合流水线（`powerlaw` 包）**
- 对每个特征：MLE 估计 α 与 x_min（KS 最小化）、bootstrap 拟合优度 p 值、
  与 lognormal / exponential / truncated power law 的似然比检验（Vuong）；
- 按 Broido & Clauset 的五级分类（Strongest → Not scale-free）给每个特征定级；
- 对 Net10k / Net50k 子图重复，检验结论对子集选择的稳健性。

**T1.3 采样偏差实验（回应 RQ2）**
- 用配置模型（configuration model）按拟合出的度分布生成合成网络，在其上从随机
  种子跑两层 BFS，对比"真实指数 vs BFS 观测指数"，复现并量化 Kurant et al.
  描述的偏差方向与幅度；
- 讨论 Kurant 校正在本数据上的适用性（两层截断 + 单种子，属于文献中偏差最重的
  情形，预期结论是"画像计数可信、诱导子图度分布不可外推"——但要用实验说话）。

**T1.4 产出**
- 一个可复现 notebook + 一篇文章《知乎社交网络分析（十年后）：这次用严格的
  幂律检验》，直接对照 2015 年报告 4.2 节逐图重做；
- 若结论有意思（例如多数特征降级为 lognormal），可整理成 arXiv note。

**里程碑判据**：五个特征各有一张"拟合对比表"（α、x_min、p 值、LR 检验结果、
分级），加一张 BFS 偏差模拟图。

## 项目二：社交社区 × 兴趣社区对齐（预计 4~8 周）

**研究问题**
- RQ3：关注网络的社区结构与用户兴趣聚类在多大程度上重合？
- RQ4：哪些社交社区是兴趣驱动的、哪些是名人/关系驱动的？

**T2.1 话题语义聚类（质量放大器，先做）**
- 对全部话题标签跑中文 embedding，HDBSCAN 或层次聚类得到话题簇
  （目标粒度：数百个簇），人工抽查 top 50 簇命名；
- 验收标准："恋爱/爱情/情感"归入同簇；"调查类问题""你如何评价 X"这类平台运营
  标签单独成簇并在后续分析中剔除（2015 年报告已指出它们无信息量）；
- 产出 topic → cluster 映射表，UserTopic 聚合为"用户 × 话题簇"权重矩阵
  （建议做 TF-IDF 加权，压掉"生活"这类万金油簇）。

**T2.2 社交社区检测**
- 在 26k 诱导子图（完整观测部分）上跑 Leiden（leidenalg，directed）；
- 分辨率扫描 + 多随机种子共识聚类（consensus clustering），只保留稳定社区；
- 参照项目一的结论说明该子图的采样局限。

**T2.3 兴趣聚类**
- 主方案：用户兴趣向量 =（TF-IDF 权重 × 话题簇 embedding 均值），KMeans/HDBSCAN
  聚类，k 用轮廓系数 + 稳定性选；
- 对照方案：直接在用户-话题簇二部图上跑二部社区检测（BiLouvain 或 bipartite
  modularity），检验结论不依赖某一种方法。

**T2.4 对齐度量与零模型（核心分析）**
- 全局：AMI / ARI / element-centric similarity（比 NMI 对社区数不敏感）；
- 零模型两个方向都要：
  - 度保持重连（degree-preserving rewiring）的关注网络 → 重跑 Leiden → 对齐度
    基线（排除"对齐只是度结构副产品"）；
  - 打乱用户-话题分配（保持每人话题数）→ 兴趣聚类基线；
- 社区级下钻（回应 RQ4）：对每个社交社区算兴趣熵/主导话题簇占比，区分
  "兴趣同质社区"与"围绕高 PageRank 节点的粉丝型社区"（结合项目一的 PageRank
  结果和 agree_num）。

**T2.5 可选延伸（时间富余再做，各自可独立成文）**
- 话题敏感 PageRank：按话题簇限制边传播，得到分领域专家榜，用 agree_num 验证
  排序质量，对照 2015 年的全局 PageRank Top5；
- 链路预测消融：node2vec baseline vs node2vec + 兴趣特征，按 HeaRT 式评测规范
  （统一负采样）报 MRR/Hits@k，把"兴趣同质性对关注行为的解释力"变成一个数。

**T2.6 产出**
- 文章《知乎社交网络分析（续）：人们跟着人走，还是跟着兴趣走？》；
- 如果对齐结论清晰（无论正反），整理成 ICWSM/CSCW 短文投稿的底稿。

**里程碑判据**：一张"社交社区 × 兴趣簇"混淆热力图 + 对齐指标相对零模型的
提升倍数 + 社区级案例表（每个大社区：规模、主导兴趣、兴趣熵、代表用户）。

## 时间线总览

| 周 | 内容 |
|---|---|
| 1 | Phase 0 全部 + T1.1/T1.2 |
| 2 | T1.3/T1.4，项目一收尾成文 |
| 3~4 | T2.1 话题语义聚类 + T2.2 社交社区 |
| 5~6 | T2.3 兴趣聚类 + T2.4 对齐分析 |
| 7~8 | 补实验、写作；富余则做 T2.5 |

## 风险与预案

| 风险 | 预案 |
|---|---|
| zhihu.db 找不回 / 损坏 | 优先级最高，第一天就验证；若丢失则一切免谈，需从 csv 原始文件重建（zhihu_database.py 路径） |
| 当年 topic 爬漏导致 UserTopic 覆盖不全 | P0.3 量化缺失率；若某类用户系统性缺话题，在 T2.3 中剔除并声明 |
| 26k 诱导子图太稠密/太精英化，Leiden 社区不清晰 | 退回 Net10k 尺度做核心分析，全图作为稳健性检验 |
| 兴趣与社交"完全对齐"或"完全不对齐"都可能是方法伪影 | T2.4 的双向零模型是防线；两种聚类各配对照方法 |
